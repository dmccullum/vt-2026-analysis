"""Build town-level demographics for Vermont county subdivisions.

Needs a Census API key in env CENSUS_API_KEY (api.census.gov now redirects
keyless requests to missing_key.html). Gazetteer + SOS name matching run
without a key; the ACS step aborts if no key is set.
"""
import json, os, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/census"
OUT = ROOT / "data/processed/town_demographics.csv"
SOS = ROOT / "data/raw/sos2026/turnOut.json"
RAW.mkdir(parents=True, exist_ok=True)

GAZ_URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/{y}_Gazetteer/{y}_gaz_cousubs_50.txt"
B01001 = [f"B01001_{i:03d}E" for i in list(range(20, 26)) + list(range(44, 50))]
VARS = ["B01003_001E", "B01002_001E", "B19013_001E", "B15003_001E", "B15003_022E", "B15003_023E",
        "B15003_024E", "B15003_025E", "B03002_001E", "B03002_003E", "B25003_001E", "B25003_002E",
        "B25004_006E", "B25001_001E", "B17001_001E", "B17001_002E", "B08301_001E", "B08301_021E",
        "B05002_001E", "B05002_003E", "B01001_001E", "B19301_001E", "B11001_001E", "B11001_008E", "B20002_001E"] + B01001


def get(url, **kw):
    for i in range(5):
        r = requests.get(url, timeout=90, allow_redirects=False, **kw)
        if r.status_code == 200:
            return r
        if r.status_code == 302 and "missing_key" in r.headers.get("location", ""):
            sys.exit("Census API requires a key: set CENSUS_API_KEY")
        if r.status_code in (429, 503):
            time.sleep(10 * (i + 1)); continue
        r.raise_for_status()
    r.raise_for_status()


def gazetteer():
    for y in (2024, 2023):
        f = RAW / f"gaz_cousubs_50_{y}.txt"
        if not f.exists():
            try:
                f.write_bytes(get(GAZ_URL.format(y=y)).content)
            except Exception:
                continue
        return pd.read_csv(f, sep="\t", dtype={"GEOID": str}, skipinitialspace=True).rename(columns=str.strip)


def sos_name(census_name, all_bases):
    base = re.sub(r" (town|city)$", "", census_name.strip(), flags=re.I)
    kind = "CITY" if re.search(r" city$", census_name, re.I) else "TOWN"
    n = base.upper().replace("ST. ", "SAINT ")
    if n == "ESSEX JUNCTION":
        return "ESSEX JUNCTION CITY"
    if n == "ESSEX" or all_bases.count(base.lower()) > 1:
        return f"{n} {kind}"
    return n


def acs():
    """Read ACS 5-year table-based summary files (keyless), pre-filtered to VT county subdivisions:
    data/raw/census/acs2024_<table>.dat  (see README for the download command)."""
    tabs = sorted({v.split("_")[0].lower() for v in VARS})
    df = None
    for t in tabs:
        d = pd.read_csv(RAW / f"acs2024_{t}.dat", sep="|", dtype=str)
        d = d.rename(columns=lambda c: re.sub(r"^([BC]\d+)_E(\d+)$", r"\1_\2E", c))
        d = d[["GEO_ID"] + [c for c in d.columns if c.endswith("E") and c in VARS]]
        df = d if df is None else df.merge(d, on="GEO_ID")
    df["state"] = "50"
    df["county"] = df.GEO_ID.str[-8:-5]
    df["county subdivision"] = df.GEO_ID.str[-5:]
    df["NAME"] = ""
    df["vintage"] = 2024
    return df


COUNTIES = {"001": "ADDISON", "003": "BENNINGTON", "005": "CALEDONIA", "007": "CHITTENDEN", "009": "ESSEX",
            "011": "FRANKLIN", "013": "GRAND ISLE", "015": "LAMOILLE", "017": "ORANGE", "019": "ORLEANS",
            "021": "RUTLAND", "023": "WASHINGTON", "025": "WINDHAM", "027": "WINDSOR"}


def main():
    gaz = gazetteer()
    gaz["base"] = gaz["NAME"].str.replace(r" (town|city)$", "", regex=True).str.lower()
    bases = gaz["base"].tolist()
    gaz["town"] = [sos_name(n, bases) for n in gaz["NAME"]]
    sos = {x["tn"] for x in json.loads(SOS.read_text())["d"]}
    print("SOS not in Census:", sorted(sos - set(gaz["town"])))
    print("Census not in SOS:", sorted(set(gaz["town"]) - sos))
    a = acs()
    for c in a.columns:
        if re.match(r"[BC]\d", c):
            a[c] = pd.to_numeric(a[c], errors="coerce")
            a.loc[a[c] < -1e6, c] = np.nan
    a["geoid"] = a["state"] + a["county"] + a["county subdivision"]
    r = lambda n, d: a[n] / a[d]
    o = pd.DataFrame({"geoid": a["geoid"], "county_fips": a["county"], "pop": a["B01003_001E"],
        "median_age": a["B01002_001E"], "median_hh_income": a["B19013_001E"],
        "pct_ba_plus": a[[f"B15003_0{i}E" for i in (22, 23, 24, 25)]].sum(axis=1, min_count=4) / a["B15003_001E"],
        "pct_white_nh": r("B03002_003E", "B03002_001E"), "pct_owner": r("B25003_002E", "B25003_001E"),
        "pct_seasonal_housing": r("B25004_006E", "B25001_001E"), "pct_poverty": r("B17001_002E", "B17001_001E"),
        "pct_wfh": r("B08301_021E", "B08301_001E"),
        "pct_65plus": a[B01001].sum(axis=1, min_count=len(B01001)) / a["B01001_001E"],
        "pct_born_in_vt": r("B05002_003E", "B05002_001E"), "per_capita_income": a["B19301_001E"], "median_earnings": a["B20002_001E"], "pct_one_person_hh": r("B11001_008E", "B11001_001E"), "acs_vintage": a["vintage"]})
    g = gaz.rename(columns={"GEOID": "geoid", "ALAND_SQMI": "land_sqmi", "INTPTLAT": "lat", "INTPTLONG": "lon"})
    m = o.merge(g[["geoid", "town", "land_sqmi", "lat", "lon"]], on="geoid", how="outer")
    m["density"] = m["pop"] / m["land_sqmi"]
    m["county"] = m["geoid"].str[2:5].map(COUNTIES)
    m = m.sort_values("town")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    m.to_csv(OUT, index=False)
    print(len(m), "rows ->", OUT)


if __name__ == "__main__":
    main()
