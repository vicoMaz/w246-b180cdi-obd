# Sensor map – engine ECU data IDs (DIDs)

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

**Totals:** 16 confirmed, 24 probable, 45 listed, 1 conflict, 6 candidate (92 IDs).

## Temperatures

| DID | Meaning | Formula | Unit | Confidence | Source | Notes |
|---|---|---|---|---|---|---|
| `2001` | Coolant temperature | `((A*256+B)-2730)/10` | °C | **confirmed** | K9K list + own logs | exact fit with PID 05 |
| `2007` | Coolant temperature (copy) | `((A*256+B)-2730)/10` | °C | **confirmed** | own logs | same value as 2001 |
| `244D` | Air temperature before intake throttle | `((A*256+B)-2730)/10` | °C | **confirmed** | K9K list + own logs | r = 0.98 with PID 0F |
| `240D` | Intake air temperature | `((A*256+B)-2730)/10` | °C | probable | K9K list + own logs | r = 0.90 with PID 0F |
| `2008` | Fuel temperature | `((A*256+B)-2730)/10` | °C | **confirmed** | K9K list + own logs | slow rise 30 -> 66 °C over a drive |
| `2439` | Turbine inlet temperature | `((A*256+B)-2730)/10` | °C | probable | K9K list + own logs | 100..545 °C, rises with load |
| `2438` | Turbine inlet temperature setpoint | `((A*256+B)-2730)/10` | °C | listed | K9K list | constant 700 °C outside regeneration |
| `2442` | DPF inlet temperature | `((A*256+B)-2730)/10` | °C | **confirmed** | K9K list + own logs | ~340 °C at motorway cruise |
| `2432` | DPF inlet temperature setpoint | `((A*256+B)-2730)/10` | °C | listed | K9K list | constant 640 °C outside regeneration |
| `2441` | Exhaust temperature downstream of 2442 (DPF outlet?) | `((A*256+B)-2730)/10` | °C | probable | own logs | not in the list; lags 2442 |

## Fuel injection and rail

| DID | Meaning | Formula | Unit | Confidence | Source | Notes |
|---|---|---|---|---|---|---|
| `2801` | Rail pressure | `A*256+B` | bar | **confirmed** | K9K list + own logs | ≈ 0.975 × PID 23 + 24 |
| `2802` | Rail pressure setpoint | `A*256+B` | bar | probable | K9K list + own logs | follows 2801, r = 0.985 |
| `2806` | Injected fuel quantity | `(A*256+B)/100` | mg/stroke | **confirmed** | K9K list + own logs | ~4 idle, ~14 at 110 km/h, ~42 full load, 0 on overrun fuel cut |
| `2809` | Total injection system quantity | `(A*256+B)/100` | mg/stroke | probable | K9K list + own logs | r = 0.975 with 2806, ~7 % lower |
| `280D` | Fuel quantity after main injection (post-injection 1) | `(A*256+B)/100` | mg/stroke | listed | K9K list | expected to rise during a regeneration |
| `280E` | Fuel quantity after main injection (post-injection 2) | `(A*256+B)/100` | mg/stroke | listed | K9K list | expected to rise during a regeneration |
| `2813` | Post-injection timing | `((A*256+B)-32767)/50` | ° crank | listed | K9K list |  |
| `2102` | Fuel consumed | `5*(A*256+B)/100` | l | listed | K9K list | trip computer value |
| `2103` | Fuel flow | `A` | l/h | listed | K9K list | trip computer value |
| `FDB6` | Rail fuel pressure regulator valve duty cycle | `(A*256+B)/655.36` | % | listed | K9K list | 21..25 % at idle and driving. FDB7..FDBA are refused by this ECU |
| `2061` | Unknown injection parameter | `A*256+B` | raw | candidate | own logs | 0x3200 at idle; 2062 and 2063 similar |

## Per-cylinder values

| DID | Meaning | Formula | Unit | Confidence | Source | Notes |
|---|---|---|---|---|---|---|
| `FD07` | Fuel flow correction cylinder 1 | `(A*256+B)*0.0000305` | factor | probable | K9K list + own logs | 1.00 = no correction. Updates only at idle. FD07..FD0A average 1.00 (balance) |
| `FD08` | Fuel flow correction cylinder 2 | `(A*256+B)*0.0000305` | factor | probable | K9K list + own logs | see FD07 |
| `FD09` | Fuel flow correction cylinder 3 | `(A*256+B)*0.0000305` | factor | probable | K9K list + own logs | see FD07 |
| `FD0A` | Fuel flow correction cylinder 4 | `(A*256+B)*0.0000305` | factor | probable | K9K list + own logs | see FD07 |
| `FD15` | Adaptation status cylinder 1 | `A` | code | listed | K9K list | read 7 on every drive |
| `FD16` | Adaptation status cylinder 2 | `A` | code | listed | K9K list | read 7 on every drive |
| `FD17` | Adaptation status cylinder 3 | `A` | code | listed | K9K list | read 7 on every drive |
| `FD18` | Adaptation status cylinder 4 | `A` | code | listed | K9K list | read 7 on every drive |
| `FD19` | Per-cylinder value 1 (unnamed in the list) | `((A*256+B)-32768)/2041.466` |  | listed | K9K list | static during a drive |
| `FD1A` | Per-cylinder value 2 (unnamed in the list) | `((A*256+B)-32768)/2041.466` |  | listed | K9K list | static during a drive |
| `FD1B` | Per-cylinder value 3 (unnamed in the list) | `((A*256+B)-32768)/2041.466` |  | listed | K9K list | static during a drive |
| `FD1C` | Per-cylinder value 4 (unnamed in the list) | `((A*256+B)-32768)/2041.466` |  | listed | K9K list | static during a drive |
| `28B4` | Learned injector correction table 1 of 8 (8 values) | – | raw | candidate | own logs | 8 signed 16-bit values centred on 0x8000, static. Same for 28B5..28BB |
| `2465` | Injector code slot? (4 records 2465..2468) | – | raw | candidate | own logs | only 2468 filled on this car |

