# Governor poll crosstab sources (retrieved 2026-11-04, web fetch only)

Files here: `governor_crosstabs_2026.csv` (vote crosstabs), `vermont_public_school_issue_items_2026.csv` (Vermont Public Q12/Q13 school/property-tax items; extra file with a different schema because issue responses do not fit the Scott/Janoo columns).

## 1. Vermont Public / Vermont State University (Braun Research, Rich Clark)
- Field: Sept 10-21, 2026. n=817 all respondents; 732 likely voters (unweighted). MoE +/-3.4 (full sample). Cell, landline, text-to-web.
- Topline all respondents (workbook): Scott 41.5, Janoo 31.9, undecided 19.9. Likely voters: Scott 43.7, Janoo 34.4, other 5.9, not sure 15.9.
- Sources: https://www.vermontpublic.org/local-news/2026-09-28/poll-shows-amanda-janoo-closing-on-phil-scott-governors-race ; results page https://www.vermontpublic.org/local-news/2026-09-28/vermont-general-election-poll-results-2026 ; XLSX https://app.vermontpublic.org/poll/2026/vermontpublic-2026-poll-full-results-likely-voters.xlsx
- The XLSX (64 KB data file, fetched by the web-fetch tool, parsed with plain zip/XML reading; nothing executed) gave exact tables. Banners available: gender, region (4 groups), education (3), age (3), party ID with leaners (3). NOT available: income, 2024 vote, urban/rural/town size, county detail beyond the 4 regions.
- Values are published as proportions; CSV converts to percent rounded to 0.1. Subgroup unweighted n are in the `n` column (small: HS or less n=96 LV).
- The article says "Janoo leads by 6 among bachelor's+" and "3 in Chittenden"; the workbook gives 45.2-37.7 (+7.5) and 42.0-40.4 (+1.6) for likely voters (all-respondent sheet differs again). Article figures are likely from a different weighting/population; use the workbook.
- Lt. Gov. question had a wording error for 363 of 817 respondents (not relevant to governor).

## 2. State Navigate (Oct 23-25, 2026)
- n=1,752 likely voters, MoE +/-2.3. Text-to-web (AllianceForge/SurveyMonkey), L2 voter file, weighted by gender, race, age, education, leaned party, state senate district.
- Topline: Scott 49, Janoo 46, other 2, DK/DR 3 (with leaners).
- Source PDF: https://projects.statenavigate.com/interactives/vt/statewide-poll-october-23-2026/vermont-statewide-poll-october-23-25-2026.pdf
- The PDF's charts are embedded raster images, so only numbers in page text were extracted (text read from the PDF's content streams; the file was saved by the fetch tool and not opened in any viewer). Text numbers captured: Scott keeps 66% of 2024 Scott voters, 30% to Janoo; Scott wins 25% of Democrats; under-30 Janoo 70, Scott 25; Scott approval 58/40; Trump approval 25/74; Legislature approval 40/52. The charts likely contain more breakdowns (by 2024 vote, party, age, Trump approval) but were not read. No education, income, region or school-issue numbers appear in the text. Appendix lists Senate district weights (Chitt. SE 13.3% etc.), not vote shares.

## 3. UNH Survey Center (Green Mountain State Poll #1012, published Nov 1, 2026)
- UNH Survey Center Green Mountain State Poll #1012. Permanent page https://scholars.unh.edu/survey_center_polls/1012 (abstract only: Janoo small lead; top issues affordability/inflation, economy, taxes).
- The PDF (https://scholars.unh.edu/cgi/viewcontent.cgi?article=2011&context=survey_center_polls) returned HTTP 403. No crosstabs, dates or MoE obtained.
- Topline only via WCAX (paraphrased): Janoo 51, Scott 43, LV "just over 1,200"; earlier UNH (Sept 24): Janoo 49, Scott 43.

## 4. WCAX, Nov 2, 2026
- https://www.wcax.com/2026/11/02/new-poll-shows-janoo-ahead-scott-vermont-governors-race/ reports the UNH poll above (not a separate poll). No crosstabs; only says the sample "skews younger" and young voters favor Janoo. Also cites State Navigate 49-46 and Vermont Public 42-32.
