#!/usr/bin/env python3
"""School consolidation / closure exposure vs the governor vote.

Exposure measures (data/raw/schools/school_risk_by_town.csv, see its SOURCES.md):
  small_school  town hosts a public school under 100 students (2024-25)
  closure       a school closure/merger approved or enacted 2025-26 (hand-coded, 10 towns)
  contested     closure proposed but not enacted (Calais, Worcester, Starksboro, Danville)
  no_school     town has no public school (tuitions students out)
  adm_change    % change in resident students FY20-FY24

Outcomes: Scott's drop since 2024 ("swing"), Scott's lead over the rest of the Republican ticket
(2026 and its change since 2024), and the town residual vs the statewide trend.
Writes data/processed/schools.json.
"""
import json, pathlib
import numpy as np, pandas as pd
import statsmodels.formula.api as smf

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"
t = pd.read_csv(P / "towns_classgeo.csv")
s = pd.read_csv(ROOT / "data/raw/schools/school_risk_by_town.csv")
m = pd.read_csv(P / "towns_model.csv")[["town", "resid_vs24", "l26"]]
t = t.merge(s, on="town", how="left").merge(m, on="town", how="left")
t = t[t.gov_R2.notna() & t.pct_ba_plus.notna() & t.per_capita_income.notna() & (t.density > 0)].copy()

t["swing"] = t.gov_R2_24 - t.gov_R2                    # Scott's drop (positive = moved to Janoo)
t["cross26"] = t.crossover                              # Scott minus Republican ticket, 2026
t["cross_drop"] = t.crossover_24 - t.crossover          # how much of that lead he lost
t["res_pts"] = 1 / (1 + np.exp(-t.l26)) - 1 / (1 + np.exp(-(t.l26 - t.resid_vs24)))
t["small_school"] = (t.n_schools_below_100.fillna(0) > 0).astype(int)
t["closure"] = t.closure_or_merger_flag.fillna(0).astype(int)
t["contested"] = t.closure_proposed_not_enacted_flag.fillna(0).astype(int)
t["any_closure"] = ((t.closure + t.contested) > 0).astype(int)
t["no_school"] = (t.has_school.fillna(0) == 0).astype(int)
t["adm_change"] = t.resident_adm_pct_change_fy20_24 / 100
t["status"] = np.select([t.any_closure == 1, t.small_school == 1, t.no_school == 1], ["Closure voted or proposed", "Has a school under 100 students", "No public school in town"], "Only schools of 100+ students")
t["den3"] = pd.cut(t.density, [0, 50, 200, 1e9], labels=["Rural", "Small town", "Suburban/urban"]).astype(str)
w = t.gov_total

def summ(g):
    v = g.gov_total; a = lambda c: float(np.average(g[c], weights=v))
    return {"towns": int(len(g)), "votes": int(v.sum()), "swing": a("swing"), "cross26": a("cross26"), "cross_drop": a("cross_drop"),
            "res": a("res_pts"), "scott24": a("gov_R2_24"), "scott26": a("gov_R2"), "ba": a("pct_ba_plus"), "den": float(g["pop"].sum() / g.land_sqmi.sum()),
            "examples": g.sort_values("gov_total", ascending=False).town.str.title().head(5).tolist()}

# Which school is affected (school_names lists every school in town); AOE lists two as grade reconfigurations
SCHOOL_LABEL = {"ESSEX JUNCTION CITY": "Summit Street School (now pre-K only)", "GREENSBORO": "Lakeview Union School (now pre-K only)"}
order = ["Closure voted or proposed", "Has a school under 100 students", "No public school in town", "Only schools of 100+ students"]
status = {k: summ(t[t.status == k]) for k in order}
by_tier = {f"{d}|{k}": summ(g) for (d, k), g in t.groupby(["den3", "status"]) if len(g) >= 3}

ctrl = "gov_R2_24 + I(pct_ba_plus*10) + I(per_capita_income/1e4) + np.log10(density) + I(median_age/10) + I(pct_seasonal_housing*10)"
models = {}
for y in ("swing", "cross_drop", "res_pts"):
    models[y] = {}
    for x in ("small_school", "closure", "any_closure", "no_school", "I(adm_change*10)"):
        for label, rhs in (("raw", x), ("controlled", f"{x} + {ctrl}")):
            d = t.dropna(subset=["adm_change"]) if "adm" in x else t
            f = smf.wls(f"{y} ~ {rhs}", d, weights=d.gov_total).fit(cov_type="HC1")
            name = f.params.index[1]
            models[y][f"{x}|{label}"] = {"b": float(f.params[name]), "lo": float(f.conf_int().loc[name, 0]), "hi": float(f.conf_int().loc[name, 1]), "p": float(f.pvalues[name]), "n": int(f.nobs)}

closure_towns = t[t.any_closure == 1].sort_values("gov_total", ascending=False)[["town", "closure", "contested", "gov_R2_24", "gov_R2", "swing", "res_pts", "cross26", "gov_total", "school_names"]]
out = {"status": status, "order": order, "by_tier": by_tier, "models": models,
       "closure_towns": [{"town": r.town.title(), "enacted": bool(r.closure), "s24": float(r.gov_R2_24), "s26": float(r.gov_R2), "swing": float(r.swing),
                          "res": float(r.res_pts), "votes": int(r.gov_total), "school": SCHOOL_LABEL.get(r.town, r.school_names if isinstance(r.school_names, str) else "")} for r in closure_towns.itertuples()],
       "n_small": int(t.small_school.sum())}
(P / "schools.json").write_text(json.dumps(out, indent=1))

pd.set_option("display.width", 200)
print(pd.DataFrame(status).T.drop(columns="examples").round(3).to_string())
print(pd.DataFrame(by_tier).T.drop(columns="examples")[["towns", "swing", "res", "cross_drop"]].round(3).to_string())
for y, ms in models.items():
    print(f"\n== {y} (points)")
    for k, v in ms.items():
        print(f"  {k:32s} {100*v['b']:+.2f}  [{100*v['lo']:+.2f}, {100*v['hi']:+.2f}]  p={v['p']:.3f} n={v['n']}")
print(closure_towns.round(3).to_string(index=False))
