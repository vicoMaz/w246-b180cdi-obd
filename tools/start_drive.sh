#!/bin/bash
# Start a logged drive: fault snapshot -> logger (background) -> vibration marker (this window).
# Run in a normal terminal window:  OBD_ADDR=AA:BB:CC:DD:EE:FF tools/start_drive.sh
# Drives are saved in drives/<date_time>/ (or in $W246_DRIVES if set).
# All ECU access is read-only.
LOGGER="$(cd "$(dirname "$0")" && pwd)"
[ -n "$OBD_ADDR" ] || { echo "Set OBD_ADDR to your adapter's Bluetooth address first"; exit 1; }
RUN="${W246_DRIVES:-$LOGGER/../drives}/$(date +%Y-%m-%d_%H%M)"
mkdir -p "$RUN" || exit 1
echo "Drive folder: $RUN"

(
  cd "$RUN" || exit 1
  echo "=== $(date) start: waiting for ignition, fault snapshot ===" >> run.log
  until python3 "$LOGGER/uds_late.py" 7E0 7E8 190201 19020D 1902FF >> dtc_start.txt 2>&1 && grep -q '59 02' dtc_start.txt; do
    echo "$(date +%T) ECU not answering yet, retry in 15 s" >> run.log; sleep 15
  done
  echo "=== $(date) logging ===" >> run.log
  python3 "$LOGGER/log_everything.py" "$RUN" 3600 >> run.log 2>&1
  echo "=== $(date) logger stopped ===" >> run.log
) &
disown

# Keep the screen on (no blanking, lock or suspend) while the marker window is open
if command -v gnome-session-inhibit >/dev/null; then
  gnome-session-inhibit --inhibit idle:suspend --reason "W246 drive logging" python3 "$LOGGER/mark.py" "$RUN"
else
  python3 "$LOGGER/mark.py" "$RUN"
fi
