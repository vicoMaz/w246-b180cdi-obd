# Fault codes with a clone ELM327

## Why generic apps show nothing

On this ECU, OBD mode `03` often answers "no codes" even when faults are stored. The full fault memory is only available
through **UDS service 0x19** (ReadDTCInformation). The ECU answers that request late: first `7F 19 78`
("response pending"), then the data about a second later. Cheap ELM327 clones stop listening after the `78` and miss it.

`tools/uds_late.py` keeps the clone listening (by sending tester-present frames to an unused address while the receive
filter stays on `7E8`), then reassembles the multi-frame answer.

```bash
python3 tools/uds_late.py 7E0 7E8 19020D     # faults that failed, are pending or are stored (short answer)
python3 tools/uds_late.py 7E0 7E8 1902FF     # every code the ECU knows, including ~40 never-failed ones (long answer)
python3 tools/decode_dtc.py "59 02 FF 02 04 3A 69"
```

Read-only: nothing is cleared.

## Reading the answer

`59 02 <mask>` then 4 bytes per code: 2 bytes code, 1 byte failure type, 1 byte status.
`02 04 3A 69` → **P0204**, failure type `3A`, status `0x69`.

Status bits (ISO 14229):

| Bit | Value | Meaning |
|---|---|---|
| 0 | 0x01 | failing now (last test failed) |
| 1 | 0x02 | failed this operation cycle |
| 2 | 0x04 | pending |
| 3 | 0x08 | confirmed (stored) |
| 4 | 0x10 | not tested since the last clear |
| 5 | 0x20 | failed since the last clear |
| 6 | 0x40 | not tested this operation cycle |
| 7 | 0x80 | warning lamp requested |

A code with only `0x40` and/or `0x10` set has **never failed**: the ECU just lists it as supported.
`decode_dtc.py` separates these from real faults.

## Codes relevant to the injection

SAE J2012 numbering (generic meaning):

| Code | Meaning |
|---|---|
| P0201 / P0202 / P0203 / P0204 | Injector circuit, cylinder 1 / 2 / 3 / 4 |
| P0263 / P0266 / P0269 / P0272 | Cylinder 1 / 2 / 3 / 4 contribution/balance |
| P0380 | Glow plug circuit |
| P0488 | EGR throttle control range/performance |

The failure-type byte (e.g. `3A`, `24`) is manufacturer specific; we do not know its meaning on this ECU.
