"""Read-only UDS request for ECUs that answer late (after 7F xx 78) on an ELM clone that stops listening.
Trick: after the 78, keep the ELM listening with a tester-present to an unused ID while the
receive filter stays on the target's response ID and flow control is sent to the target.

Usage: OBD_ADDR=AA:BB:CC:DD:EE:FF uds_late.py 7E0 7E8 190201 19020D 1902FF
       (read-only: fault memory by status mask; any 0x22 read works too)"""
import socket, time, re, sys, os

FCSD = os.environ.get("FCSD", "300000")
ADDR = os.environ.get("OBD_ADDR") or sys.exit("Set OBD_ADDR to your adapter's Bluetooth address")
s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
s.settimeout(15); s.connect((ADDR, 1))

def raw(c, t=3):
    s.sendall((c + "\r").encode()); b = b""; e = time.time() + t; s.settimeout(0.05)
    while time.time() < e and b">" not in b:
        try: b += s.recv(4096)
        except socket.timeout: pass
    return b.decode(errors="replace").replace(">", "")

def frames(txt, rid):
    for l in txt.replace("\r", "\n").split("\n"):
        t = l.split()
        if len(t) > 1 and t[0] == rid:
            yield [int(x, 16) for x in t[1:] if re.fullmatch(r"[0-9A-F]{2}", x)]

def init():
    for c in ["ATZ", "ATE0", "ATL0", "ATS1", "ATH1", "ATSP6", "0100", "ATCAF0", "ATCFC1", "ATSTFF", "ATAT0"]:
        raw(c, 10)

def request(req, resp, payload, dummy="7E5", listens=6):
    raw(f"ATCRA{resp}"); raw(f"ATFCSH{req}"); raw("ATFCSD" + FCSD); raw("ATFCSM1")
    raw(f"ATSH{req}")
    txt = raw(payload, 6)
    raw(f"ATSH{dummy}")
    for _ in range(listens):
        txt += raw("3E00", 4)                       # nobody answers on dummy ID -> ELM listens ~1 s
        if re.search(rf"{resp} 0[1-7] (?!7F)", txt): break             # real single-frame answer
        m = re.search(rf"{resp} 1([0-9A-F]) ([0-9A-F]{{2}})", txt)      # first frame: wait for all CFs
        if m:
            total = int(m.group(1) + m.group(2), 16)
            for _ in range(8):
                r = assemble(txt, resp, payload)
                if isinstance(r, list) and len(r) >= total: break
                txt += raw("3E00", 4)
            break
    return assemble(txt, resp, payload)

def assemble(txt, resp, payload):
    sid = int(payload[:2], 16)
    data, total = None, None
    for f in frames(txt, resp):
        pci = f[0] >> 4
        if pci == 0:
            body = f[1:1 + (f[0] & 0xF)]
            if body[:1] == [0x7F] and body[2:3] == [0x78]: continue
            return body
        if pci == 1: total = ((f[0] & 0xF) << 8) | f[1]; data = f[2:]
        elif pci == 2 and data is not None: data += f[1:]
    if data is None: return None
    return data[:total] if len(data) >= total else ("INCOMPLETE", data, total)

if __name__ == "__main__":
    init()
    req, resp = sys.argv[1], sys.argv[2]
    for p in sys.argv[3:]:
        r = request(req, resp, p)
        print(p, "->", " ".join(f"{x:02X}" for x in r) if isinstance(r, list) else r, flush=True)
        time.sleep(2)
    s.close()
