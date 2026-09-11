# PhonePe merchant expansion — investigation recommendation

**Decision date:** 2026 portfolio analysis. **Measurement period:** 2026 Q2. **Audience:** Merchant-growth manager.

## Recommended action

Start field validation with **West Godavari and Sangareddy**, the top two scored districts. Also validate **Dr BR Ambedkar Konaseema, East Godavari, Sri Potti Sriramulu Nellore, and Alluri Sitharama Raju**: these six remain in the top ten when transaction intensity is removed from the score. They are candidates for research, not automatic acquisition spend.

Keep **Tirupati, Eluru, Mandya, and Hassan** on the investigation list, with lower confidence in their relative rank because they depend more on the intensity weighting. No uplift, profit, or merchant-acquisition success has been measured.

## Demand context

Q2 2026 recorded **38.66 billion transactions**, **₹45.50 trillion transaction value**, **711.65 million registered users**, and **50.71 million registered merchants** in the mapped PhonePe ecosystem. Transaction volume grew **6.66% QoQ**. Average transaction value was **₹1,176.70**.

| State | Transactions (billion) | Contribution |
|---|---|---|
| Maharashtra | 5.06 | 13.1% |
| Karnataka | 4.49 | 11.6% |
| Telangana | 3.88 | 10.0% |
| Uttar Pradesh | 3.67 | 9.5% |
| Andhra Pradesh | 3.25 | 8.4% |

These are activity leaders; volume leadership alone does not establish an acceptance gap.

## Ten districts to investigate

| Rank | District | State | Score / 100 | YoY growth | Users / merchant | Merchants | Next action |
|---|---|---|---|---|---|---|---|
| 1 | West Godavari | Andhra Pradesh | 86.7 | 30.5% | 24.6 | 48,583 | Priority field validation |
| 2 | Sangareddy | Telangana | 86.3 | 32.3% | 18.0 | 102,640 | Priority field validation |
| 3 | Dr Br Ambedkar Konaseema | Andhra Pradesh | 85.0 | 33.0% | 20.4 | 45,653 | Priority field validation |
| 4 | East Godavari | Andhra Pradesh | 84.5 | 32.2% | 18.3 | 74,989 | Priority field validation |
| 5 | Sri Potti Sriramulu Nellore | Andhra Pradesh | 84.1 | 30.5% | 18.5 | 93,583 | Priority field validation |
| 6 | Alluri Sitharama Raju | Andhra Pradesh | 83.6 | 37.9% | 36.6 | 11,247 | Priority field validation |
| 7 | Tirupati | Andhra Pradesh | 82.3 | 28.2% | 18.7 | 118,910 | Investigate; sensitive to intensity weighting |
| 8 | Eluru | Andhra Pradesh | 81.4 | 29.2% | 18.9 | 67,639 | Investigate; sensitive to intensity weighting |
| 9 | Mandya | Karnataka | 81.1 | 28.2% | 23.8 | 41,069 | Investigate; sensitive to intensity weighting |
| 10 | Hassan | Karnataka | 80.3 | 26.4% | 26.2 | 42,357 | Investigate; sensitive to intensity weighting |

Full supporting metrics, alternative ranks, and recommendations are in `data/analysis/top10_recommendations.csv`.

## Why the relative-gap signal matters

Among 680 eligible districts, the median is **15.52 registered users per merchant**, compared with a mean of **17.21** and sample standard deviation **7.71**. The middle half ranges from **12.90 to 18.95**. Use the median as a typical-district benchmark because the distribution is skewed. This is not a desired operating target or a population-adjusted penetration rate.

West Godavari has about **24.6 users per registered merchant** and **30.5% YoY transaction growth**. Sangareddy has about **18.0 users per merchant** and **32.3% YoY growth**. Those combinations justify asking whether active acceptance is keeping up with demand.

## Statistical and sensitivity interpretation

| metric_a | metric_b | spearman_rho | n |
|---|---|---|---|
| registered_users | transactions | 0.898 | 680 |
| users_per_merchant | transactions_per_merchant | 0.485 | 680 |
| registered_merchants | transactions | 0.854 | 680 |
| transaction_yoy | users_per_merchant | -0.206 | 680 |

Spearman correlation describes monotonic association across eligible districts. It does not establish that adding merchants causes transaction growth. In particular, a correlation between the two per-merchant ratios is partly mechanical because they share the denominator.

The top ten retain 9 districts under equal weights, but only 6 when intensity is omitted and 6 when size cutoffs are removed. Conclusions about precise rank are therefore less reliable than the broader case for field investigation. Seven of the original ten are in Andhra Pradesh; local geography and behavior require validation before geographic concentration becomes a budget decision.

## Markets to monitor

| state | district | transaction_yoy | merchants_per_1000_users |
|---|---|---|---|
| karnataka | bengaluru urban | 17.3% | 73.9 |
| maharashtra | pune | 23.1% | 85.5 |
| maharashtra | thane | 25.0% | 88.8 |
| rajasthan | jaipur | 15.9% | 101.7 |
| maharashtra | mumbai suburban | 23.0% | 98.3 |
| telangana | medchal malkajgiri | 24.0% | 72.1 |
| tamil nadu | chennai | 15.7% | 67.1 |
| west bengal | north twenty four parganas | 23.0% | 86.6 |
| telangana | hyderabad | 21.3% | 74.2 |
| uttar pradesh | gautambuddha nagar | 21.7% | 76.1 |

These large-user markets fall below the eligible-universe median for both growth percentile and users-per-merchant percentile. Review activation, merchant retention, and category gaps before assuming broad new-merchant acquisition is the right intervention. They are **not proven saturated**.

Also examine Dahod, Jamnagar, Bharuch, and Dakshina Kannada as alternative candidates surfaced by the no-intensity scenario. They provide a useful challenge to the default southern-state concentration.

## Field pilot proposal — assumptions, not observed outcomes

1. **Validate coverage:** Confirm district boundaries and inspect a stratified sample of commercial areas in the six stronger candidates. Include comparable non-shortlisted areas; do not sample only high-activity streets.
2. **Collect missing evidence:** Active PhonePe acceptance, other payment acceptance, onboarding eligibility, merchant categories, local opportunity counts, sales-team travel time, and acquisition costs.
3. **Run a small acquisition pilot:** After discovery, select pilot and comparison areas with similar starting conditions. Define the budget, sample size, and success thresholds with the business before launch.
4. **Measure activation, not just sign-ups:** Track eligible shops contacted, onboarding conversion, first-payment activation, 30-day active merchants, acquisition cost per 30-day active merchant, and incremental business transaction volume versus the comparison areas.
5. **Expand only with evidence:** Scale where active acceptance and unit economics improve. If registrations rise without activity, investigate activation and merchant support before adding more acquisition spend.

No arbitrary conversion, ROI, or revenue target is supplied without operating data. A pilot would produce those measurements; Pulse does not contain them.

## Decision limits

PhonePe ecosystem only; cumulative registrations, not active shops; all-category district demand, not merchant sales; no population/shop denominator; no competitor coverage or acquisition costs; source-specific geography; judgment-based weights; historical missingness; one restated release. Business category counts are state-level and labeled Retail in raw files.

Source: [Official PhonePe Pulse repository](https://github.com/PhonePe/pulse/tree/943e6e52a71513d683f804add12d0b61145e8007). Computation: `sql/02_metrics.sql`, `sql/03_opportunity.sql`, and `src/analyze.py`.
