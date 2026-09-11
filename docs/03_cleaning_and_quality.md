# Cleaning and data-quality summary — read before the findings

**Decision:** Q2 2026 is complete for the four core fields across 36 states/UTs and 783 districts. Historical missingness is retained and must be respected in trends.

- Extracted 1,224 state-quarter and 26,622 district-quarter rows across 34 quarters.
- No duplicate geographic keys in any of the six source metric cuts.
- No observed negative or zero values in the four core fields. Missing values are a separate issue.
- All 783 district keys are represented in all 34 quarters. Representation does not mean every measure is populated.
- No missing periods within a district's represented history.
- District transaction counts and user/merchant registration totals match state totals where comparable.
- Maximum state-quarter transaction-value rounding difference: approximately ₹0.3042, retained rather than artificially adjusted.
- State category transaction counts reconcile exactly to state map counts.

## Missing observations retained as NULL

| table | column | count |
|---|---|---|
| state | registered_merchants | 46 |
| district | transactions | 6 |
| district | value_inr | 6 |
| district | registered_merchants | 1885 |

Historical merchant coverage is incomplete through 2022 Q3; Q2 2026 has no core-field missingness. Missing merchant counts are **not** converted to zero or estimated. Total merchant cards return blank when selected geography has incomplete counts.

## Cleaning choices and reasons

1. Lowercase names, replace hyphens with spaces, collapse whitespace, and remove a trailing “district”. Retain raw names in source lineage. No fuzzy matching or guessed renaming.
2. Use state + district as the geographic key. Same-name districts in different states remain separate.
3. Validate year and quarter from filenames. Keep calendar-quarter definitions explicit.
4. Use nullable integer counts. Preserve INR amounts as source floating-point values; do not claim accounting precision beyond the source.
5. Join transaction, user, and merchant cuts with one-to-one validated outer joins so missing values remain visible.
6. Use IQR fences to flag outliers for interpretation. Do not remove large cities merely because they are outliers.
7. Use exact adjacent-quarter and same-quarter-last-year comparisons. Do not bridge missing quarters with an unrelated earlier record.

## Evidence

Machine-readable checks are in `data/processed/quality_checks.csv`, `geographic_reconciliation.csv`, `category_reconciliation.csv`, and coverage CSVs. `data/analysis/validation.json` contains 10 independent calculation and integrity checks, all passed. Source-file hashes and the release commit are in `data/source_manifest.json`.

The geographic names are the source's restated geography. A stable name/count does not prove unchanged administrative boundaries; validate target boundaries with regional teams before using a district ranking operationally.
