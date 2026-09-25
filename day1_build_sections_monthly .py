"""
Day 1: build one row per section per month for the initial greater-Hyderabad study area.

All files sit in the same folder as this script.
Reads  : tg_ev_monthly_master.csv   (never modified)
Writes : sections_monthly.csv
         negative_rows_removed.csv

Decisions (agreed 25 Sep 2026):
- Study area: the 9 TGSPDCL circles below, labelled "initial greater-Hyderabad study area"
  (provisional; revisit after geocoding).
- Negative-unit rows are deleted (units AND connections) and saved to an audit file.
- Denominator = totservices (all connections, including idle ones).
- Zero-unit rows are kept.
- Missing months stay missing (no row) - never filled with zero.
- A section is identified by circle + section -> section_id, e.g. CYBERCITY_KONDAPUR.
- Area names are not edited or merged by hand; all area rows in a section are summed.
- Load is carried through but its unit (kW or hp) is unconfirmed per the official metadata.
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "tg_ev_monthly_master.csv"
OUT = ROOT

STUDY_AREA_CIRCLES = [
    "BANJARA HILLS", "CYBERCITY", "HABSIGUDA", "HYDERABAD CENTRAL", "HYDERABAD SOUTH",
    "MEDCHAL", "RAJENDRA NAGAR", "SAROORNAGAR", "SECUNDERABAD",
]
STUDY_AREA_LABEL = "initial greater-Hyderabad study area"


def make_id(circle: str, section: str) -> str:
    def clean(s):
        return re.sub(r"[^A-Z0-9]+", "_", s.strip().upper()).strip("_")
    return f"{clean(circle)}_{clean(section)}"


def main():
    raw = pd.read_csv(RAW)
    df = raw[(raw.discom == "TGSPDCL") & raw.circle.isin(STUDY_AREA_CIRCLES)].copy()
    df["section_id"] = [make_id(c, s) for c, s in zip(df.circle, df.section)]

    # 1. Negative readings -> audit file, then remove
    neg = df[df.units < 0].copy()
    neg["reason_removed"] = "negative units (likely billing correction)"
    OUT.mkdir(parents=True, exist_ok=True)
    neg.to_csv(OUT / "negative_rows_removed.csv", index=False)
    kept = df[df.units >= 0]

    # 2. Sum all area rows within each section-month
    keys = ["section_id", "discom", "circle", "division", "subdivision", "section", "date", "year", "month"]
    g = kept.groupby(keys, as_index=False).agg(
        n_areas=("area", "size"),
        n_zero_unit_areas=("units", lambda u: int((u == 0).sum())),
        totservices=("totservices", "sum"),
        billedservices=("billedservices", lambda b: b.sum(min_count=1)),
        billedservices_incomplete=("billedservices", lambda b: bool(b.isna().any())),
        units=("units", "sum"),
        load_unit_unconfirmed=("load", "sum"),
    )
    g["units_per_connection"] = (g.units / g.totservices).round(2)

    # note how many negative rows were removed from each section-month
    negc = neg.groupby(["section_id", "date"]).size().rename("n_negative_rows_removed")
    g = g.merge(negc, on=["section_id", "date"], how="left")
    g["n_negative_rows_removed"] = g.n_negative_rows_removed.fillna(0).astype(int)
    g.insert(1, "study_area", STUDY_AREA_LABEL)

    g = g.sort_values(["section_id", "date"]).reset_index(drop=True)
    g.to_csv(OUT / "sections_monthly.csv", index=False)
    print(f"sections_monthly.csv: {len(g)} rows, {g.section_id.nunique()} sections")
    print(f"negative_rows_removed.csv: {len(neg)} rows")


if __name__ == "__main__":
    main()
