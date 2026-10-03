# ELM327 clone notes

Tested adapter: a ~€10 "ELM327 v1.5" clone (shows up as "OBD BLE" / "OBDII"), used over **classic Bluetooth RFCOMM, channel 1**.

## What works

- Standard OBD-II PIDs (mode 01), modes 03 / 06 / 07 / 09.
- UDS `0x22` reads on the engine ECU (`7E0` → `7E8`), including multi-frame answers.
- About 7 reads per second in practice (~0.14 s per request with `ATST19`).

## What does not (on this clone)

- **Other modules** (gearbox, ESP, airbag, body). The clone's CAN filtering only passes replies on `7E8`–`7EF`, so modules
  on other addresses cannot be read. Use a better adapter (OBDLink MX+/EX, vLinker FS/MC+) for those.
- **Late answers** (`7F xx 78` response pending): the clone stops listening. Workaround in `tools/uds_late.py`.
- **Long multi-frame answers** sometimes lose frames (`INCOMPLETE`). Ask for less at a time.

## Settings used by the tools

```
ATZ  ATE0  ATL0  ATS1  ATH0  ATSP6  ATST19   then  ATSH7E0
```

`ATSP6` = ISO 15765-4 CAN 11-bit 500 kbit/s. `ATST19` shortens the response timeout (~100 ms) to speed up polling.

## Bluetooth tips

- Only **one** program can be connected at a time (close Torque or any other app).
- The adapter drops the link when the ignition goes off, and sometimes on its own. The logger reconnects automatically.
- Some adapters stay powered with the ignition off and slowly drain the battery: unplug it when parked for days.