## Engine, torque, pedal, gear

| DID | Meaning | Formula | Unit | Confidence | Source | Notes |
|---|---|---|---|---|---|---|
| `2002` | Engine speed | `(A*256+B)/4` | rpm | probable | K9K list + own logs | r = 0.91 with PID 0C (readings up to 2.5 s apart) |
| `2067` | Total engine torque | `(A*256+B)/32` | Nm | probable | own logs | ~30 idle, ~97 cruise, ~282 full load. 2068 and 2069 are copies |
| `2004` | Engine torque | `((A*256+B)-12800)/32` | Nm | listed | K9K list | weak match with 2067 (r = 0.44) |
| `202E` | Accelerator pedal position | `(A*256+B)/8` | % | listed | K9K list | 0..31 % on the logged drives; not verified |
| `2C04` | Gear engaged (code − 1 = gear) | `A&7` | gear | probable | K9K list + own logs | codes 2..7 match gears 1..6 by km/h per 1000 rpm (8.4 / 15.9 / 25.5 / 36.4 / – / 55); 1 = neutral or clutch |
| `2050` | Displayed vehicle speed | `(A*256+B)/100` | km/h | listed | K9K list | always 0 on this car |
| `2005` | ECU supply voltage | `(A*256+B)/100` | V | probable | K9K list + own logs | 14.1..14.9 V with the engine running, matches adapter voltage |

## Air, boost, intake throttle, EGR

| DID | Meaning | Formula | Unit | Confidence | Source | Notes |
|---|---|---|---|---|---|---|
| `2009` | Atmospheric pressure | `A*256+B` | mbar | probable | K9K list + own logs | 1001..1008 mbar |
| `2401` | Boost pressure | `A*256+B` | mbar | probable | K9K list + own logs | r = 0.90 with 10 × PID 0B |
| `2402` | Boost pressure setpoint | `A*256+B` | mbar | probable | K9K list + own logs | follows 2401, r = 0.78 |
| `240B` | Manifold pressure | `A*256+B` | mbar | listed | K9K list | r = 0.68 with 10 × PID 0B; range 790..2520, may be a setpoint |
| `24E1` | Manifold pressure (uncorrected) | `A*256+B` | mbar | **confirmed** | own logs | r = 0.94, slope 0.94 with 10 × PID 0B (kPa) |
| `2403` | Boost control solenoid duty cycle | `(A*256+B)/100` | % | listed | K9K list |  |
| `24F2` | Measured air mass flow | `(A*256+B)/10` | kg/h | probable | K9K list + own logs | r = 0.84 with PID 10 (MAF converted to kg/h), reads ~20 % lower |
| `2412` | Intake air per stroke | `(A*256+B)/10` | mg/stroke | listed | K9K list | 200..1720 mg/stroke; pairs with 2413 |
| `2413` | Intake air per stroke setpoint | `(A*256+B)/10` | mg/stroke | probable | K9K list + own logs | follows 2412, r = 0.99 |
| `2421` | Estimated air flow | `(A*256+B)/10` | mg/stroke | listed | K9K list | 350..910 mg/stroke, plausible for a 1.5 l with boost |
| `2448` | Turbine inlet pressure | `A*256+B` | mbar | probable | K9K list + own logs | 1000..3800 mbar, rises with load |
| `2404` | Intake throttle position | `(A*256+B)/20.491` | % | listed | K9K list | reads 78.6..79.4 when PID 11 reads 89.4..89.8; no regeneration logged to check movement |
| `2405` | Intake throttle setpoint | `((A*256+B)-31981)/20` | % | listed | K9K list | decodes to ~140 %, formula probably wrong |
| `2407` | EGR valve position | `(A*256+B)/20.491` | % | listed | K9K list | mostly 0, max 36 %; does not follow 259B (r = 0.35) |
| `2408` | EGR valve setpoint | `(A*256+B)/20.491` | % | listed | K9K list | constant 1580 % on this car, formula probably wrong |
| `2409` | EGR valve command | `((A*256+B)-32767)/100` | % | listed | K9K list |  |
| `256B` | EGR valve position (logs) or exhaust flap position (list) | `(A*256+B)/20.492` | % | **conflict** | K9K list + own logs | r = 0.98 with 259B but not with 2407 (r = 0.36). The list meaning comes from the K9K 636 variant with low-pressure EGR. 256A = 256B + 0x8000 |
| `259B` | EGR valve position sensor voltage | `A*256+B` | mV | probable | own logs | ~890 open ... 3945 closed; pinned closed on fuel cut and full load |
| `2527` | Actuator setpoint (turbo vanes?) | `(A*256+B)/100` | % | candidate | own logs |  |
| `2528` | Actuator position (turbo vanes?) | `(A*256+B)/100` | % | candidate | own logs |  |

