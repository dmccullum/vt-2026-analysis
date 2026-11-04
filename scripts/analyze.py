#!/usr/bin/env python3
"""Core post-election analysis: downballot partisan lean, Scott vs. the Republican ticket, legislative results vs. expectations.

    uv run python scripts/analyze.py

Inputs:  data/processed/{2024,2026}_results.csv, data/processed/{2024,2026}_turnout.csv,
         data/processed/town_demographics.csv (optional), data/raw/needle_baseline.json
Outputs: data/processed/pieces.csv, towns.csv, house_candidates.csv, senate_candidates.csv,
         house_districts.csv, statewide_summary.json
"""
import json, pathlib, re
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"

UNREPORTED = {"ROYALTON", "STANNARD", "WASHINGTON"}  # no 2026 returns as of the SOS 11/04 08:21 AM file
# Unofficial 2026 governor return with Scott at 0 and 129 "other write-in": excluded as a probable reporting error
SUSPECT_GOV = {"MARLBORO"}

DOWNBALLOT = ["LIEUTENANT GOVERNOR", "STATE TREASURER", "SECRETARY OF STATE", "AUDITOR OF ACCOUNTS",
              "ATTORNEY GENERAL", "REPRESENTATIVE TO CONGRESS"]


def side(party):
    """Lead party -> 'L' (Dem/Prog), 'R', 'I' (independent/minor), 'W' (write-in)."""
    p = (party or "").upper()
    if p == "WRITE-IN" or not p:
        return "W"
    lead = re.split(r"[/ ]", p)[0]
    if lead.startswith("DEM") or lead.startswith("PROG"):
        return "L"
    if lead.startswith("REP"):
        return "R"
    return "I"


def load(year):
    r = pd.read_csv(P / f"{year}_results.csv")
    r = r[~r.town.str.upper().str.contains("DISTRICT WIDE")].copy()
    r["side"] = r.party.map(side)
    r["piece"] = r.town + "|" + r.rep_district
    return r


def piece_table(r, year):
    """One row per town x House-district piece with statewide-race votes by side."""
    sw = r[r.level.isin(["statewide", "federal"])]
    out = sw.groupby(["piece", "town", "rep_district", "sen_district"]).size().reset_index()[["piece", "town", "rep_district", "sen_district"]]
    out = out.set_index("piece")
    gov = sw[sw.office == "GOVERNOR"].pivot_table(index="piece", columns="side", values="votes", aggfunc="sum").fillna(0)
    out["gov_R"], out["gov_L"] = gov.get("R", 0), gov.get("L", 0)
    out["gov_total"] = gov.sum(axis=1)
    if year == 2026:
        bad = out.town.isin(SUSPECT_GOV)
        out.loc[bad, ["gov_R", "gov_L", "gov_total"]] = np.nan
    db = sw[sw.office.isin(DOWNBALLOT)].pivot_table(index="piece", columns="side", values="votes", aggfunc="sum").fillna(0)
    out["env_R"], out["env_L"] = db.get("R", 0), db.get("L", 0)
    for off, tag in [("LIEUTENANT GOVERNOR", "lg"), ("REPRESENTATIVE TO CONGRESS", "ush"), ("US PRESIDENT AND VICE PRESIDENT", "pres")]:
        x = sw[sw.office == off].pivot_table(index="piece", columns="side", values="votes", aggfunc="sum").fillna(0)
        if len(x):
            out[f"{tag}_R"], out[f"{tag}_L"] = x.get("R", 0), x.get("L", 0)
    out["year"] = year
    return out.fillna(0).reset_index()


def shares(df):
    df = df.copy()
    df["gov_R2"] = df.gov_R / (df.gov_R + df.gov_L)
    df["env_R2"] = df.env_R / (df.env_R + df.env_L)
    df["crossover"] = df.gov_R2 - df.env_R2  # Scott two-party share minus the downballot Republican share
    if "lg_R" in df:
        df["lg_R2"] = df.lg_R / (df.lg_R + df.lg_L)
    if "pres_R" in df:
        df["pres_R2"] = df.pres_R / (df.pres_R + df.pres_L)
    return df


def agg(pieces, key):
    cols = [c for c in pieces.columns if re.match(r"^(gov|env|lg|ush|pres)_(R|L|total)$", c)]
    return shares(pieces.groupby(key)[cols].sum().reset_index())


