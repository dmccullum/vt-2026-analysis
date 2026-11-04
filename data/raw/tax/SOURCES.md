# Vermont education property tax rates by town, FY2025–FY2027

Source: Vermont Department of Taxes, Education Property Tax Rates (https://tax.vermont.gov/ed-rates), read 2026-11-04:
- FY2025: https://tax.vermont.gov/sites/tax/files/documents/FY25EdTaxRates_102424.xlsx
- FY2026: https://tax.vermont.gov/sites/tax/files/documents/FY26EdTaxRates_081825.xlsx
- FY2027: https://tax.vermont.gov/sites/tax/files/documents/FY27EdTaxRates_072926.xlsx

The XLSX files were opened in a browser (scripted downloads return HTTP 403) and the town rows were extracted to `ed_tax_rates_fy25_fy27.csv`:
- `dr` = District Rate (equalized homestead rate before the common level of appraisal; reflects education spending per pupil, comparable across towns)
- `hr` = Homestead Rate actually billed (dr adjusted by the town's CLA, so it jumps when a town reappraises)
- `cla` = Common Level of Appraisal

Rates are per $100 of assessed value. FY2026 bills went out in summer/fall 2025; FY2027 bills in summer/fall 2026, before the election.
Notes: Barre City and Barre Town show 0 for FY2027 (budget data missing, "B" status in the source). Rows such as "Orleans ID", "Shaftsbury ID", "North Bennington", and "Wells River" are incorporated school districts within towns and are not joined to election towns.
