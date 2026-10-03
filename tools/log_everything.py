"""Read-only 'log everything' drive logger for the W246 engine ECU (ELM327 clone over RFCOMM).

Usage: OBD_ADDR=AA:BB:CC:DD:EE:FF log_everything.py OUT_DIR [DURATION_S]

Each loop iteration (~2.5 s) reads:
  - fast set: standard PIDs (rpm, speed, load, rail, MAP, MAF, temps, intake throttle) + adapter voltage
  - priority DIDs (fuel quantity, torque, gear, air mass, DPF pressure/temp, EGR, per-cylinder fuel corrections)
  - next N 'live' DIDs (those that move while driving), rotating
  - next M of all 544 known DIDs, rotating (full sweep about every 6 min)
  - once at start: probe of IDs outside the 1 Oct scan range (unsupported ones are dropped)
  - occasionally: regeneration history counters, OBD fault codes, monitor status, mode 06 results
Writes OUT_DIR/everything.csv (epoch, t, wall, kind, id, raw) and OUT_DIR/status.json (for mark.py).
Survives Bluetooth dropouts. Stops after DURATION s, or when the ECU has been silent for 90 s (ignition off).
No writes, no clears, no session changes."""
import socket, time, csv, sys, os, json, datetime

ADDR = os.environ.get("OBD_ADDR") or sys.exit("Set OBD_ADDR to your adapter's Bluetooth address, e.g. export OBD_ADDR=AA:BB:CC:DD:EE:FF")
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
DURATION = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(OUT_DIR, "everything.csv")
STATUS = os.path.join(OUT_DIR, "status.json")

ALL_DIDS = [l.strip() for l in open(os.path.join(HERE, "didlist.txt")) if l.strip()]
# Names and scalings: data/dids.csv and docs/sensor-map.md
PRIORITY = ["2806", "2809", "2067", "2C04", "24F2", "2542", "2442", "256B", "259B",   # fuel mg/stroke, torque, gear, air kg/h, DPF dp, DPF in temp, EGR?
            "FD07", "FD08", "FD09", "FD0A"]                                            # fuel flow correction cyl 1-4
SLOW_DIDS = ["2488", "2487", "2481", "2485", "24A9", "24A5", "2489", "2810", "2006",   # regen history, oil viscosity loss, odometer
             "FD15", "FD16", "FD17", "FD18"]                                                  # adaptation status cyl 1-4
LIVE_DIDS = ["2001", "2002", "2004", "2005", "2008", "2009", "2022", "2061", "2062", "2063", "2064", "2065",
             "2066", "2068", "2069", "2163", "2246", "2294", "2296", "2403", "2406", "2407", "2409", "240B",
             "240D", "2412", "2421", "2424", "2439", "2447", "2448", "244D", "24BA", "24E1", "24E2", "24FA",
             "2510", "2521", "2527", "2528", "2557", "2561", "2567", "2569", "256A", "259F", "2801",
             "2808", "2886", "28C9",
             "2802", "280D", "280E", "2813", "202E", "2050", "2103", "2401", "2402", "2404", "2405", "2408",
             "2413", "2432", "2438", "2441", "242C", "2166", "246D", "2434",
             "FD19", "FD1A", "FD1B", "FD1C", "FDB6", "FDB7", "FDB8", "FDB9", "FDBA"]
# IDs outside the 0x01xx-0x2Exx scan range: read once at start, kept in the rotation only if the ECU answers positively
PROBE = ["FD07", "FD08", "FD09", "FD0A", "FD15", "FD16", "FD17", "FD18", "FD19", "FD1A", "FD1B", "FD1C",
         "FD28", "FD2D", "FD2E", "FD2F", "FD42", "FD43", "FD4D", "FD4E", "FD69", "FD70", "FD82", "FD84",
         "FD86", "FD88", "FD89", "FD8A", "FD8B", "FD96", "FD9C", "FDB6", "FDB7", "FDB8", "FDB9", "FDBA",
         "8000", "8002", "EF0F", "F40B"]
FAST = ["010C", "010D", "0104", "0123", "010B", "0110", "0105", "010F", "0111"]
SLOW_OBD = ["03", "07", "0101", "0141", "0130", "0131", "0600", "0631", "0685", "06B2"]
N_LIVE, N_ALL = 5, 3
INIT = ["ATZ", "ATE0", "ATL0", "ATS1", "ATH0", "ATSP6", "ATST19"]

def connect():
    while True:
        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.settimeout(15); s.connect((ADDR, 1)); return s
        except OSError as e:
            print("connect failed:", e, "- retrying in 10 s", flush=True); time.sleep(10)

s = connect()
def _cmd(c, timeout):
    s.sendall((c + "\r").encode()); buf = b""; end = time.time() + timeout; s.settimeout(0.05)
    while time.time() < end and b">" not in buf:
        try: buf += s.recv(4096)
        except socket.timeout: pass
    return " ".join(buf.decode(errors="replace").replace(">", "").split())

