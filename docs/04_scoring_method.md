# Merchant Expansion Opportunity Score

## Why a score?

The team needs a repeatable way to compare markets with different sizes. Absolute volume alone favors large cities; percentage growth alone can favor tiny bases. The score combines growth, scale, and acceptance registration density.

## Main comparison universe

At the latest quarter, require at least 100,000 registered users, 1,000 registered merchants, and 1 million quarterly transactions, plus comparable QoQ and YoY growth. These analyst-selected cutoffs give a material base for national field research; they are not PhonePe business policy.

This leaves 680 of 783 districts. The 103 exclusions remain in `excluded_districts.csv`, with reasons. After scoring, the investigation pool additionally requires positive QoQ and YoY transaction growth and non-declining user and merchant registration bases. This leaves 624 districts.

## Formula

| Component | Weight | Why included |
|---|---:|---|
| YoY transaction growth percentile | 30% | Demand momentum with a same-season baseline |
| Transactions per merchant percentile | 25% | Demand intensity relative to registered acceptance |
| Users per merchant percentile | 25% | Relative acceptance registration gap |
| Registered-user base percentile | 20% | Market scale |

`Score = 100 × (0.30 × growth + 0.25 × intensity + 0.25 × relative_gap + 0.20 × scale)`

Each component uses `PERCENT_RANK()` across the same 680 eligible districts. Ties receive the same percentile. A score of 85 is neither an 85% success probability nor an estimate of revenue. Geography filters retain this national score; they do not silently rerank against a smaller universe.

Weights are judgment calls. Growth receives slightly more weight; intensity and gap share the acceptance signal; scale prevents the exercise from becoming a tiny-market ranking. Users per merchant and transactions per merchant share a denominator, so the following sensitivity test is essential.

## Robustness checks

- **Equal weights:** 25% per factor. Retains 9 of the original 10.
- **Remove transaction intensity:** 40% growth, 35% users per merchant, 25% user scale. Retains 6 of 10 within the same investigation pool.
- **Remove all size cutoffs and recompute percentiles:** Retains 6 of 10. This changes the comparison population as well as eligibility; it is deliberately a broad stress test.

Treat the six districts retained without intensity as stronger field-validation candidates. Keep the other four conditional. The original top ten are geographically concentrated (seven Andhra Pradesh, two Karnataka, one Telangana); do not interpret that concentration as proof of a nationwide optimum or allocate all acquisition budget to it.

The matrix labels “high growth / low relative penetration” only when growth and users-per-merchant percentiles are both at least 75%. A district may rank highly overall without meeting both matrix thresholds. “Established acceptance / slower growth” is a relative monitoring label, not evidence of saturation.
