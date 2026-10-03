"""Decode a UDS 59 02 fault-memory answer (hex) into P-codes with status flags.

Usage: decode_dtc.py "59 02 FF 02 04 3A 69 ..."
"""
import sys
FLAGS = [(0, "FAILING NOW"), (1, "failed this cycle"), (2, "pending"), (3, "CONFIRMED/stored"),
         (4, "not tested since clear"), (5, "failed since clear"), (6, "not tested this cycle"), (7, "warning lamp")]
def decode(hexstr):
    b = bytes.fromhex(hexstr.replace(" ", ""))
    assert b[0] == 0x59
    out = []
    for i in range(3, len(b) - 3, 4):
        a, c, ftb, st = b[i:i + 4]
        code = f"{'PCBU'[a >> 6]}{(a >> 4) & 3}{a & 0xF:X}{c:02X}-{ftb:02X}"
        out.append((code, st, [n for bit, n in FLAGS if st >> bit & 1]))
    return out
if __name__ == "__main__":
    rows = decode(sys.argv[1])
    real = [r for r in rows if r[1] & 0b10101111]          # failed now/this cycle/pending/confirmed/since clear/lamp
    print(f"{len(rows)} DTC records; {len(real)} with an actual failure flag:")
    for code, st, fl in real: print(f"  {code}  status {st:02X}  {', '.join(fl)}")
    print("Records with only 'not tested' flags (no fault):", " ".join(r[0] for r in rows if r not in real))