## DPF, soot and regeneration

| DID | Meaning | Formula | Unit | Confidence | Source | Notes |
|---|---|---|---|---|---|---|
| `242C` | Soot mass in DPF | `(A*256+B)/100` | g | probable | K9K list + own logs | 5.7 -> 14.3 g over three days of short drives, only rises while driving |
| `2542` | DPF differential pressure | `(A*256+B)-32768` | mbar | probable | K9K list + own logs | 2..114 mbar, rises with exhaust flow (r = 0.74 with MAF) |
| `24FB` | DPF differential pressure (corrected) | `(A*256+B)-32768` | mbar | listed | K9K list |  |
| `2447` | Exhaust flow through DPF | `(A*256+B)/10` | m³/h | probable | K9K list + own logs | 3..430 m³/h, rises with load |
| `2488` | Engine running time since last regeneration | `(A*256+B)/3600` | h | **confirmed** | K9K list + own logs | +1 per second of running; restarted right after an observed regeneration |
| `2487` | Duration of last regeneration | `(A*256+B)/600` | min | listed | K9K list |  |
| `2481` | Successful regenerations | `A` | count | listed | K9K list |  |
| `2485` | Failed regeneration attempts | `A` | count | listed | K9K list |  |
| `24A9` | Distance since last successful regeneration | `A*65536+B*256+C` | km | listed | K9K list |  |
| `24A5` | Soot mass after last regeneration | `(A*256+B)/100` | g | listed | K9K list |  |
| `24BB` | Distance since DPF replacement | `A*65536+B*256+C` | km | listed | K9K list |  |
| `2166` | Regeneration allowed | `A` | status | listed | K9K list |  |
| `246D` | Regeneration command | `A` | status | listed | K9K list |  |
| `2434` | Static regeneration | `A` | status | listed | K9K list |  |
| `2810` | Soot estimate? | `(A*256+B)-32768` |  | candidate | own logs |  |

## Oil

| DID | Meaning | Formula | Unit | Confidence | Source | Notes |
|---|---|---|---|---|---|---|
| `2489` | Oil viscosity loss | `(A*256+B)/655` | % | listed | K9K list |  |
| `2294` | Oil dilution | `((A*16777216+B*65536+C*256+D)-(4294967296 if A>127 else 0))/214748364.8` | % | listed | K9K list | decodes oddly on this car, unverified |

## Counters and timers

| DID | Meaning | Formula | Unit | Confidence | Source | Notes |
|---|---|---|---|---|---|---|
| `2006` | Odometer | `A*65536+B*256+C` | km | **confirmed** | K9K list + own logs | +1.01 per km driven |
| `2003` | Vehicle speed | `(A*256+B)/100` | km/h | **confirmed** | K9K list + own logs | r = 0.999, slope 1.00 with PID 0D. Earlier 'distance accumulator' guess was wrong |
| `2168` | Engine start counter 4 | `A*65536+B*256+C` | count | listed | K9K list |  |
| `2169` | Engine start counter 3 | `A*65536+B*256+C` | count | listed | K9K list |  |
| `216A` | Engine start counter 2 | `A*65536+B*256+C` | count | listed | K9K list |  |
| `216B` | Engine start counter 1 | `A*65536+B*256+C` | count | listed | K9K list |  |
| `210E` | Crankshaft revolutions | `A*256+B` | million | listed | K9K list |  |
| `25B1` | ECU clock | `A*256+B` | min | probable | own logs | keeps counting with the ignition off |
| `2296` | Running timer | `(A*256+B)/10` | s | **confirmed** | own logs | +10.0 per second |
| `2557` | Running timer | `(A*256+B)/10` | s | **confirmed** | own logs | +10.0 per second |

## Identification

| DID | Meaning | Formula | Unit | Confidence | Source | Notes |
|---|---|---|---|---|---|---|
| `F190` | VIN | – | ASCII | **confirmed** | ISO 14229 | ISO 14229 standard identifier |
| `F111` | ECU part number | – | ASCII | **confirmed** | ISO 14229 |  |
| `F121` | ECU software number | – | ASCII | **confirmed** | ISO 14229 |  |

## Standard OBD-II PIDs used by the logger

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
