"""Vibration marker: press SPACE whenever you feel the vibration. Shows live logger status.

Usage: mark.py OUT_DIR
  SPACE  -> records a vibration mark (epoch + clock time) in OUT_DIR/markers.csv, beeps, confirms on screen
  n      -> records a 'no vibration now' mark (useful as a comparison point)
  q      -> quits the marker window (the logger keeps running in the background)
Must run in a real terminal window (it reads single key presses)."""
import sys, os, time, json, csv, select, termios, tty, datetime

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
MARKS = os.path.join(OUT_DIR, "markers.csv")
STATUS = os.path.join(OUT_DIR, "status.json")

def status_line():
    try:
        st = json.load(open(STATUS))
    except (OSError, ValueError):
        return "logger: starting..."
    if st.get("state") != "ok":
        return f"logger: {st.get('state')}"
    regen = "  REGEN ACTIVE?" if st.get("regen") else ""
    return (f"{st.get('elapsed', 0)//60:3d} min | {st.get('speed') or 0:3} km/h {st.get('rpm') or 0:5.0f} rpm | "
            f"coolant {st.get('coolant')} °C | throttle {st.get('throttle')} %{regen} | rows {st.get('rows')}")

new = not os.path.exists(MARKS)
fh = open(MARKS, "a", newline=""); w = csv.writer(fh)
if new: w.writerow(["epoch", "wall", "kind", "status_at_mark"]); fh.flush()

fd = sys.stdin.fileno(); old = termios.tcgetattr(fd)
count = 0
print("\n  VIBRATION MARKER  -  SPACE = vibration now   n = no vibration now   q = quit marker\n")
try:
    tty.setcbreak(fd)
    while True:
        print("\r\033[K" + status_line(), end="", flush=True)
        r, _, _ = select.select([sys.stdin], [], [], 1.0)
        if not r: continue
        k = sys.stdin.read(1)
        if k in (" ", "n"):
            now = time.time(); wall = datetime.datetime.now().strftime("%H:%M:%S")
            kind = "VIBRATION" if k == " " else "NO_VIBRATION"
            w.writerow([f"{now:.2f}", wall, kind, status_line()]); fh.flush()
            if kind == "VIBRATION": count += 1
            print(f"\r\033[K\a  >>> {kind} marked at {wall}" + (f"  (#{count})" if kind == "VIBRATION" else ""))
        elif k in ("q", "Q"):
            break
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old)
    fh.close()
    print(f"\nmarker closed ({count} vibration marks). Logger keeps running until ignition off.")
