# Explain this project in an interview

## A 60-second introduction

“This independent project uses PhonePe Pulse data through Q2 2026 to help a merchant-growth team choose districts for further investigation. I used Python to extract and validate the JSON data, MySQL to calculate quarterly metrics and rankings, and Power BI to make the results explorable. The key challenge was distinguishing transaction demand from merchant acceptance: registrations are not active shops, and district transactions include P2P. I tested alternative score weights before recommending a field-validation shortlist rather than claiming guaranteed business growth.”

Adapt this introduction to the parts you have personally reviewed and can demonstrate.

## Questions you should be able to answer

| Interview question | What to explain |
|---|---|
| Why this business problem? | A sales team has limited field time; the analysis narrows where to investigate first. |
| Why Python and SQL? | Python handles nested JSON and validation; MySQL handles joins, time comparisons and ranking; Power BI handles exploration. |
| What is the grain? | A district within a state in one calendar quarter. Explain why the key needs all three. |
| How did you handle missing merchants? | Kept NULL; did not infer zero. Ratios and totals respect incomplete coverage. |
| Why not use top district JSON? | Top-N files omit most districts and would bias the universe. |
| Why use LAG? | Retrieve the previous row, then check that it really is the previous quarter. |
| Why a same-quarter YoY join? | Directly match period_id − 4; do not assume four rows always mean one year. |
| Why not sum registered users over time? | They are cumulative quarter-end stocks, so that would repeatedly count the same base. |
| Why percentiles? | Factors have different scales and long tails. Percentile ranks are simple to explain, though they lose magnitude differences. |
| Why sensitivity analysis? | Weights are assumptions. The top ten changed when the shared-denominator intensity factor was removed. |
| Does low penetration prove opportunity? | No. It is relative registrations per user, not coverage of all local shops. Field evidence is required. |
| What did you validate independently? | SQL QoQ, YoY, users per merchant, score, contribution totals, row count and key integrity against Pandas. |
| What would you do with internal data? | Replace registered merchants with active eligible merchants, add merchant category, competition, costs, and pilot outcomes. |
| What business impact did this project achieve? | It produced an investigation framework; no real merchant acquisition or revenue impact was measured. |

## Walkthrough order

1. Explain the decision and source limitations.
2. Open a raw JSON record and its cleaned CSV row.
3. Show missing-data and reconciliation checks.
4. Explain one MySQL JOIN, one LAG calculation, and the score CTE.
5. Show the Power BI overview, penetration page, and shortlist.
6. Explain why six candidates have stronger sensitivity support than the other four.
7. Close with the field pilot and the data needed to authorize acquisition spend.

## Practice tasks

- Recalculate West Godavari users per merchant using its source counts.
- Explain why taking the average of district averages is wrong for national average transaction value.
- Change the score weights and explain the resulting rank movement.
- Filter one state in Power BI and explain why national score ranks stay fixed.
- Identify a case where a large transaction market should be monitored before more acquisition.
