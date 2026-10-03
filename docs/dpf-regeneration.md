# DPF, soot and regeneration

The diesel particulate filter (DPF) collects soot. When it is full enough, the ECU burns it off (**regeneration**)
by raising exhaust temperature: it throttles the intake, adds late post-injections and raises the idle speed.
A regeneration takes roughly 10–20 minutes of steady driving. Short trips interrupt it.

## Is a regeneration running right now?

**Simplest sign, with any OBD tool:** PID `0111` (intake throttle valve).

| PID 0111 | Meaning |
|---|---|
| ≈ 89.6 % | normal |
| **35–50 % at steady cruise**, or **~19 % at idle with idle raised to ~875 rpm** | regeneration running |

`tools/mark.py` shows **REGEN ACTIVE?** when PID 0111 drops below 80 %. The included log
`drives/2026-10-01/live15.csv` contains a regeneration (throttle down to 18 %).

## IDs

| DID | Meaning | Formula | Unit | Confidence |
|---|---|---|---|---|
| `242C` | Soot mass in the DPF | `(A*256+B)/100` | g | probable |
| `2542` | DPF differential pressure | `(A*256+B)-32768` | mbar | probable |
| `2442` | DPF inlet temperature | `((A*256+B)-2730)/10` | °C | confirmed |
| `2432` | DPF inlet temperature setpoint | `((A*256+B)-2730)/10` | °C | listed (640 outside regeneration) |
| `2447` | Exhaust flow through the DPF | `(A*256+B)/10` | m³/h | probable |
| `2488` | Engine running time since the last regeneration | `(A*256+B)/3600` | h | confirmed |
| `2487` | Duration of the last regeneration | `(A*256+B)/600` | min | listed |
| `2481` / `2485` | Successful regenerations / failed attempts | `A` | count | listed |
| `24A9` | Distance since the last successful regeneration | `A*65536+B*256+C` | km | listed |
| `24A5` | Soot mass after the last regeneration | `(A*256+B)/100` | g | listed |
| `2166` / `246D` / `2434` | Regeneration allowed / command / static regeneration | `A` | status | listed |
| `280D` / `280E` | Post-injection quantities | `(A*256+B)/100` | mg/stroke | listed |
| `2489` | Oil viscosity loss (dilution from regenerations) | `(A*256+B)/655` | % | listed |

`2488` restarted from zero right after an observed regeneration and then counts up by 1 per second of engine running,
across key cycles. The direct flags (`2166`, `246D`, `2434`) and post-injections (`280D`, `280E`) read 0 on all logged
drives, none of which captured them during a regeneration. **A log with a regeneration would confirm them**: please share one.

## Notes

- A cool-running engine (coolant levelling off below ~85 °C, e.g. a thermostat stuck open) makes more soot and makes
  regenerations harder to complete.
- Regenerations change how the engine feels (deeper, rougher at low rpm, higher idle). If you chase an intermittent
  vibration or noise, check whether it lines up with PID 0111 dropping.