link_state = "connecting"
def cmd(c, timeout=2.5):
    """Like _cmd, but survives Bluetooth dropouts: reconnect, re-init, and report the gap."""
    global s, link_state
    try:
        return _cmd(c, timeout)
    except OSError as e:
        link_state = "reconnecting"
        print(f"{datetime.datetime.now():%H:%M:%S} link lost ({e}) - reconnecting", flush=True)
        try: s.close()
        except OSError: pass
        while True:   # a dropout during re-init just means another reconnect
            s = connect()
            try:
                for i in INIT: _cmd(i, 5)
                _cmd("0100", 6); _cmd("ATSH7E0", 2.5)
                break
            except OSError as e2:
                print("re-init failed:", e2, "- reconnecting", flush=True)
                try: s.close()
                except OSError: pass
        link_state = "ok"
        print(f"{datetime.datetime.now():%H:%M:%S} reconnected", flush=True)
        return "LINK_LOST"

def pid_val(raw, pid):
    b = raw.split()
    try:
        i = b.index("41"); assert b[i + 1] == pid[2:]
        d = [int(x, 16) for x in b[i + 2:i + 4]]
    except (ValueError, AssertionError, IndexError):
        return None
    return {"010C": lambda: (d[0] * 256 + d[1]) / 4, "010D": lambda: d[0], "0105": lambda: d[0] - 40,
            "0111": lambda: round(d[0] * 100 / 255, 1), "0104": lambda: round(d[0] * 100 / 255, 1)}.get(pid, lambda: None)()

def write_status(**kw):
    try:
        tmp = STATUS + ".tmp"
        json.dump(kw, open(tmp, "w")); os.replace(tmp, STATUS)
    except OSError:
        pass

for c in INIT: cmd(c, 5)
print("waiting for ECU (ignition on)...", flush=True)
write_status(state="waiting for ignition")
while "41 00" not in cmd("0100", 6): time.sleep(5)
cmd("ATSH7E0"); link_state = "ok"
print("ECU answering - logging", flush=True)

ok = lambda r: r and not any(x in r for x in ("NO DATA", "ERROR", "STOPPED", "?", "UNABLE", "LINK_LOST"))
t0 = time.time(); last_ok = t0; it = li = ai = si = sd = n = 0
live = {}
with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["epoch", "t", "wall", "kind", "id", "raw"])
    def rec(kind, ident, raw):
        global n, last_ok
        now = time.time()
        w.writerow([f"{now:.2f}", round(now - t0, 2), datetime.datetime.now().strftime("%H:%M:%S"), kind, ident, raw]); n += 1
        if ok(raw): last_ok = now
        if kind == "pid": live[ident] = pid_val(raw, ident)
    for d in PROBE:
        raw = cmd("22" + d, 3); rec("did_probe", d, raw)
        if any(x in (raw or "") for x in ("7F 22", "NO DATA")):   # refused/unsupported; keep on link errors
            PRIORITY, SLOW_DIDS, LIVE_DIDS = ([x for x in L if x != d] for L in (PRIORITY, SLOW_DIDS, LIVE_DIDS))
    fh.flush()
    print("probe: kept " + " ".join(d for d in PROBE if d in PRIORITY + SLOW_DIDS + LIVE_DIDS), flush=True)
    while time.time() - t0 < DURATION:
        rec("adapter", "ATRV", cmd("ATRV"))
        for p in FAST: rec("pid", p, cmd(p))
        for d in PRIORITY: rec("did_prio", d, cmd("22" + d, 3))
        for _ in range(N_LIVE):
            d = LIVE_DIDS[li % len(LIVE_DIDS)]; li += 1; rec("did_live", d, cmd("22" + d, 3))
        for _ in range(N_ALL):
            d = ALL_DIDS[ai % len(ALL_DIDS)]; ai += 1; rec("did_all", d, cmd("22" + d, 3))
        if it % 5 == 0:
            d = SLOW_DIDS[sd % len(SLOW_DIDS)]; sd += 1; rec("did_slow", d, cmd("22" + d, 3))
        if it % 15 == 0:
            q = SLOW_OBD[si % len(SLOW_OBD)]; si += 1; rec("obd_slow", q, cmd(q, 4))
        fh.flush(); it += 1
        th = live.get("0111")
        write_status(state=link_state, elapsed=round(time.time() - t0), rows=n,
                     rpm=live.get("010C"), speed=live.get("010D"), coolant=live.get("0105"), load=live.get("0104"),
                     throttle=th, regen=(th is not None and th < 80), sweep=f"{ai // len(ALL_DIDS)}+{ai % len(ALL_DIDS)}/{len(ALL_DIDS)}")
        if it % 20 == 0:
            print(f"t={time.time()-t0:5.0f}s rows={n} all-DID sweep {ai // len(ALL_DIDS)}+{ai % len(ALL_DIDS)}/{len(ALL_DIDS)}", flush=True)
        if time.time() - last_ok > 90:
            print("ECU silent for 90 s (ignition off?) - stopping", flush=True); break
s.close()
write_status(state="finished", rows=n, elapsed=round(time.time() - t0))
print(f"done: {n} rows, {time.time()-t0:.0f} s -> {OUT}", flush=True)
