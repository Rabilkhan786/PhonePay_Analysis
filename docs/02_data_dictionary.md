# Data dictionary and aggregation rules

| Field | Meaning / unit | Aggregation rule |
|---|---|---|
| state | Source state/UT name, mechanically standardized | Use with district to identify geography |
| district | Source district name | Never join on district alone |
| district_key | State + separator + district | Unique district identity within this release |
| year / quarter | Calendar year and quarter, Q1 = Jan–Mar | Q2 2026 is Apr–Jun 2026 |
| period_id | year × 4 + quarter − 1 | Numeric sequential quarter key |
| transactions | Number of PhonePe transactions in quarter | Additive across geography and time |
| value_inr | Transaction value in INR | Additive flow; floating-point source precision |
| registered_users | Cumulative registered user base at quarter end | Sum across geography within a quarter, never across quarters |
| registered_merchants | Cumulative merchant registrations at quarter end | Not active shops; never sum across quarters |
| category_raw | P2P, Retail, Utility as actually encoded in JSON | Category volume only; values unavailable in this cut |
| transaction_qoq | Current quarter volume / previous quarter volume − 1 | Null if the immediately preceding quarter is unavailable |
| transaction_yoy | Current volume / same quarter last year − 1 | Handles broad seasonality better than QoQ |
| user_qoq / merchant_qoq | Change in cumulative registration stock / prior stock | Net stock change; not churn or activation |
| average_transaction_value | value_inr / transactions | Ratio of sums, not average of district averages |
| users_per_merchant | Registered users / registered merchants | Higher suggests lower relative acceptance registration density |
| transactions_per_merchant | All transactions / registered merchants | Demand intensity proxy; not merchant throughput |
| value_per_merchant | All transaction value / registered merchants | Includes P2P and utilities; not merchant sales |
| merchants_per_1000_users | 1,000 × merchants / users | Relative indicator, not % of all local shops covered |
| state_contribution | State volume / summed state volume in the quarter | Percent of mapped PhonePe India total |
| district_share_of_state | District volume / its state's volume | Parent-state denominator |
| district_share_of_mapped_india | District volume / summed district volume | Mapped India denominator |
| opportunity_score | Weighted percentile score × 100 | Ordinal investigation priority, not probability or revenue |

## Source paths

- `data/map/transaction/hover/country/india/<year>/<quarter>.json`: state volumes and values.
- `data/map/<transaction|user|merchant>/hover/country/india/state/<state>/<year>/<quarter>.json`: district metrics.
- `data/map/<user|merchant>/hover/country/india/<year>/<quarter>.json`: state registration counts.
- `data/aggregated/transaction/country/india/state/<state>/<year>/<quarter>.json`: state category counts.

Do not use the `top` folder as the full district population: it is a selected top-N extract. Do not join category rows directly to district-quarter totals; that would multiply records. The README calls the consolidated business category “Business”, while actual JSON uses “Retail”; the project preserves the raw label and documents that distinction.
