"""Offline tests: these never connect to Home Assistant or the appliance."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest


def load_capabilities(upstream):
    root = Path(upstream)
    for name, relative in (
        ("localthings", ""),
        ("localthings.registry", "registry"),
        ("localthings.registry.capabilities", "registry/capabilities"),
    ):
        module = types.ModuleType(name)
        module.__path__ = [str(root / relative)]
        sys.modules[name] = module
    name = "localthings.registry.capabilities.homelab_samsung_ac"
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("homelab_samsung_ac.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = load_capabilities(sys.argv[1])

    def resources(self, power="On", mode="Cool"):
        return {
            "/information/vs/0": {"x.com.samsung.da.modelNum": "TP1X_DA-AC-RAC-01011_0000|fixture"},
            "/power/vs/0": {"x.com.samsung.da.power": power},
            "/mode/vs/0": {self.c.MODE_FIELD: [mode]},
        }

    def test_swing_writes_one_axis_only(self):
        vertical = self.c.AIRFLOW.entities[0]
        rep = {"vertical": "Fix", "supportedVertical": ["Swing", "Fix"]}
        self.assertTrue(vertical.exists_fn(rep, self.resources()))
        self.assertEqual(vertical.write_fn("Swing", rep), (["wind", "oscillation", "vs", "0"], {"vertical": "Swing"}))
        self.assertIsNone(vertical.write_fn("invented", rep))

    def test_position_sets_only_its_axis_fixed(self):
        position = self.c.AIRFLOW.entities[2]
        rep = {"verticalAngle": "5", "supportedVerticalAngle": ["1", "2", "3", "4", "5", "6"], "supportedVertical": ["Swing", "Fix"]}
        self.assertEqual(position.write_fn("2", rep)[1], {"verticalAngle": "2", "vertical": "Fix"})
        self.assertIsNone(position.write_fn("7", rep))
        self.assertIsNone(position.write_fn("2", {**rep, "supportedVertical": ["Swing"]}))

    def test_power_off_and_non_cool_rejected(self):
        desc = self.c.FIVE_STEP.entities[0]
        self.assertEqual(desc.validate_fn("80", {}, self.resources(power="Off")), "homelab_ac_power_required")
        self.assertEqual(desc.validate_fn("80", {}, self.resources(mode="Dry")), "homelab_ac_cool_required")
        self.assertIsNone(desc.validate_fn("80", {}, self.resources()))

    def test_step_payload_is_scalar_not_mode_list(self):
        desc = self.c.FIVE_STEP.entities[0]
        rep = {self.c.MODE_FIELD: "Off", self.c.MODES_FIELD: ["Off", "80", "60", "40", "Power"]}
        self.assertEqual(desc.write_fn("80", rep), (["stepcontrol", "vs", "0"], {self.c.MODE_FIELD: "80"}))
        self.assertIsNone(desc.write_fn("50", rep))
        self.assertEqual(desc.display_fn("Off", {}), "Standard (100%)")
        self.assertEqual(desc.display_fn("Power", {}), "Power (120%)")

    def test_gated_to_observed_model_and_advertised_fields(self):
        desc = self.c.AIRFLOW.entities[0]
        rep = {"vertical": "Fix", "supportedVertical": ["Swing", "Fix"]}
        self.assertFalse(desc.exists_fn(rep, {}))
        self.assertFalse(desc.exists_fn({"vertical": "Fix"}, self.resources()))

    def test_presets_are_exclusive_not_three_independent_switches(self):
        desc = self.c.COMFORT_MODE.entities[0]
        rep = {self.c.MODE_FIELD: "Off", self.c.MODES_FIELD: ["Off", "Sleep", "Quiet", "Speed"]}
        self.assertEqual(desc.write_fn("Sleep", rep)[1], {self.c.MODE_FIELD: "Sleep"})
        self.assertEqual(desc.display_fn("Speed", {}), "MAX (Fast)")
        self.assertEqual(desc.display_fn("Sleep", {}), "Good Sleep")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]], verbosity=2)
