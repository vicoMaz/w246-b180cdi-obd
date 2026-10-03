"""Regenerate docs/sensor-map.md and data/torque_pro_w246.csv from data/dids.csv.

Usage: python3 tools/build_tables.py
data/dids.csv is the single source of truth. Edit it, then run this script.
"""
import csv, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DIDS = os.path.join(ROOT, "data", "dids.csv")
MAP_MD = os.path.join(ROOT, "docs", "sensor-map.md")
TORQUE = os.path.join(ROOT, "data", "torque_pro_w246.csv")

CATEGORIES = [
    ("temperature", "Temperatures"),
    ("fuel", "Fuel injection and rail"),
    ("cylinder", "Per-cylinder values"),
    ("engine", "Engine, torque, pedal, gear"),
    ("air", "Air, boost, intake throttle, EGR"),
    ("dpf", "DPF, soot and regeneration"),
    ("oil", "Oil"),
    ("counter", "Counters and timers"),
    ("identification", "Identification"),
]
CONF_ORDER = ["confirmed", "probable", "listed", "conflict", "candidate"]
SOURCE = {"logs": "own logs", "list": "K9K list", "both": "K9K list + own logs", "standard": "ISO 14229"}

HEADER = """# Sensor map – engine ECU data IDs (DIDs)

> Generated from [`data/dids.csv`](../data/dids.csv) by `tools/build_tables.py`. Do not edit by hand.

**ECU:** Continental SID307/SID310 (Mercedes part A 607 901 01 00), engine OM607 = Renault K9K 1.5 dCi.
**Address:** request `0x7E0`, response `0x7E8`, ISO 15765-4 CAN 11-bit 500 kbit/s.
**Read with:** UDS service `0x22` ReadDataByIdentifier, default session. Request `22 2001` → answer `62 20 01 0D DD`.

**How to read the formulas:** `A`, `B`, `C`, `D` are the data bytes after the 3-byte header (`62 DID_hi DID_lo`).
Example: coolant `62 20 01 0D DD` → A = 0x0D, B = 0xDD → ((13 × 256 + 221) − 2730) / 10 = **80.9 °C**.

**Confidence levels:**

| Level | Meaning |
|---|---|
| confirmed | Exact unit fit against a standard OBD value or a known physical quantity |
| probable | Several independent checks agree (correlation, setpoint/actual pairing, physics), or the K9K list name plus a matching behaviour |
| listed | Named in the K9K list, values look plausible, not yet checked against data |
| conflict | The K9K list and the logs disagree |
| candidate | One line of evidence only, from our logs |

Where the names come from: see [Data provenance](../README.md#data-provenance).

"""


def main():
    rows = list(csv.DictReader(open(DIDS, encoding="utf-8")))
    out = [HEADER]
    counts = {c: sum(r["confidence"] == c for r in rows) for c in CONF_ORDER}
    out.append("**Totals:** " + ", ".join(f"{n} {c}" for c, n in counts.items() if n) + f" ({len(rows)} IDs).\n\n")
    for key, title in CATEGORIES:
        group = [r for r in rows if r["category"] == key]
        if not group:
            continue
        out.append(f"## {title}\n\n| DID | Meaning | Formula | Unit | Confidence | Source | Notes |\n|---|---|---|---|---|---|---|\n")
        for r in group:
            formula = f"`{r['formula']}`" if r["formula"] else "–"
            conf = f"**{r['confidence']}**" if r["confidence"] in ("confirmed", "conflict") else r["confidence"]
            notes = r["notes"].replace("|", "\\|")
            out.append(f"| `{r['did']}` | {r['name']} | {formula} | {r['unit']} | {conf} | {SOURCE.get(r['source'], r['source'])} | {notes} |\n")
        out.append("\n")
    out.append("""## Standard OBD-II PIDs used by the logger

| PID | Meaning | Formula | Unit |
|---|---|---|---|
| `010C` | Engine speed | `(A*256+B)/4` | rpm |
| `010D` | Vehicle speed | `A` | km/h |
| `0104` | Calculated load | `A*100/255` | % |
| `0123` | Rail pressure | `(A*256+B)*10` | kPa |
| `010B` | Manifold absolute pressure | `A` | kPa |
| `0110` | MAF air flow | `(A*256+B)/100` | g/s |
| `0105` | Coolant temperature | `A-40` | °C |
| `010F` | Intake air temperature | `A-40` | °C |
| `0111` | Intake throttle valve | `A*100/255` | % (≈ 89.6 normally, below ~80 during a DPF regeneration) |
""")
    open(MAP_MD, "w", encoding="utf-8").write("".join(out))

    # Torque Pro "extended PIDs" import file: only plain arithmetic formulas
    with open(TORQUE, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_ALL)
        w.writerow(["Name", "ShortName", "ModeAndPID", "Equation", "Min Value", "Max Value", "Units", "OBD Header"])
        n = 0
        for r in rows:
            f = r["formula"]
            if not f or any(x in f for x in (" if ", "&")) or r["category"] == "identification":
                continue
            short = ("W246_" + r["did"])
            w.writerow([f"W246 {r['did']} {r['name']}", short, "22" + r["did"], f, 0, 0, r["unit"], "7E0"])
            n += 1
    print(f"wrote {MAP_MD} ({len(rows)} IDs) and {TORQUE} ({n} PIDs)")


if __name__ == "__main__":
    main()
