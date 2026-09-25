"""
Day 3: merge the retry run into the first run.
Reads  : sections_geocoded_raw.csv, sections_geocoded_retry_raw.csv
Writes : sections_geocoded_combined_raw.csv  (same columns as the first run + geocode_source + retry_decision)

A retry result replaces the first-run point only when ALL of these hold:
  1. the retry found something,
  2. its name matches the section name (a different place's name is never accepted),
  3. it lies in Hyderabad, Ranga Reddy or Medchal-Malkajgiri district,
  4. it scores at least 1 point better than the first-run point (score = km from the
     expected area + 3 if a building/road + 10 if a whole mandal/city + 5 if name mismatch),
     or the first run found nothing.
"""
import math, re
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
p1 = pd.read_csv(HERE / "sections_geocoded_raw.csv")
rt = pd.read_csv(HERE / "sections_geocoded_retry_raw.csv")
OK_DISTRICTS = ("hyderabad", "ranga reddy", "medchal")
norm = lambda s: re.sub(r"[^a-z]", "", str(s).lower())

def km(a, b, c, d):
    a, b, c, d = map(math.radians, [a, b, c, d])
    h = math.sin((c-a)/2)**2 + math.cos(a)*math.cos(c)*math.sin((d-b)/2)**2
    return 6371*2*math.asin(math.sqrt(h))

def score(lat, lon, cat, rank, name, query, alat, alon):
    pen = (3 if cat not in ("place", "boundary") else 0) + (10 if (rank if pd.notna(rank) else 30) <= 16 else 0)
    first, v = str(name).split(",")[0], str(query).split(",")[0]
    mismatch = norm(v)[:6] not in norm(first) and norm(first)[:6] not in norm(v)
    return km(alat, alon, lat, lon) + pen + (5 if mismatch else 0), mismatch

out = p1.copy()
out["geocode_source"] = np.where(out.geocode_status.eq("found"), "first run", "")
out["retry_decision"] = ""
for _, r in rt.iterrows():
    i = out.index[out.section_id == r.section_id][0]
    if r.retry_status != "found":
        out.at[i, "retry_decision"] = "retry found nothing - kept first run"; continue
    rs, rmis = score(r.best_lat, r.best_lon, r.best_category, r.best_place_rank, r.best_name, r.best_query, r.anchor_lat, r.anchor_lon)
    in_area = any(d in str(r.best_name).lower() for d in OK_DISTRICTS)
    if out.at[i, "geocode_status"] == "found":
        ps, _ = score(out.at[i, "lat"], out.at[i, "lon"], out.at[i, "osm_category"], out.at[i, "osm_place_rank"],
                      out.at[i, "osm_name"], out.at[i, "query_used"], r.anchor_lat, r.anchor_lon)
    else:
        ps = np.inf
    if rmis:
        out.at[i, "retry_decision"] = f"retry rejected: name doesn't match ({str(r.best_name).split(',')[0]})"
    elif not in_area:
        out.at[i, "retry_decision"] = "retry rejected: outside Hyderabad/Ranga Reddy/Medchal districts"
    elif rs <= ps - 1:
        out.loc[i, ["lat", "lon", "osm_name", "osm_category", "osm_type", "osm_place_rank", "query_used"]] = \
            [r.best_lat, r.best_lon, r.best_name, r.best_category, r.best_type, r.best_place_rank, r.best_query]
        out.at[i, "geocode_status"] = "found"
        out.at[i, "geocode_source"] = "retry"
        out.at[i, "other_candidates"] = r.other_candidates
        out.at[i, "retry_decision"] = "retry accepted" + (" (first run found nothing)" if np.isinf(ps) else f" (score {rs:.1f} vs {ps:.1f})")
    else:
        out.at[i, "retry_decision"] = f"retry not better (score {rs:.1f} vs {ps:.1f}) - kept first run"
out.to_csv(HERE / "sections_geocoded_combined_raw.csv", index=False)
print(out.geocode_source.value_counts().to_string())
print(out[out.retry_decision != ""].retry_decision.str.split(" \\(|:").str[0].value_counts().to_string())
