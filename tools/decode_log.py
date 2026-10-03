"""Decode a raw logger file (everything.csv) into physical values, using data/dids.csv.

Usage:
  python3 tools/decode_log.py drives/2026-10-03_b/everything.csv            > decoded.csv
  python3 tools/decode_log.py drives/2026-10-03_b/everything.csv --wide     > wide.csv

Long output (default): t, wall, id, name, value, unit, confidence (one row per reading).
Wide output (--wide):  one row per logger loop (~3 s), one column per ID; the last known value is kept between readings.

Can also be imported:  from decode_log import load_dids, decode_did, decode_pid
"""
import csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIDS_CSV = os.path.join(HERE, "..", "data", "dids.csv")

# Standard OBD-II mode 01 PIDs used by the logger (SAE J1979)
PIDS = {
    "010C": ("Engine speed", "rpm", lambda A, B: (A * 256 + B) / 4),
    "010D": ("Vehicle speed", "km/h", lambda A, B: A),
    "0104": ("Calculated load", "%", lambda A, B: round(A * 100 / 255, 1)),
    "0123": ("Rail pressure (PID)", "bar", lambda A, B: (A * 256 + B) * 10 / 100),
    "010B": ("Manifold absolute pressure", "kPa", lambda A, B: A),
    "0110": ("MAF air flow", "g/s", lambda A, B: (A * 256 + B) / 100),
    "0105": ("Coolant temperature (PID)", "°C", lambda A, B: A - 40),
    "010F": ("Intake air temperature (PID)", "°C", lambda A, B: A - 40),
    "0111": ("Intake throttle (PID)", "%", lambda A, B: round(A * 100 / 255, 1)),
}


def load_dids(path=DIDS_CSV):
    return {r["did"].upper(): r for r in csv.DictReader(open(path, encoding="utf-8"))}


def _bytes(raw):
    parts = (raw or "").split()
    if not parts or not all(len(p) == 2 for p in parts):
        return None
    try:
        return [int(p, 16) for p in parts]
    except ValueError:
        return None


def decode_did(did, raw, table):
    """raw = ECU answer as hex text, e.g. '62 20 01 0D DD'. Returns a number, or None."""
    b = _bytes(raw)
    row = table.get(did.upper())
    if not b or b[0] != 0x62 or not row or not row["formula"]:
        return None
    data = b[3:] + [0, 0, 0, 0]
    A, B, C, D = data[:4]
    try:
        return round(eval(row["formula"], {"__builtins__": {}}, {"A": A, "B": B, "C": C, "D": D}), 4)
    except Exception:
        return None


def decode_pid(pid, raw):
    b = _bytes(raw)
    if not b or pid not in PIDS or b[0] != 0x41 or len(b) < 3 or b[1] != int(pid[2:], 16):
        return None
    A, B = (b[2:4] + [0])[:2]
    return PIDS[pid][2](A, B)


def read_log(path, table):
    """Yields (t, wall, id, name, value, unit, confidence) for every decodable reading."""
    for r in csv.DictReader(open(path, encoding="utf-8")):
        kind, ident, raw = r.get("kind", ""), r.get("id", ""), r.get("raw", "")
        if kind == "pid" and ident in PIDS:
            v = decode_pid(ident, raw)
            name, unit = PIDS[ident][:2]; conf = "standard"
        elif kind.startswith("did"):
            v = decode_did(ident, raw, table)
            row = table.get(ident.upper(), {})
            name, unit, conf = row.get("name", ""), row.get("unit", ""), row.get("confidence", "")
        else:
            continue
        if v is not None:
            yield float(r["t"]), r.get("wall", ""), ident, name, v, unit, conf


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    table = load_dids()
    rows = list(read_log(sys.argv[1], table))
    w = csv.writer(sys.stdout)
    if "--wide" not in sys.argv:
        w.writerow(["t", "wall", "id", "name", "value", "unit", "confidence"])
        w.writerows(rows)
        return
    ids = sorted({r[2] for r in rows})
    w.writerow(["t", "wall"] + ids)
    last, cur_t = {}, None
    for t, wall, ident, *_rest in rows:
        if ident == "010C" and cur_t is not None:   # 010C starts each logger loop
            w.writerow([cur_t[0], cur_t[1]] + [last.get(i, "") for i in ids])
        if ident == "010C":
            cur_t = (t, wall)
        last[ident] = _rest[1]
    if cur_t:
        w.writerow([cur_t[0], cur_t[1]] + [last.get(i, "") for i in ids])


if __name__ == "__main__":
    main()
