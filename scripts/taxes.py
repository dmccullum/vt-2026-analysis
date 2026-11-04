#!/usr/bin/env python3
"""Education property tax changes by town vs the governor vote.

Uses the equalized District Rate (driven by education spending per pupil, comparable across towns)
from data/raw/tax/ed_tax_rates_fy25_fy27.csv. The billed homestead rate also moves with town
reappraisals, so it is reported but not used as the main measure.
Writes data/processed/taxes.json.
"""
import json, pathlib, re
import numpy as np, pandas as pd
import statsmodels.formula.api as smf

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"
tax = pd.read_csv(ROOT / "data/raw/tax/ed_tax_rates_fy25_fy27.csv")
NAME = {"ESSEX JUNCTION": "ESSEX JUNCTION CITY", "ST. ALBANS CITY": "SAINT ALBANS CITY", "ST. ALBANS TOWN": "SAINT ALBANS TOWN",
        "ST. GEORGE": "SAINT GEORGE", "ST. JOHNSBURY": "SAINT JOHNSBURY"}
tax["town"] = tax.town.str.upper().map(lambda n: NAME.get(n, n))
for a, b in (("25", "26"), ("26", "27"), ("25", "27")):
    ok = (tax[f"dr{a}"] > 0) & (tax[f"dr{b}"] > 0)
    tax[f"dr_chg_{a}_{b}"] = np.where(ok, tax[f"dr{b}"] / tax[f"dr{a}"] - 1, np.nan)
    okh = (tax[f"hr{a}"] > 0) & (tax[f"hr{b}"] > 0)
    tax[f"hr_chg_{a}_{b}"] = np.where(okh, tax[f"hr{b}"] / tax[f"hr{a}"] - 1, np.nan)
tax["reappraised_27"] = (tax.cla27.between(0.995, 1.005) & ~tax.cla26.between(0.995, 1.005)) | ((tax.cla27 / tax.cla26) > 1.25)

t = pd.read_csv(P / "towns_classgeo.csv").merge(tax, on="town", how="left")
t = t[t.gov_R2.notna() & t.pct_ba_plus.notna() & t.per_capita_income.notna() & (t.density > 0)].copy()
t["swing"] = t.gov_R2_24 - t.gov_R2
t["cross_drop"] = t.crossover_24 - t.crossover
unmatched = sorted(set(pd.read_csv(P / "towns_classgeo.csv").town) - set(tax.town))
ctrl = "gov_R2_24 + I(pct_ba_plus*10) + I(per_capita_income/1e4) + np.log10(density) + I(median_age/10) + I(pct_seasonal_housing*10)"

models = {}
for y in ("swing", "cross_drop"):
    models[y] = {}
    for x, lab in (("dr_chg_25_26", "District rate change FY25→FY26"), ("dr_chg_26_27", "District rate change FY26→FY27"),
                   ("dr_chg_25_27", "District rate change FY25→FY27"), ("dr27", "District rate level FY27")):
        d = t.dropna(subset=[x])
        for kind, rhs in (("raw", x), ("controlled", f"{x} + {ctrl}")):
            scale = 10  # per +10% change, or per +0.10 rate
            f = smf.wls(f"{y} ~ I({x}*{scale}) " + ("" if kind == "raw" else f"+ {ctrl}"), d, weights=d.gov_total).fit(cov_type="HC1")
            nm = f.params.index[1]
            models[y][f"{x}|{kind}"] = {"label": lab, "b": float(f.params[nm]), "lo": float(f.conf_int().loc[nm, 0]),
                                        "hi": float(f.conf_int().loc[nm, 1]), "p": float(f.pvalues[nm]), "n": int(f.nobs)}

def wq(col, k=3):
    d = t.dropna(subset=[col]); o = d[col].sort_values().index
    cw = d.gov_total[o].cumsum() / d.gov_total.sum()
    return pd.Series(np.ceil(cw * k).clip(1, k).astype(int), index=o)
t["q"] = wq("dr_chg_25_27")
groups = []
for q, g in t.dropna(subset=["q"]).groupby("q"):
    v = g.gov_total; a = lambda c: float(np.average(g[c].dropna(), weights=v[g[c].notna()]))
    groups.append({"q": int(q), "towns": int(len(g)), "dr_chg": a("dr_chg_25_27"), "swing": a("swing"), "cross_drop": a("cross_drop"),
                   "s24": a("gov_R2_24"), "s26": a("gov_R2"), "ba": a("pct_ba_plus")})
state = {f"dr_chg_{a}_{b}": float(np.average(t[f"dr_chg_{a}_{b}"].dropna(), weights=t.gov_total[t[f"dr_chg_{a}_{b}"].notna()]))
         for a, b in (("25", "26"), ("26", "27"), ("25", "27"))}
out = {"models": models, "groups": groups, "state": state, "unmatched": unmatched, "n": int(t.dr_chg_25_27.notna().sum())}
(P / "taxes.json").write_text(json.dumps(out, indent=1))
print("unmatched:", unmatched)
print("vote-weighted avg district-rate change:", {k: round(100 * v, 1) for k, v in state.items()})
print(pd.DataFrame(groups).round(3).to_string(index=False))
for y, ms in models.items():
    print(f"\n== {y} (points per +10% rate change, or per +0.10 rate level)")
    for k, v in ms.items():
        print(f"  {k:28s} {100*v['b']:+.2f} [{100*v['lo']:+.2f}, {100*v['hi']:+.2f}] p={v['p']:.3f} n={v['n']}")
