# Day 2–3: placing sections on the map

| File | What it is |
|---|---|
| `day2_geocode_sections.ipynb` | Colab notebook, first run: looks up all 163 sections on OpenStreetMap |
| `sections_geocoded_raw.csv` | Output of the first run |
| `day3_retry_geocode.ipynb` | Colab notebook, retry of the 58 "check first" sections |
| `sections_geocoded_retry_raw.csv` | Output of the retry |
| `day3_merge_retry.py` | Keeps the better point per section → `sections_geocoded_combined_raw.csv` |
| `day2_flag_geocodes.py` | Adds quality flags and review priority → `sections_geocoded.csv` |
| `sections_geocoded.csv` | **Main output:** one row per section with coordinates, flags and priority |
| `manual_fixes.csv` | Hand-check sheet for the 29 "check first" sections |

To rebuild: run `day3_merge_retry.py`, then `day2_flag_geocodes.py`. The flagging script reads `../sections_monthly.csv` from the main folder.
