"""Scan the engine ECU for every data ID (DID) it answers with service 0x22 (read-only).

Usage: OBD_ADDR=AA:BB:CC:DD:EE:FF did_scan.py [START_HEX]
Scans 0x0100-0x0FFF and 0x2000-0x2FFF (about 1 hour), writes didscan.log in the current folder.
Pauses automatically whenever the car moves: run it parked, engine idling or ignition on.
Resume after an interruption with the last '# progress' value, e.g. did_scan.py 2400
"""
import socket, time, sys, os
ADDR = os.environ.get("OBD_ADDR") or sys.exit("Set OBD_ADDR to your adapter's Bluetooth address")
START = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x0100
RANGES = [(max(lo, START), hi) for lo, hi in [(0x0100, 0x0FFF), (0x2000, 0x2FFF)] if hi >= START]
LOG = "didscan.log"
s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
s.settimeout(15); s.connect((ADDR, 1))
def cmd(c, timeout=3):
    s.sendall((c + "\r").encode()); buf = b""; end = time.time() + timeout
    s.settimeout(0.3)
    while time.time() < end and b">" not in buf:
        try: buf += s.recv(4096)
        except socket.timeout: pass
    return buf.decode(errors="replace").replace("\r", " | ").replace(">", "").strip(" |")
def log(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f: f.write(msg + "\n")
for c in ["ATZ", "ATE0", "ATL0", "ATS1", "ATSP6", "ATH1", "ATSH7E0", "ATCAF1", "ATST19"]: cmd(c)
def speed():
    r = cmd("010D")
    try: return int(r.split()[-1], 16)
    except Exception: return -1
def wait_stopped():
    while (v := speed()) != 0:
        log(f"# paused: speed={v} km/h"); time.sleep(10)
log(f"# start {time.ctime()}")
wait_stopped()
n = 0
for lo, hi in RANGES:
    for did in range(lo, hi + 1):
        if n % 100 == 0:
            wait_stopped(); log(f"# progress {did:04X}")
        n += 1
        r = cmd(f"22{did:04X}")
        if "7F 22 78" in r:            # response pending
            r += " || " + cmd("", 5)
        if "7F 22 31" in r or "NO DATA" in r or not r:
            continue
        log(f"{did:04X} {r}")
log(f"# done {time.ctime()}")
s.close()
