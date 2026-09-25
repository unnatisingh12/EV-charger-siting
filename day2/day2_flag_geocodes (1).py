"""
Day 2: flag questionable geocodes.
Reads  : sections_geocoded_combined_raw.csv (first run + retry), sections_monthly.csv
Writes : sections_geocoded.csv  (one row per section, coordinates + flags)
"""
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
raw = pd.read_csv(HERE / "sections_geocoded_combined_raw.csv")
monthly = pd.read_csv(HERE / "sections_monthly.csv")
meta = monthly[["section_id", "division", "subdivision"]].drop_duplicates()
g = raw.merge(meta, on="section_id", how="left")

# Rule thresholds (agreed defaults; change here if needed)
BOX = dict(lat_min=16.80, lat_max=17.80, lon_min=77.95, lon_max=78.95)  # generous greater-Hyderabad box
FAR_FROM_CIRCLE_KM = 15
FAR_FROM_DIVISION_KM = 8
VAGUE_RANK = 16          # OSM place_rank <= 16 = whole mandal / city / district
AREA_CATEGORIES = {"place", "boundary"}   # anything else = matched a building, road, shop...

def km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2-lat1)/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    return 6371 * 2 * np.arcsin(np.sqrt(a))

found = g.geocode_status.eq("found")

def dist_to_group(col):
    out = pd.Series(np.nan, index=g.index)
    for i in g[found].index:
        peers = g[found & g[col].eq(g.at[i, col]) & (g.index != i)]
        if len(peers) >= 2:
            out[i] = km(g.at[i, "lat"], g.at[i, "lon"], peers.lat.median(), peers.lon.median())
    return out.round(1)

g["km_from_circle_centre"] = dist_to_group("circle")
g["km_from_division_centre"] = dist_to_group("division")
key = g.lat.round(4).astype(str) + "," + g.lon.round(4).astype(str)
dup = found & key.duplicated(keep=False)

flags = {
    "not_found": ~found,
    "outside_greater_hyderabad": found & ~(g.lat.between(BOX["lat_min"], BOX["lat_max"]) & g.lon.between(BOX["lon_min"], BOX["lon_max"])),
    "far_from_circle": g.km_from_circle_centre > FAR_FROM_CIRCLE_KM,
    "far_from_division": g.km_from_division_centre > FAR_FROM_DIVISION_KM,
    "too_vague": found & (g.osm_place_rank <= VAGUE_RANK),
    "shares_coordinates": dup,
    "matched_a_building_or_road": found & ~g.osm_category.isin(AREA_CATEGORIES),
}
for k, v in flags.items():
    g[f"flag_{k}"] = v.fillna(False).astype(bool)

serious = ["not_found", "outside_greater_hyderabad", "far_from_circle", "far_from_division", "too_vague", "shares_coordinates"]
g["flags"] = g.apply(lambda r: "; ".join(k for k in flags if r[f"flag_{k}"]), axis=1)
# A section that is far from its neighbours but matched a real town or village with the
# same name is probably a genuinely outlying section (e.g. Amangal), not a wrong match.
outlying_town = g.osm_type.isin(["town", "village"]) & ~g.flag_outside_greater_hyderabad
far_only = (g.flag_far_from_circle | g.flag_far_from_division)
other_serious = g[[f"flag_{k}" for k in serious if not k.startswith("far_")]].any(axis=1)
g["note"] = np.where(far_only & outlying_town & ~other_serious,
                     "far from neighbours but matched a real town/village of that name - probably an outlying section", "")
g["review_priority"] = np.select(
    [other_serious | (far_only & ~outlying_town), far_only | g.flag_matched_a_building_or_road],
    ["1_check_first", "2_check_if_time"], "3_looks_ok")
g["alias_used"] = found & ~g.apply(lambda r: str(r.query_used).upper().startswith(str(r.section).title().upper()), axis=1)

cols = ["section_id", "circle", "division", "subdivision", "section", "geocode_status", "lat", "lon",
        "review_priority", "flags", "note", "km_from_circle_centre", "km_from_division_centre",
        "query_used", "alias_used", "osm_name", "osm_category", "osm_type", "osm_place_rank", "n_candidates", "other_candidates"] \
       + [f"flag_{k}" for k in flags]
g = g[cols].sort_values(["review_priority", "circle", "section"])
g.to_csv(HERE / "sections_geocoded.csv", index=False)
print(g.review_priority.value_counts().sort_index().to_string())
print({k: int(g[f'flag_{k}'].sum()) for k in flags})
