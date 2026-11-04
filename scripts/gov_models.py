#!/usr/bin/env python3
"""Town-level governor models: Scott 2026 vs 2024 lean, downballot partisan lean, demographics. Writes towns_model.csv."""
import pandas as pd, numpy as np, statsmodels.formula.api as smf
t=pd.read_csv('data/processed/towns.csv')
lg=lambda p: np.log(p.clip(.01,.99)/(1-p.clip(.01,.99)))
t['log_density']=np.log10(t.density.clip(lower=1))
t['l26'],t['l24'],t['e26'],t['e24']=lg(t.gov_R2),lg(t.gov_R2_24),lg(t.env_R2),lg(t.env_R2_24)
t['inc10k']=t.per_capita_income/1e4
d=t.dropna(subset=['l26','l24','pct_ba_plus','per_capita_income','pct_born_in_vt','turnout']).copy()
w=np.sqrt(d.gov_total)
Z=['log_density','pct_ba_plus','inc10k','median_age','pct_seasonal_housing','pct_born_in_vt','pct_wfh','turnout']
for c in Z: d[c+'_z']=(d[c]-np.average(d[c],weights=d.gov_total))/d[c].std()
zs=' + '.join(c+'_z' for c in Z)
for name,f in [('M0 l24 only','l26 ~ l24'),('M1 l24+demos','l26 ~ l24 + '+zs),('M2 env26 only','l26 ~ e26'),('M3 env26+demos','l26 ~ e26 + '+zs),('M4 env26+l24+demos','l26 ~ e26 + l24 + '+zs)]:
    m=smf.wls(f,d,weights=w).fit(); print(f'\n{name}: R2={m.rsquared:.3f} n={int(m.nobs)}')
    if 'demos' in name: print(pd.DataFrame({'b':m.params.round(3),'t':m.tvalues.round(1)}).to_string())
    else: print(m.params.round(3).to_dict())
d['resid_vs24']=smf.wls('l26 ~ l24',d,weights=w).fit().resid
d['resid_full']=smf.wls('l26 ~ e26 + l24 + '+zs,d,weights=w).fit().resid
d.to_csv('data/processed/towns_model.csv',index=False)
cols=['town','county','gov_R2','gov_R2_24','scott_swing','crossover','crossover_24','pct_ba_plus','density','pct_born_in_vt','gov_total']
big=d[d.gov_total>=400]
print('\nScott held up best vs 2024 lean (>=400 votes):'); print(big.sort_values('resid_vs24',ascending=False)[cols+['resid_vs24']].head(12).round(3).to_string())
print('\nWorst:'); print(big.sort_values('resid_vs24')[cols+['resid_vs24']].head(12).round(3).to_string())
g=t.groupby('county')
c=g[['gov_R','gov_L','env_R','env_L','gov_total']].sum()
c['s24']=g.apply(lambda x: np.average(x.gov_R2_24,weights=x.gov_total))
c['scott26']=c.gov_R/(c.gov_R+c.gov_L); c['env26']=c.env_R/(c.env_R+c.env_L); c['swing']=c.scott26-c.s24; c['cross']=c.scott26-c.env26
print(c[['scott26','s24','swing','env26','cross']].sort_values('swing').round(3).to_string())
