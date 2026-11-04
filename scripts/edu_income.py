#!/usr/bin/env python3
"""Education relative to income: how far a town's college share sits above or below what its income predicts.

Writes data/processed/edu_income.json (used by build_viz.py).
"""
import json, pathlib
import numpy as np, pandas as pd
import statsmodels.formula.api as smf

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"
t = pd.read_csv(P / "towns_classgeo.csv")
t = t[t.gov_R2.notna() & t.pct_ba_plus.notna() & t.per_capita_income.notna() & (t.density > 0)].copy()
t["janoo"] = 1 - t.gov_R2
t["swing"] = t.gov_R2_24 - t.gov_R2
t["vs_ticket"] = -t.crossover
t["loginc"] = np.log(t.per_capita_income)
w = t.gov_total

# Expected college share given income (vote-weighted fit); gap = actual - expected
fit = smf.wls("pct_ba_plus ~ loginc", t, weights=w).fit()
t["ba_expected"] = fit.predict(t)
t["ba_gap"] = t.pct_ba_plus - t.ba_expected

o = t.ba_gap.sort_values().index
cw = w[o].cumsum() / w.sum()
t["gap_q"] = pd.Series(np.ceil(cw * 5).clip(1, 5).astype(int), index=o).reindex(t.index)

def summ(g):
    v = g.gov_total; a = lambda c: float(np.average(g[c], weights=v))
    return {"towns": int(len(g)), "votes": int(v.sum()), "janoo": a("janoo"), "swing": a("swing"), "vs_ticket": a("vs_ticket"),
            "ba": a("pct_ba_plus"), "inc": a("per_capita_income"), "gap": a("ba_gap"), "age": a("median_age"), "owner": a("pct_owner"),
            "examples": g.sort_values("gov_total", ascending=False).town.head(4).str.title().tolist()}
bins = [summ(g) for _, g in t.groupby("gap_q")]

models = {}
for y in ("janoo", "swing", "vs_ticket"):
    m = smf.wls(f"{y} ~ I(pct_ba_plus*10) + I(per_capita_income/1e4) + np.log10(density) + I(median_age/10) + I(pct_seasonal_housing*10)", t, weights=w).fit(cov_type="HC1")
    m2 = smf.wls(f"{y} ~ I(ba_gap*10)", t, weights=w).fit(cov_type="HC1")
    models[y] = {"ba10": float(m.params.iloc[1]), "inc10": float(m.params.iloc[2]),
                 "gap10": float(m2.params.iloc[1]), "gap10_lo": float(m2.conf_int().iloc[1, 0]), "gap10_hi": float(m2.conf_int().iloc[1, 1]), "gap_r2": float(m2.rsquared)}

out = {"fit": {"a": float(fit.params.Intercept), "b": float(fit.params.loginc)}, "bins": bins, "models": models,
       "towns": {r.town: round(float(r.ba_gap), 4) for r in t.itertuples()}}
(P / "edu_income.json").write_text(json.dumps(out, indent=1))
print("expected BA = %.3f + %.3f*ln(income)" % (fit.params.Intercept, fit.params.loginc))
for i, b in enumerate(bins, 1):
    print(i, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in b.items()})
print(json.dumps(models, indent=1))
