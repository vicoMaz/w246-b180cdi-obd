# Mercedes W246 B 180 CDI (OM607 / Renault K9K) – engine ECU data IDs, decoding and logging tools

Open, reverse-engineered map of the **engine ECU live data** on the **Mercedes-Benz B-Class W246 B 180 CDI**
(engine **OM607**, which is the **Renault K9K 1.5 dCi**), readable with a **cheap ELM327 Bluetooth adapter**.

You get:
- **92 data IDs (DIDs)** with name, formula, unit and a confidence level: temperatures, rail pressure, injected quantity,
  **per-cylinder fuel corrections**, boost, EGR, **DPF soot and regeneration**, oil dilution, counters.
- **Tools** (Python, read-only) to log a drive, mark events with a key press, read the fault memory with a clone adapter,
  and decode the logs into physical values.
- **Real drive logs** (4 drives, identifying data removed) to check the decoding against.
- A **Torque Pro** import file with the same IDs.

Everything here is **read-only**: no coding, no adaptations, no clearing of fault codes, no writes to the car.

---

## Quick links

| I want to… | Go to |
|---|---|
| Read my car's data for the first time | [GET_STARTED.md](GET_STARTED.md) |
| Look up what an ID means and how to scale it | [docs/sensor-map.md](docs/sensor-map.md) |
| Use the IDs in my own code | [data/dids.csv](data/dids.csv) |
| Use the IDs in Torque Pro | [data/torque_pro_w246.csv](data/torque_pro_w246.csv) |
| Check per-cylinder injector balance | [docs/per-cylinder-corrections.md](docs/per-cylinder-corrections.md) |
| Know when a DPF regeneration is running | [docs/dpf-regeneration.md](docs/dpf-regeneration.md) |
| Read fault codes (P0xxx) with a clone ELM327 | [docs/fault-codes.md](docs/fault-codes.md) |
| Know what a cheap adapter can and cannot do | [docs/elm327-notes.md](docs/elm327-notes.md) |
| Work on this repo with an AI coding agent | [AGENTS.md](AGENTS.md) |

## Car and ECU

| | |
|---|---|
| Car | Mercedes-Benz B-Class **W246**, **B 180 CDI** with the **1.5 l** engine |
| Engine | **OM607** = Renault **K9K** 1.5 dCi, common rail diesel with DPF |
| Engine ECU | Continental **SID307 / SID310**, Mercedes part **A 607 901 01 00** |
| Bus | ISO 15765-4 CAN, 11-bit, 500 kbit/s (OBD protocol 6) |
| Address | request **0x7E0**, response **0x7E8** |
| Service | UDS **0x22** ReadDataByIdentifier, default session, no security access needed |

**Check your engine first.** Some B 180 CDI, notably with the 7G-DCT automatic, have the 1.8 l **OM651** instead,
with a different ECU: this repo does not apply to them. The engine code is on the type plate and in the registration documents.

**Other cars with the same engine** (A 180 CDI W176, CLA 180 CDI C117, GLA 180 CDI X156, Citan 108/109/111 CDI, and the
Renault/Dacia/Nissan K9K cars) very likely share many of these IDs, but **none of them were tested**. Check with
`tools/did_scan.py` and compare with the drive logs here before trusting a value.

## Most useful IDs

| DID | Meaning | Formula | Unit | Confidence |
|---|---|---|---|---|
| `2001` | Coolant temperature | `((A*256+B)-2730)/10` | °C | confirmed |
| `2801` | Rail pressure | `A*256+B` | bar | confirmed |
| `2806` | Injected fuel quantity | `(A*256+B)/100` | mg/stroke | confirmed |
| `FD07`…`FD0A` | Fuel flow correction, cylinders 1–4 | `(A*256+B)*0.0000305` | factor (1.00 = none) | probable |
| `2067` | Total engine torque | `(A*256+B)/32` | Nm | probable |
| `2401` / `2402` | Boost pressure, actual / setpoint | `A*256+B` | mbar | probable |
| `24F2` | Measured air mass flow | `(A*256+B)/10` | kg/h | probable |
| `242C` | Soot mass in the DPF | `(A*256+B)/100` | g | probable |
| `2542` | DPF differential pressure | `(A*256+B)-32768` | mbar | probable |
| `2488` | Engine running time since the last regeneration | `(A*256+B)/3600` | h | confirmed |
| `2442` | DPF inlet temperature | `((A*256+B)-2730)/10` | °C | confirmed |
| `2C04` | Gear engaged | `A&7`, then code − 1 = gear | – | probable |
| `2003` | Vehicle speed | `(A*256+B)/100` | km/h | confirmed |
| `2489` | Oil viscosity loss (dilution) | `(A*256+B)/655` | % | listed |

