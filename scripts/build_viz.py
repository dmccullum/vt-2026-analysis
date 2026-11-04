#!/usr/bin/env python3
"""Bundle processed results into docs/data.js for the report page.

    uv run python scripts/build_viz.py
"""
import json, pathlib, re
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"
OUT = ROOT / "docs/data.js"


def r(x, n=4):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return None
    return round(float(x), n)


def title(s):
    t = s.title().replace("'S", "'s")
    t = re.sub(r"^Saint ", "St. ", t)
    return {"Essex Town": "Essex"}.get(t, t)


def wavg(g, col, w="gov_total"):
    m = g[col].notna() & g[w].notna()
    return np.average(g.loc[m, col], weights=g.loc[m, w]) if m.any() else np.nan


def main():
    S = json.loads((P / "statewide_summary.json").read_text())
    t = pd.read_csv(P / "towns_classgeo.csv")
    tm = pd.read_csv(P / "towns_model.csv")[["town", "resid_vs24", "resid_full", "l26"]]
    tm["res_pts"] = 1 / (1 + np.exp(-tm.l26)) - 1 / (1 + np.exp(-(tm.l26 - tm.resid_vs24)))  # actual minus expected share
    t = t.merge(tm, on="town", how="left")
    allt = pd.read_csv(P / "towns.csv")

    # ---------- offices 2024 vs 2026
    offices = []
    res = {y: pd.read_csv(P / f"{y}_results.csv") for y in (2024, 2026)}
    for off, short in [("GOVERNOR", "Governor"), ("LIEUTENANT GOVERNOR", "Lt. Governor"), ("ATTORNEY GENERAL", "Attorney General"),
                       ("AUDITOR OF ACCOUNTS", "Auditor"), ("STATE TREASURER", "Treasurer"), ("SECRETARY OF STATE", "Secretary of State"),
                       ("REPRESENTATIVE TO CONGRESS", "U.S. House")]:
        row = {"office": short}
        for y in (2024, 2026):
            g = res[y][(res[y].office == off) & (res[y].town != "District Wide") & (res[y].party != "WRITE-IN")]
            tot = g.votes.sum()
            byc = g.groupby(["candidate", "party"]).votes.sum().sort_values(ascending=False)
            R = g[g.party.str.upper().str.startswith("REP")].votes.sum()
            L = g[g.party.str.upper().str.match(r"^(DEM|PROG)")].votes.sum()
            row[str(y)] = {"R": r(R / tot), "L": r(L / tot),
                           "cands": [{"name": a.title(), "party": b, "pct": r(v / tot)} for (a, b), v in byc.head(3).items()]}
        offices.append(row)

    # ---------- towns for map + scatter
    towns = []
    for _, x in t.iterrows():
        towns.append({"n": title(x.town), "c": (x.county or "").title() if isinstance(x.county, str) else None,
                      "v": int(x.gov_total), "s26": r(x.gov_R2), "s24": r(x.gov_R2_24), "s22": r(x.gov_R2_22),
                      "e26": r(x.env_R2), "e24": r(x.env_R2_24), "x26": r(x.crossover), "x24": r(x.crossover_24),
                      "res": r(x.res_pts), "ba": r(x.pct_ba_plus), "inc": r(x.per_capita_income, 0),
                      "den": r(x.density, 1), "age": r(x.median_age, 1), "vt": r(x.pct_born_in_vt), "wfh": r(x.pct_wfh),
                      "seas": r(x.pct_seasonal_housing), "to": r(x.turnout), "tier": x.tier[2:] if isinstance(x.tier, str) else None})
    excluded = sorted(set(allt.town) - set(t.town))

    # ---------- class / geography bins
    cg = pd.read_csv(P / "class_geo_summary.csv")
    bins = {}
    for grp, g in cg.groupby("group"):
        bins[grp] = [{k: (r(v) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, (np.integer,)) else v))
                      for k, v in row.items() if k != "group"} for row in g.to_dict("records")]

    # ---------- legislature
    def leg(level):
        c = pd.read_csv(P / f"{level}_candidates.csv")
        clean = c[(c.clean == True) & c.war.notna()]
        keep = ["district", "candidate", "party", "side", "vote_for", "incumbent", "share", "expected", "war", "won", "incomplete", "env_side"]
        rows = lambda d: [{k: (r(v) if isinstance(v, float) else (bool(v) if isinstance(v, (bool, np.bool_)) else v)) for k, v in row.items()}
                          for row in d[keep].to_dict("records")]
        for col in ("candidate", "district"):
            clean = clean.assign(**{col: clean[col].str.title().str.replace("_$", "", regex=True)})
        lost = c[c.incumbent & ~c.won]
        def margin(g):
            g = g.sort_values("votes", ascending=False); v = int(g.vote_for.iloc[0])
            if len(g) <= v:
                return None
            return {"district": g.district.iloc[0].replace("_", "").title(), "margin": r((g.votes.iloc[v - 1] - g.votes.iloc[v]) / g.dist_total.iloc[0]),
                    "votes": int(g.votes.iloc[v - 1] - g.votes.iloc[v]), "winner": g.candidate.iloc[v - 1].title(), "wparty": g.party.iloc[v - 1],
                    "loser": g.candidate.iloc[v].title(), "lparty": g.party.iloc[v], "incomplete": bool(g.incomplete.iloc[0])}
        cl = [m for m in (margin(g) for _, g in c[c.side != "W"].groupby("district")) if m]
        cl = sorted(cl, key=lambda m: m["margin"])[:10]
        seats = c[c.won].groupby("side").size().to_dict()
        seats["P"] = int(c[c.won & c.party.str.startswith("PROG")].shape[0])
        return {"all": rows(clean), "lost": [{"district": a.replace("_", "").title(), "candidate": b.title(), "party": p, "share": r(s),
                                              "seats": int(vf), "place": int(rk)}
                                             for a, b, p, s, vf, rk in lost[["district", "candidate", "party", "share", "vote_for", "rank"]].values],
                "closest": cl, "seats26": {k: int(v) for k, v in seats.items()}, "model": S[level]}

    r24 = pd.read_csv(P / "2024_results.csv")
    side = lambda p: "L" if re.match(r"^(DEM|PROG)", str(p).upper()) else "R" if str(p).upper().startswith("REP") else "I"
    w24 = r24[r24.winner == 1].drop_duplicates(["level", "district", "candidate"])
    seats24 = {lvl: w24[w24.level == lvl].party.map(side).value_counts().to_dict() for lvl in ("house", "senate")}

    hd = pd.read_csv(P / "house_districts.csv")
    hd["scott_won"] = hd.gov_R2 > 0.5
    split = {"scott_districts": int(hd.scott_won.sum()), "districts": len(hd),
             "scott_districts_24": int((hd.gov_R2_24 > 0.5).sum()),
             "scott_no_R": int((hd.scott_won & (hd.get("seats26_R", 0) == 0)).sum()),
             "L_seats_in_scott": int(hd[hd.scott_won].get("seats26_L", 0).sum()),
             "R_seats_in_scott": int(hd[hd.scott_won].get("seats26_R", 0).sum())}
    hdist = [{"d": x.rep_district.title(), "gov": r(x.gov_R2), "gov24": r(x.gov_R2_24), "env": r(x.env_R2),
              "L": int(x.get("seats26_L", 0)), "R": int(x.get("seats26_R", 0)), "I": int(x.get("seats26_I", 0)) if "seats26_I" in hd else 0,
              "L24": int(x.get("seats24_L", 0)), "R24": int(x.get("seats24_R", 0))} for _, x in hd.iterrows()]

    hist = None
    hp = ROOT / "data/raw/legislature_history.csv"
    if hp.exists():
        h = pd.read_csv(hp)
        hist = [{k: (None if pd.isna(v) else (int(v) if isinstance(v, (int, np.integer)) or (isinstance(v, float) and float(v).is_integer() and k != "gov_R_pct" and k != "gov_D_pct") else v))
                 for k, v in row.items() if k not in ("source_urls",)} for row in h.to_dict("records")]

    tot = allt[allt.gov_R.notna()]
    meta = {"sos_updated": "11/04/2026 08:21 AM", "towns_reporting": "244 of 247",
            "unreported": ["Royalton", "Stannard", "Washington"], "excluded_gov": [title(x) for x in excluded],
            "ballots26": int(pd.read_csv(P / "2026_turnout.csv").ballots.sum()),
            "ballots24": int(pd.read_csv(P / "2024_turnout.csv").ballots.sum()),
            "reg26": int(pd.read_csv(P / "2026_turnout.csv").registered.sum()),
            "govtot22": int(allt.gov_total_22.sum())}
    data = {"meta": meta, "statewide": {k: r(v) for k, v in S["statewide"].items()}, "toplines": S["toplines"], "offices": offices,
            "towns": towns, "bins": bins, "house": leg("house"), "senate": leg("senate"), "seats24": seats24, "split": split,
            "hdist": hdist, "history": hist,
            "controls": json.loads((P / "controls.json").read_text()) if (P / "controls.json").exists() else None,
            "eduinc": json.loads((P / "edu_income.json").read_text()) if (P / "edu_income.json").exists() else None,
            "schools": json.loads((P / "schools.json").read_text()) if (P / "schools.json").exists() else None,
            "taxes": json.loads((P / "taxes.json").read_text()) if (P / "taxes.json").exists() else None}
    OUT.parent.mkdir(exist_ok=True)
    js = json.dumps(data, separators=(",", ":"), default=lambda o: None)
    js = re.sub(r"\b(Ii|Iii|Iv)\b", lambda m: m.group(0).upper(), js)  # Roman numerals after .title()
    OUT.write_text("// Generated by scripts/build_viz.py; do not edit\nwindow.VT26=" + js + ";\n")
    print(f"{OUT} {OUT.stat().st_size/1024:.0f} KB; towns {len(towns)}; history {'yes' if hist else 'no'}")


if __name__ == "__main__":
    main()
