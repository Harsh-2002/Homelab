# NVMe health snapshot, 31 October 2026

Read-only live SMART readings captured at `2026-10-31T16:20:27Z`. No NVMe self-test, firmware
update or write/erase operation was performed. Both NVMe host/root disks and
dev VM100 root remain excluded from the data-disk erasure.

| Metric | px10 | px20 |
|---|---|---|
| Model | Micron_2400_MTFDKBA512QFM | SAMSUNG MZVLQ512HALU-000H1 |
| Capacity | 512 GB | 512 GB |
| SMART overall result | PASS | PASS |
| Critical warning bitmap | 0 | 0 |
| Temperature | 51°C | 50°C |
| Endurance used | 14% | 8% |
| Estimated endurance remaining | ~86% | ~92% |
| Available spare | 100% | 100% |
| Media/data-integrity errors | 0 | 0 |
| Error-log entry counter | 0 | 2708 |
| Power-on hours | 14,933 | 3,216 |
| Data written | ~25.2 TB | ~35.0 TB |
| Unsafe-shutdown counter | 208 | 280 |
| Historical warning-temperature time | 0 minutes | 368 minutes |
| Historical critical-temperature time | 0 minutes | 6 minutes |

Endurance remaining is `100 − Percentage Used`, a manufacturer wear estimate,
not a guaranteed remaining lifespan or an overall health score. See the
[NVMe endurance explanation](https://nvmexpress.org/resource/features-for-error-reporting-smart-log-pages-failures-and-management-capabilities-in-nvme-architectures/).

The px20 error-log query during this investigation returned an available entry
with status **Invalid Field in Command**; its media/data-integrity counter is
zero. Do not interpret the command-error counter as a count of bad sectors.
Its historical thermal counters record accumulated threshold-exceedance time;
they do not mean a current overtemperature warning. See the
[SMART temperature-counter definitions](https://learn.microsoft.com/en-us/windows/win32/api/nvme/ns-nvme-nvme_health_info_log).

These measurements do not establish the cause of earlier server hangs.
