# Per-cylinder fuel corrections (injector balance)

The ECU balances the four cylinders at idle. It watches how much the crankshaft speeds up after each cylinder fires,
and gives a weak cylinder more fuel and a strong one less, until the engine runs evenly.
The result can be read live, one value per cylinder.

| DID | Cylinder | Formula | Meaning |
|---|---|---|---|
| `FD07` | 1 | `(A*256+B)*0.0000305` | fuel flow correction factor |
| `FD08` | 2 | same | |
| `FD09` | 3 | same | |
| `FD0A` | 4 | same | |
| `FD15`–`FD18` | 1–4 | `A` | adaptation status (read 7 on every drive so far) |
| `FD19`–`FD1C` | 1–4 | `((A*256+B)-32768)/2041.466` | unnamed in the list, static during a drive |

The names "cylinder 1–4" come from the K9K list; the behaviour below fits them.

## How to read the factor

- **1.00** = no correction. **1.25** = that cylinder gets 25 % more fuel than the base amount; **0.85** = 15 % less.
- The four factors **average 1.00**: the raw values always add up to ≈ 4 × 32768. It is a balance between cylinders,
  so one weak cylinder pushes the others below 1.00.
- The values **only change at idle**. While driving they stay frozen at the last idle value.

## What we observed

| Situation | Spread of the four factors |
|---|---|
| Warm engine (coolant ≥ 75 °C), 2–4 min idle | all within about **0.92–1.05** |
| First minutes after a cold start (coolant ~35 °C) | up to **0.68–1.45**, shrinking steadily as the engine warmed |

So **always compare at the same temperature**. A large correction on a cold start that disappears when warm points to
a cylinder that is weak when cold (for example a sticking or dirty injector, or lower compression). A large correction
that stays when warm is a stronger sign of a problem with that cylinder.

We do not know the ECU's own limits for these values. Do not replace parts on these numbers alone.

## How to measure

1. Log a drive with `tools/start_drive.sh` (the logger reads `FD07`–`FD0A` every ~3 s).
2. For a **cold** reading: start logging before the first start of the day.
3. For a **warm** reading: end the drive with **2 minutes at idle**, coolant ≥ 75 °C, no electrical loads changing.
4. Decode: `python3 tools/decode_log.py drives/<date>/everything.csv --wide` and look at the `FD07`–`FD0A` columns at idle (speed 0).

Related fault codes (SAE numbering): **P0201–P0204** injector circuit, cylinders 1–4;
**P0263 / P0266 / P0269 / P0272** cylinder contribution/balance, cylinders 1–4. See [fault-codes.md](fault-codes.md).

## Usual next checks (outside this repo)

Connector and wiring of the injector concerned, injector **back-leak (return flow) test**, and if needed swapping two
injectors (new copper washers, and the injector codes must be programmed into the ECU) to see whether the correction
follows the injector.
