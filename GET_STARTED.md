# Get started

From an unopened adapter to a decoded drive log in about 30 minutes. Everything here is read-only.

## 1. What you need

| Item | Notes |
|---|---|
| ELM327 adapter with **classic Bluetooth** (SPP/RFCOMM) | A ~€10 "ELM327 v1.5" clone works. Adapters that are **BLE-only** will not work with these tools. See [docs/elm327-notes.md](docs/elm327-notes.md) |
| Laptop with **Linux** and Bluetooth | Tested on Ubuntu with BlueZ. The tools use Python's built-in RFCOMM sockets, which macOS does not provide |
| Python **3.8 or newer** | No extra packages needed |
| The car | W246 B 180 CDI, 1.5 l **OM607** engine. Check this first: see [README](README.md#car-and-ecu) |

The **OBD port** is under the dashboard on the driver's side, above the pedals.

## 2. Get the code

```bash
git clone https://github.com/vicoMaz/w246-b180cdi-obd.git
cd w246-b180cdi-obd
```

## 3. Pair the adapter

Plug the adapter in and switch the **ignition on** (most adapters only power up then). Then:

```bash
bluetoothctl
  scan on              # wait for a device called OBDII, OBD BLE, V-LINK or similar
  pair AA:BB:CC:DD:EE:FF   # PIN is usually 1234 or 0000
  trust AA:BB:CC:DD:EE:FF
  quit
```

Tell the tools which adapter to use. Put this in your shell, or in `~/.bashrc` to keep it:

```bash
export OBD_ADDR=AA:BB:CC:DD:EE:FF
```

## 4. First read: coolant temperature

Ignition on (engine running or not):

```bash
python3 tools/uds_late.py 7E0 7E8 222001
```

Expected answer, something like:

```
222001 -> 62 20 01 0D DD
```

`62` means "positive answer to service 22", `20 01` is the ID, and `0D DD` is the value.
From [docs/sensor-map.md](docs/sensor-map.md): coolant = `((A*256+B)-2730)/10` → ((13×256 + 221) − 2730) / 10 = **80.9 °C**.

Any other ID works the same way: `222801` for rail pressure, `22FD0A` for the cylinder 4 fuel correction, and so on.

## 5. Read the fault memory

Generic OBD apps often show "no codes" on this car, because the ECU only lists its faults through the UDS service 0x19.
Clone adapters also give up before the ECU answers. `uds_late.py` works around both:

```bash
python3 tools/uds_late.py 7E0 7E8 19020D          # only codes that failed, are pending or are stored
python3 tools/decode_dtc.py "59 02 FF 02 04 3A 69"  # paste the answer printed by the line above
```

How to read the result: [docs/fault-codes.md](docs/fault-codes.md). Nothing is cleared.

## 6. Log a drive

**Set everything up while parked.** In a terminal window:

```bash
tools/start_drive.sh
```

1. Start the engine. The window shows `logger: waiting for ignition`, then a live line:
   `12 min |  98 km/h  1950 rpm | coolant 80 °C | throttle 89.6 % | rows 5230`
2. **REGEN ACTIVE?** on that line means a DPF regeneration is probably running.
3. Keys, in that window (keep it focused, or let a passenger press them):

   | Key | Records |
   |---|---|
   | `SPACE` | "event now" (vibration, noise, hesitation…), with the time to 0.01 s |
   | `n` | "no event now", a comparison point in a similar situation |
   | `q` | closes the marker window only; logging continues |

4. The logger stops by itself **90 s after the engine is switched off**, or after 60 minutes.
   The screen is kept awake while the marker window is open (GNOME).

Files are saved in `drives/<date_time>/`:

| File | Content |
|---|---|
| `everything.csv` | every reading: time, kind, ID, raw answer |
| `markers.csv` | your key presses |
| `dtc_start.txt` | fault memory at the start |
| `run.log` | logger messages |

**Tip for the per-cylinder values:** finish with **2 minutes at idle with a warm engine** (coolant ≥ 75 °C).
The ECU only updates `FD07`–`FD0A` at idle. See [docs/per-cylinder-corrections.md](docs/per-cylinder-corrections.md).

## 7. Decode the log

```bash
python3 tools/decode_log.py drives/<date_time>/everything.csv          > decoded.csv   # one row per reading
python3 tools/decode_log.py drives/<date_time>/everything.csv --wide   > wide.csv      # one row per ~3 s, one column per ID
```

Open `wide.csv` in a spreadsheet, or in Python/pandas. Try it first on the included logs in [`drives/`](drives/README.md).

## 8. Optional

- **Scan your own ECU** for every ID it answers (about an hour, parked; pauses if the car moves):
  `python3 tools/did_scan.py`. Useful to check a different car or software version against this map.
- **Torque Pro (Android):** copy `data/torque_pro_w246.csv` to the phone, then in Torque:
  Settings → Manage extra PIDs/Sensors → menu → Import CSV file.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `connect failed: Host is down` | Ignition off, adapter asleep, laptop out of range, or not paired. The logger retries every 10 s |
| `Connection refused` / busy | Another program (Torque, a second tool) is connected. Only one connection at a time |
| `NO DATA` for every ID | Wrong car/engine, or ignition off. Try `0100` first: `python3 tools/uds_late.py 7E0 7E8 0100` |
| `7F 22 31` for an ID | The ECU does not support that ID (normal for some IDs, e.g. `FDB7`) |
| Fault memory answer `INCOMPLETE` | The clone missed some frames of a long answer. Use the short mask `19020D` instead of `1902FF` (which also lists the ~40 untested codes) |
| Keys do nothing in the marker window | Click on the window to focus it |
