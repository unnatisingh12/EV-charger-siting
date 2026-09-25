# Hyderabad EV Charger Siting

An open tool that predicts how heavily a new public EV charger would be used in each Hyderabad neighbourhood. It is trained and tested on Telangana's measured charging-electricity data.

## Status

- [x] **Day 1:** monthly table of EV charging use per section (163 sections, Jan 2023 – Aug 2026)
- [ ] Day 2–3: place sections on the map
- [ ] Day 4: define the target (median units per connection, last 6 months)
- [ ] Days 5–14: features, model, web map

## Files

| File | What it is |
|---|---|
| `data/raw/tg_ev_monthly_master.csv` | Original data, unchanged |
| `data/processed/sections_monthly.csv` | One row per section per month, initial greater-Hyderabad study area |
| `data/processed/negative_rows_removed.csv` | The 13 negative-unit rows removed, kept for audit |
| `scripts/day1_build_sections_monthly.py` | Rebuilds both processed files from the raw data |

## Day 1 cleaning rules

- **Study area (provisional):** the 9 TGSPDCL circles Banjara Hills, Cybercity, Habsiguda, Hyderabad Central, Hyderabad South, Medchal, Rajendra Nagar, Saroornagar and Secunderabad. This is not a definitive Hyderabad boundary; it will be revisited after mapping.
- **Section identity:** `section_id` = circle + section (e.g. `CYBERCITY_KONDAPUR`), because some section names repeat across circles.
- **Areas:** all area rows within a section-month are summed. Area names are not edited.
- **Negative readings:** removed (both units and connections) and kept in the audit file.
- **Units per connection:** units ÷ all connections (`totservices`), including idle connections.
- **Zeros:** kept. A zero means infrastructure exists but went unused.
- **Missing months:** left missing, never filled with zero.
- **Load:** the unit (kW or hp) is not stated in the source, so load is not used in calculations.

## Data source and licence

Telangana EV Charging Stations Electricity Consumption Dataset, published by the Telangana Southern Power Distribution Company Limited (TGSPDCL) via Open Data Telangana, under the Open Government License – India. Dataset page: https://aikosh.indiaai.gov.in/home/datasets/details/telangana_ev_charging_stations_electricity_consumption_dataset.html
