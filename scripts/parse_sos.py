#!/usr/bin/env python3
"""Flatten Vermont SOS results JSON into tidy CSVs.

    python3 scripts/parse_sos.py data/raw/sos2026 data/processed/2026

Writes <out>_results.csv (one row per town x district-row x office x candidate)
and <out>_turnout.csv (registered voters / ballots per town).
"""
import csv, json, pathlib, sys

FILES = {"federal": "federal", "statewide": "statewide", "senate": "senate", "house": "house"}


def rows(src, level):
    s = json.loads((src / f"{level}.json").read_text())
    for blk in s["d"]:
        for o in blk["o"]:
            office = o["on"].strip()
            vote_for = o.get("vf") or 1
            for c in o.get("cs", []):
                tn = (c.get("tn") or "").strip()
                if not tn or "STATE WIDE" in tn.upper():
                    continue
                dist = c.get("distCode") or ""
                if level == "house":
                    district = c.get("repd")
                elif level == "senate":
                    district = c.get("send")
                else:
                    district = "STATEWIDE"
                base = dict(level=level, office=office, district=(district or "").strip(), dist_code=dist,
                            vote_for=c.get("vf") or vote_for, town=tn, rep_district=(c.get("repd") or "").strip(),
                            sen_district=(c.get("send") or "").strip(), ballots=c.get("sc"), blanks=c.get("bv"),
                            spoiled=c.get("sv"))
                for x in c.get("rc") or []:
                    yield dict(base, candidate=(x.get("cn") or "WRITE-IN").strip(), party=(x.get("pn") or "").strip(), votes=int(x.get("vc") or 0),
                               write_in=int(bool(x.get("isWriteIn"))), winner=int(bool(x.get("isWinner"))))
                for x in c.get("wc") or []:
                    yield dict(base, candidate=(x.get("cn") or "WRITE-IN").strip(), party="WRITE-IN", votes=int(x.get("vc") or 0),
                               write_in=1, winner=0)


def main():
    src, out = pathlib.Path(sys.argv[1]), sys.argv[2]
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    allrows = [r for lvl in FILES for r in rows(src, lvl) if (src / f"{lvl}.json").exists()]
    with open(f"{out}_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(allrows[0].keys()))
        w.writeheader(); w.writerows(allrows)
    t = src / "turnOut.json"
    if t.exists():
        d = json.loads(t.read_text())["d"]
        with open(f"{out}_turnout.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["town", "registered", "ballots", "absentee", "districts", "districts_reported"])
            for x in d:
                w.writerow([x["tn"].strip(), x.get("tvr"), x.get("tvc"), x.get("tabs"), x.get("tdis"), x.get("tdisr")])
    print(f"{len(allrows)} result rows -> {out}_results.csv")


if __name__ == "__main__":
    main()
