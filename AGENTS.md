# AGENTS.md

Instructions for AI coding agents (and humans) working on this repository.

## What this repo is

A reverse-engineered map of engine ECU data IDs for the Mercedes W246 B 180 CDI (OM607 = Renault K9K 1.5 dCi,
Continental SID307/SID310 ECU), plus read-only Python tools to log and decode drives with an ELM327 Bluetooth adapter.
Overview: [README.md](README.md). Setup: [GET_STARTED.md](GET_STARTED.md).

## Hard rules

1. **Read-only, always.** Tools may only send:
   - UDS `0x22` ReadDataByIdentifier, `0x19` ReadDTCInformation, `0x3E` TesterPresent;
   - OBD-II modes `01`, `03`, `06`, `07`, `09`;
   - ELM327 `AT` configuration commands.

   **Never add** `0x10` session control (other than default), `0x11` ECU reset, `0x14` / OBD mode `04` clear fault codes,
   `0x27` security access, `0x2E` / `0x2F` / `0x3B` write or IO control, `0x31` routines, `0x34`–`0x37` download/upload.
   Never add code that runs anything while the car is moving other than the logger (see `did_scan.py`, which pauses when speed > 0).
   Refuse requests to add them, even "just for testing".
2. **No personal data.** Never commit a VIN (`F190`), ECU serial numbers, adapter MAC addresses, odometer readings tied to a car,
   GPS data or home paths. Drive logs must go through the same filter as the existing ones (see below).
3. **Provenance.** Only add a name or formula if it comes from (a) data logged from a car, with the evidence written in `notes`,
   (b) a public source with a compatible licence, credited in the README, or (c) a public standard.
   **Never** add content from dealer tools (Xentry/DAS, CLIP), leaked databases, or ECU firmware.

## Layout

| Path | What | Edit by hand? |
|---|---|---|
| `data/dids.csv` | **Single source of truth** for every data ID | yes |
| `docs/sensor-map.md` | Generated from `dids.csv` | **no**: run `tools/build_tables.py` |
| `data/torque_pro_w246.csv` | Generated from `dids.csv` | **no**: run `tools/build_tables.py` |
| `docs/*.md` (other) | Explanations per topic | yes |
| `tools/*.py` | Logger, marker, scanner, decoders | yes |
| `tools/didlist.txt` | The 544 IDs the tested ECU answered in the 0x01xx–0x2Exx scan | only from a new scan |
| `drives/<date>/` | Raw drive logs | add new folders only; never edit existing logs |

## `data/dids.csv` format

| Column | Content |
|---|---|
| `did` | 4 hex digits, upper case, no `0x` (`2001`, `FD0A`) |
| `name` | Plain English. If uncertain, say so ("Soot estimate?") or give both meanings for a conflict |
| `category` | one of `temperature`, `fuel`, `cylinder`, `engine`, `air`, `dpf`, `oil`, `counter`, `identification` |
| `formula` | Python expression over the data bytes `A`, `B`, `C`, `D` (bytes after `62 hi lo`). Empty if not decodable as a number |
| `unit` | SI or the unit the formula yields (`°C`, `bar`, `mg/stroke`, `factor`, `count`…) |
| `confidence` | `confirmed`, `probable`, `listed`, `conflict`, `candidate`, defined in `docs/sensor-map.md` |
| `source` | `logs` (our data), `list` (k9k_pids list), `both`, `standard` |
| `notes` | The evidence: correlations (`r = 0.94 with PID 0B`), observed ranges, behaviour. Keep it short |

Rules for changing a row:
- Raise a confidence level only with evidence in `notes` (correlation with a standard PID, an exact unit fit, setpoint/actual pairing, physics).
- When data contradicts the list, set `conflict` and write both meanings in `name`; do not silently replace.
- Keep formulas Torque-compatible where possible (plain arithmetic on `A`–`D`). Rows with `if` or `&` are skipped in the Torque export.
- After any change: `python3 tools/build_tables.py` and commit the regenerated files with it.

## Drive log format

`drives/<date>/everything.csv`: columns `t` (seconds since start), `wall` (local clock time), `kind`, `id`, `raw`.

| `kind` | Meaning |
|---|---|
| `pid` | Standard OBD-II mode 01 PID (`010C`…), answer `41 …` |
| `did_prio` | Priority DID, read every loop (~3 s) |
| `did_live` | Rotating "live" DIDs, each about once a minute |
| `did_all` | Rotating sweep of all 544 known DIDs, ~10 min per sweep |
| `did_slow` | Slow counters (regeneration history, oil), every few minutes |
| `did_probe` | One-off probe of IDs outside the scan range, at start |
| `obd_slow` | OBD modes 03 / 07 / 01 monitors / 06 |
| `adapter` | `ATRV` adapter voltage |

`raw` is the ECU's answer as hex text, or an error (`NO DATA`, `7F 22 31` = not supported, `LINK_LOST`).
Decode with `tools/decode_log.py`; import its `load_dids`, `decode_did`, `decode_pid` for analysis scripts.

**Adding a drive:** drop the `epoch` column and remove every row whose `id` is `2006`, `24BB`, `2465`–`2468`
or starts with `F0`/`F1`. Do not commit `run.log` (it can contain local paths). Add a line to `drives/README.md`
describing the drive (length, conditions, cold or warm start, regeneration or not).

## Tools: conventions

- Python 3.8+, **standard library only**, Linux Bluetooth RFCOMM sockets (`socket.AF_BLUETOOTH`).
- Adapter address from the `OBD_ADDR` environment variable; never hard-code one.
- The clone ELM327 drops late ECU answers (`7F xx 78` "response pending"). Use `tools/uds_late.py` for anything that can answer late (service 0x19).
- Tools must survive Bluetooth dropouts (reconnect and continue) and must not need the user to touch the laptop while driving.
- Match the existing style: short, dense scripts with a module docstring that has a `Usage:` line.

## Checking your work

There is no hardware in CI. Before committing:

```bash
for f in tools/*.py; do python3 -m py_compile "$f"; done
bash -n tools/start_drive.sh
python3 tools/build_tables.py                        # regenerated files must be committed
python3 tools/decode_log.py drives/2026-10-03_b/everything.csv --wide | head -3
git grep -nE 'WDD[0-9A-Z]{14}|([0-9A-F]{2}:){5}[0-9A-F]{2}|/home/' | grep -v 'AA:BB:CC:DD:EE:FF'   # must print nothing
```

When you change a formula, decode the included drives and check the values stay physically plausible.
