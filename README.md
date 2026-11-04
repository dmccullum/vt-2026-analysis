# Vermont 2026 election analysis

Results and analysis for every race in Vermont's 2026 general election, compared with 2024 and with town demographics, schools, and education tax rates.

**Report:** https://dmccullum.github.io/vt-2026-analysis/

```bash
./run.sh                                       # rebuild from data/raw
python3 -m http.server 8643 --directory docs   # view at localhost:8643
```

Sources: Vermont Secretary of State, U.S. Census (ACS, Gazetteer), Vermont Agency of Education, NCES, Vermont Department of Taxes. Details in `data/raw/*/SOURCES.md` and the report's method notes.