def candidates(r, level, pieces26):
    """Per-candidate totals with the district's downballot partisan lean for the candidate's side."""
    leg = r[(r.level == level) & (r.side != "W")]
    dist = pieces26.groupby("rep_district" if level == "house" else "sen_district")[["env_R", "env_L", "gov_R", "gov_L"]].sum()
    dist["env_R2"] = dist.env_R / (dist.env_R + dist.env_L)
    dist["gov_R2"] = dist.gov_R / (dist.gov_R + dist.gov_L)
    lv = r[r.level == level]
    # SOS 'ballots' (sc) counts vote slots = voters x seats; one row per piece
    slots = lv.drop_duplicates(["district", "town", "rep_district"]).groupby("district").apply(
        lambda g: (g.ballots / g.vote_for).sum(), include_groups=False)
    c = leg.groupby(["district", "candidate", "party", "side", "vote_for"]).votes.sum().reset_index()
    c["dist_total"] = c.district.map(slots)  # voters casting a ballot in the district
    c["share"] = c.votes / c.dist_total  # share of voters who voted for this candidate
    td = json.loads((ROOT / "data/raw/sos2026/el2026.json").read_text())["townDistricts"]
    key = "repDistrict" if level == "house" else "senateDistrict"
    c["incomplete"] = c.district.isin({x[key].strip() for x in td if x["townName"] in UNREPORTED})
    c = c.join(dist[["env_R2", "gov_R2"]], on="district")
    c["env_side"] = np.where(c.side == "R", c.env_R2, np.where(c.side == "L", 1 - c.env_R2, np.nan))
    c["vs_env"] = c.share - c.env_side
    c["vs_scott"] = np.where(c.side == "R", c.share - c.gov_R2, np.nan)
    # field structure
    n = c.groupby(["district", "side"]).size().unstack(fill_value=0)
    c["n_L"] = c.district.map(n.get("L", pd.Series(dtype=int))).fillna(0).astype(int)
    c["n_R"] = c.district.map(n.get("R", pd.Series(dtype=int))).fillna(0).astype(int)
    c["n_I"] = c.district.map(n.get("I", pd.Series(dtype=int))).fillna(0).astype(int)
    c["contested"] = (c.n_L > 0) & (c.n_R > 0)
    c["rank"] = c.groupby("district").votes.rank(ascending=False, method="first")
    c["won"] = c["rank"] <= c.vote_for
    return c


def add_incumbency(c, r24, level):
    w = r24[(r24.level == level) & (r24.winner == 1)].candidate.str.upper().unique()
    w_any = r24[(r24.level.isin(["house", "senate"])) & (r24.winner == 1)].candidate.str.upper().unique()
    c["incumbent"] = c.candidate.str.upper().isin(w)
    c["prior_legislator"] = c.candidate.str.upper().isin(w_any)
    return c


def war(c):
    """Share minus expected share for contested major-party candidates.

    One-seat and multi-seat races are modeled separately when each group has at least 25 candidates,
    because in multi-seat races voters can choose several candidates and "second votes" behave differently.
    Otherwise one pooled model with a multi-seat indicator is used.
    """
    import statsmodels.formula.api as smf
    d = c[c.contested & c.side.isin(["L", "R"])].copy()
    d["is_R"] = (d.side == "R").astype(int)
    d["multi"] = (d.vote_for > 1).astype(int)
    d["own_n"] = np.where(d.side == "R", d.n_R, d.n_L)
    d["opp_n"] = np.where(d.side == "R", d.n_L, d.n_R)
    d["own_short"] = (d.own_n < d.vote_for).astype(int)  # party fielded fewer candidates than seats
    d["own_crowded"] = (d.own_n > d.vote_for).astype(int)  # more same-side candidates than seats
    specs = {0: "share ~ env_side + is_R + incumbent + n_I",
             1: "share ~ env_side + is_R + incumbent + own_short + own_crowded + n_I + opp_n"}
    groups = d.groupby("multi")
    parts = {}
    if all(len(g) >= 25 for _, g in groups) and len(groups) == 2:
        for k, g in groups:
            m = smf.wls(specs[k], data=g, weights=np.sqrt(g.dist_total)).fit()
            d.loc[g.index, "expected"] = m.predict(g)
            parts["multi" if k else "single"] = {"n": int(m.nobs), "r2": round(float(m.rsquared), 3),
                                                  "incumbent": round(float(m.params["incumbent[T.True]"]), 4)}
    else:
        m = smf.wls("share ~ env_side + is_R + incumbent + own_short + own_crowded + n_I + multi", data=d,
                    weights=np.sqrt(d.dist_total)).fit()
        d["expected"] = m.predict(d)
        parts["pooled"] = {"n": int(m.nobs), "r2": round(float(m.rsquared), 3), "incumbent": round(float(m.params["incumbent[T.True]"]), 4)}
    d["war"] = d.share - d.expected
    resid, y = d.war, d.share
    summary = {"n": int(len(d)), "r2": round(float(1 - (resid ** 2).sum() / ((y - y.mean()) ** 2).sum()), 3),
               "incumbent": round(float(np.average([p["incumbent"] for p in parts.values()], weights=[p["n"] for p in parts.values()])), 4),
               "parts": parts}
    return d, summary


