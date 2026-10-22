"""Additional controls observed on the owner's TP1X RAC-01011 AC.

Writes are partial resource updates, never raw collections or option blobs.
Wire contracts are inferred from live advertised fields, not yet actuated.
"""

from ..capability import Capability
from ..entities import SelectDesc

OSCILLATION = "/wind/oscillation/vs/0"
STEP = "/stepcontrol/vs/0"
COMFORT = "/mode/convenient/vs/0"
OVERRIDDEN_HREFS = frozenset((OSCILLATION, STEP, COMFORT))
MODE_FIELD = "x.com.samsung.da.modes"
MODES_FIELD = "x.com.samsung.da.supportedModes"


def _our_model(resources):
    return str(
        resources.get("/information/vs/0", {}).get("x.com.samsung.da.modelNum", "")
    ).startswith("TP1X_DA-AC-RAC-01011_0000")


def _present(field, options):
    return lambda rep, resources: (
        _our_model(resources)
        and field in rep
        and isinstance(rep.get(options), (list, tuple))
        and bool(rep[options])
    )


def _on_guard(payload, rep, resources):
    power = resources.get("/power/vs/0", {}).get("x.com.samsung.da.power")
    return None if power == "On" else "homelab_ac_power_required"


def _cool_guard(payload, rep, resources):
    if error := _on_guard(payload, rep, resources):
        return error
    modes = resources.get("/mode/vs/0", {}).get(MODE_FIELD, [])
    return None if "Cool" in modes else "homelab_ac_cool_required"


def _field_write(field, options, *, fixed_axis=None):
    def write(value, rep, href=None):
        if value not in rep.get(options, ()):
            return None
        body = {field: value}
        if fixed_axis:
            if "Fix" not in rep.get("supported" + fixed_axis.title(), ()):
                return None
            body[fixed_axis] = "Fix"
        return OSCILLATION.strip("/").split("/"), body

    return write


def _airflow_label(value, resources):
    return {"Fix": "Fixed", "AllSwing": "Full sweep", "LeftSwing": "Left side", "RightSwing": "Right side"}.get(value)


AIRFLOW = Capability(
    href=OSCILLATION,
    poll_tier="warm",
    entities=tuple(
        SelectDesc(
            key=key,
            field=field,
            options_field=options,
            exists_fn=_present(field, options),
            icon=icon,
            display_fn=_airflow_label,
            write_fn=_field_write(field, options, fixed_axis=fixed_axis),
            validate_fn=_on_guard,
        )
        for key, field, options, icon, fixed_axis in (
            ("homelab_vertical_swing", "vertical", "supportedVertical", "mdi:swap-vertical", None),
            ("homelab_horizontal_swing", "horizontal", "supportedHorizontal", "mdi:swap-horizontal", None),
            ("homelab_vertical_position", "verticalAngle", "supportedVerticalAngle", "mdi:arrow-up-down", "vertical"),
            ("homelab_horizontal_position", "horizontalAngle", "supportedHorizontalAngle", "mdi:arrow-left-right", "horizontal"),
            ("homelab_horizontal_sweep", "horizontalSwingMode", "supportedHorizontalSwingMode", "mdi:arrow-left-right-bold", None),
        )
    ),
)


def _mode_write(href):
    def write(value, rep, actual_href=None):
        if value not in rep.get(MODES_FIELD, ()):
            return None
        return href.strip("/").split("/"), {MODE_FIELD: value}

    return write


FIVE_STEP = Capability(
    href=STEP,
    poll_tier="warm",
    entities=(
        SelectDesc(
            key="homelab_cooling_capacity",
            field=MODE_FIELD,
            options_field=MODES_FIELD,
            exists_fn=_present(MODE_FIELD, MODES_FIELD),
            icon="mdi:snowflake-variant",
            display_fn=lambda value, resources: {
                "Off": "Standard (100%)", "Power": "Power (120%)",
                "80": "80%", "60": "60%", "40": "40%",
            }.get(value),
            write_fn=_mode_write(STEP),
            validate_fn=_cool_guard,
        ),
    ),
)

COMFORT_MODE = Capability(
    href=COMFORT,
    poll_tier="warm",
    entities=(
        SelectDesc(
            key="homelab_comfort_mode",
            field=MODE_FIELD,
            options_field=MODES_FIELD,
            exists_fn=_present(MODE_FIELD, MODES_FIELD),
            icon="mdi:weather-night",
            display_fn=lambda value, resources: {
                "Off": "Normal", "Sleep": "Good Sleep", "Quiet": "Quiet",
                "Speed": "MAX (Fast)",
            }.get(value),
            write_fn=_mode_write(COMFORT),
            validate_fn=_on_guard,
        ),
    ),
)

CAPABILITIES = (AIRFLOW, FIVE_STEP, COMFORT_MODE)
