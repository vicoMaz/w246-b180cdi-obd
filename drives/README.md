# Drive logs

Real logs from one W246 B 180 CDI (OM607), recorded with the tools in this repo.
Raw ECU answers are kept as is, so any decoding can be re-checked.

**Removed for privacy:** VIN and identification IDs (`F0xx`, `F1xx`), odometer (`2006`), distance since DPF replacement (`24BB`),
injector code slots (`2465`–`2468`), absolute timestamps (`epoch`), logger messages (`run.log`). Clock times (`wall`) are local time.

| Folder | Length | Conditions | Notable |
|---|---|---|---|
| `2026-10-01/` | 2 + 15 + 10 min | motorway and mixed, warm | **Contains a DPF regeneration** (`live15.csv`, throttle down to 18 %). Older, simpler format (see below). Also the full ID scan and fault memory |
| `2026-10-02/` | 21 min | cold start (40 °C), up to 120 km/h, ~13 min above 80 km/h | no regeneration |
| `2026-10-03_a/` | 15 min | **cold start** (36 °C), town, several idle stops | per-cylinder corrections large when cold, shrinking as it warms |
| `2026-10-03_b/` | 19 min | **warm start** (75 °C), town, **4 min warm idle** at the end | per-cylinder corrections within 0.92–1.05 |

## Formats

**`everything.csv`** (2 Oct onward): one row per reading. Columns `t`, `wall`, `kind`, `id`, `raw`; see [AGENTS.md](../AGENTS.md#drive-log-format).
Decode with:

```bash
python3 tools/decode_log.py drives/2026-10-03_b/everything.csv --wide > wide.csv
```

**`2026-10-01/`** (first session, early tools):

| File | Content |
|---|---|
| `live.csv`, `live15.csv` | already decoded: `t`, rail pressure (bar), rpm, load %, intake throttle %, speed |
| `cand_drive.csv` | already decoded PIDs + raw 16-bit values of candidate DIDs |
| `didscan.log` | every ID the ECU answered in 0x0100–0x0FFF and 0x2000–0x2FFF, raw CAN frames |
| `idletest.json` | two idle passes over all IDs plus a forward/reverse read-order test |
| `dtc.txt` | fault memory, raw (`1902FF`) |

`dtc_start.txt` / `dtc_end.txt` in the other folders: fault memory read at the start / end of the drive (`uds_late.py` output).