def main():
    r26, r24 = load(2026), load(2024)
    p26, p24 = shares(piece_table(r26, 2026)), shares(piece_table(r24, 2024))
    p26.to_csv(P / "pieces_2026.csv", index=False); p24.to_csv(P / "pieces_2024.csv", index=False)

    # ---- towns
    t26, t24 = agg(p26, "town"), agg(p24, "town")
    towns = t26.merge(t24, on="town", how="left", suffixes=("", "_24"))
    for y in (2026, 2024):
        t = pd.read_csv(P / f"{y}_turnout.csv")
        t = t[t.registered > 0]
        sfx = "" if y == 2026 else "_24"
        towns = towns.merge(t[["town", "registered", "ballots"]].rename(columns={"registered": "reg" + sfx, "ballots": "ballots" + sfx}), on="town", how="left")
    # 2022 turnout + older governor shares from the needle baseline
    base = pd.DataFrame(json.loads((ROOT / "data/raw/needle_baseline.json").read_text()))
    base["town"] = base.town.str.upper().str.replace(r"^ST\. ", "SAINT ", regex=True)
    base.loc[base.town == "ESSEX", "town"] = "ESSEX TOWN"  # baseline folds Essex Junction into Essex
    for y in ("16", "18", "20", "22"):
        base[f"gov_R2_{y}"] = base[f"r{y}"] / (base[f"r{y}"] + base[f"d{y}"])
        base[f"gov_total_{y}"] = base[f"r{y}"] + base[f"d{y}"] + base[f"o{y}"]
    towns = towns.merge(base[["town", "county"] + [c for c in base.columns if c.startswith("gov_")]], on="town", how="left")
    towns["turnout"] = towns.ballots / towns.reg
    towns["turnout_24"] = towns.ballots_24 / towns.reg_24
    towns["ballots_vs_22"] = towns.gov_total / towns.gov_total_22 - 1
    towns["scott_swing"] = towns.gov_R2 - towns.gov_R2_24
    towns["env_swing"] = towns.env_R2 - towns.env_R2_24
    towns["crossover_change"] = towns.crossover - towns.crossover_24
    demo = P / "town_demographics.csv"
    if demo.exists():
        d = pd.read_csv(demo)
        towns = towns.merge(d.drop(columns=[c for c in ("county",) if c in d.columns]), on="town", how="left")
    towns.to_csv(P / "towns.csv", index=False)

    # ---- legislative
    out = {}
    for level in ("house", "senate"):
        c = add_incumbency(candidates(r26, level, p26), r24, level)
        d, m = war(c)
        d["clean"] = (d.own_crowded == 0) & (d.n_I == 0)  # partisan-lean benchmark applies
        c = c.merge(d[["district", "candidate", "expected", "war", "clean"]], on=["district", "candidate"], how="left")
        c.to_csv(P / f"{level}_candidates.csv", index=False)
        out[level] = m

    # house district summary (2026 vs 2024 partisan lean, Scott, seats)
    hd = agg(p26, "rep_district").merge(agg(p24, "rep_district"), on="rep_district", suffixes=("", "_24"))
    hc = pd.read_csv(P / "house_candidates.csv")
    seats = hc[hc.won].groupby(["district", "side"]).size().unstack(fill_value=0)
    hd = hd.join(seats.add_prefix("seats26_"), on="rep_district")
    w24 = r24[(r24.level == "house") & (r24.winner == 1)].drop_duplicates(["district", "candidate"])
    s24 = w24.groupby(["district", "side"]).size().unstack(fill_value=0)
    hd = hd.join(s24.add_prefix("seats24_"), on="rep_district").fillna(0)
    hd.to_csv(P / "house_districts.csv", index=False)

    # statewide toplines
    sw = r26[r26.level.isin(["statewide", "federal"])]
    tops = {}
    for off, g in sw.groupby("office"):
        t = g.groupby(["candidate", "party"]).votes.sum().sort_values(ascending=False)
        tops[off] = [{"candidate": a, "party": b, "votes": int(v), "pct": round(100 * v / t.sum(), 2)} for (a, b), v in t.head(4).items()]
    out["toplines"] = tops
    tot26, tot24 = p26.sum(numeric_only=True), p24.sum(numeric_only=True)
    out["statewide"] = {
        "scott_R2_26": tot26.gov_R / (tot26.gov_R + tot26.gov_L), "scott_R2_24": tot24.gov_R / (tot24.gov_R + tot24.gov_L),
        "env_R2_26": tot26.env_R / (tot26.env_R + tot26.env_L), "env_R2_24": tot24.env_R / (tot24.env_R + tot24.env_L),
        "pres_R2_24": tot24.pres_R / (tot24.pres_R + tot24.pres_L),
    }
    (P / "statewide_summary.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out["statewide"], indent=1, default=float))
    print({k: out[k] for k in ("house", "senate")})


if __name__ == "__main__":
    main()