The full table, with notes and the evidence for each ID, is in **[docs/sensor-map.md](docs/sensor-map.md)**.

## Repository layout

```
README.md            this page
GET_STARTED.md       hardware, setup, first read, first logged drive
AGENTS.md            rules and conventions for AI coding agents and contributors
LICENSE              MIT
data/
  dids.csv           the sensor table: single source of truth
  torque_pro_w246.csv  generated Torque Pro import file
docs/
  sensor-map.md      generated human-readable table, grouped by system
  per-cylinder-corrections.md, dpf-regeneration.md, fault-codes.md, elm327-notes.md
tools/               Python 3 tools, standard library only, Linux (BlueZ RFCOMM)
drives/              4 drive logs, raw ECU answers, identifying IDs removed (see drives/README.md)
```

## Data provenance

**Nothing in this repository was copied from Mercedes-Benz, Renault or Continental software, documentation or databases.**
No dealer tool (Xentry/DAS, CLIP), no leaked database and no ECU firmware was used, read or dumped.
The data comes from three places:

1. **Our own reverse engineering.** We scanned the ECU of our own car for every data ID it answers to
   (service 0x22, read-only), then logged real drives and worked out each ID's meaning and scaling from the data:
   - correlation with the standard OBD-II values the ECU publishes (rpm, speed, coolant, MAF, boost, rail pressure),
   - exact unit fits (e.g. 0.1 K temperatures, `raw / 4` rpm),
   - setpoint/actual pairs that track each other,
   - physical behaviour (zero on overrun fuel cut, counters that tick once per second, values that jump during a DPF regeneration).
2. **The public [k9k_pids](https://github.com/MeganeClubUkraine/k9k_pids) list** by Megane Club Ukraine and contributors,
   released under the **MIT licence**. It is a community list of K9K data IDs for Torque Pro, made with the open-source
   [PyRen](https://gitlab.com/py_ren/pyren) tool. We used its names and formulas as a starting point and checked them against
   our logs. IDs whose name comes only from that list are marked **listed** or carry the source "K9K list".
   See [Credits](#credits).
3. **Public standards:** ISO 15765-4 (CAN diagnostics), ISO 14229 (UDS services and fault status bits), SAE J1979
   (OBD-II PIDs) and SAE J2012 (fault code numbering, e.g. P0201–P0204 = injector circuit, cylinders 1–4).

Every ID carries a `source` column (`logs`, `list`, `both`, `standard`) in `data/dids.csv`, so you can always tell which is which.

## Safety and disclaimer

- The tools only send **read** requests (service 0x22, 0x19, OBD modes 01/03/06/07). Do not add write, routine or
  clear-codes services; see [AGENTS.md](AGENTS.md).
- **Do not operate a laptop while driving.** Set things up while parked; let a passenger press the marker key.
- Names and formulas are reverse-engineered and can be wrong. Do not base a repair decision on one ID alone;
  confirm with a proper diagnosis.
- Provided as is, without warranty (see [LICENSE](LICENSE)). "Mercedes-Benz", "Renault", "Continental" and other names
  are trademarks of their owners; this project is not affiliated with or endorsed by them.

## Contributing

Owners of an OM607 / K9K car can help a lot:
- **Confirm or correct an ID**: open an issue with the DID, your raw answers and what the car was doing.
- **Add a car**: run `tools/did_scan.py`, then share which IDs answer (remove `F190` / VIN first).
- **Add a drive log**: especially one with a **DPF regeneration**, which would confirm the `246D` / `2434` / `280D` IDs.

See [AGENTS.md](AGENTS.md) for the conventions (the CSV is the single source of truth, docs are generated).

## Credits

- Data ID names and formulas marked "K9K list": [MeganeClubUkraine/k9k_pids](https://github.com/MeganeClubUkraine/k9k_pids),
  © 2020 Megane Club Ukraine and contributors, MIT licence.
- [PyRen](https://gitlab.com/py_ren/pyren), the open-source Renault diagnostic tool that list was created with.

## Keywords

Mercedes W246, B-Class, B180 CDI, B 180 CDI, OM607, OM 607, Renault K9K, 1.5 dCi, SID307, SID310, A6079010100,
ELM327, OBD2, OBD-II, UDS, ISO 14229, ISO-TP, DID, ReadDataByIdentifier, mode 22, live data, Torque Pro PIDs,
DPF regeneration, soot load, injector correction, cylinder balance, P0204, P0202, P0272, diesel diagnostics.
