# Analytical SQL questions

Run `01_schema.sql` through `05_opportunity_analysis.sql` using the package loader first. These fenced queries are the single source for analytical questions: copy a block into MySQL Workbench using the dedicated portfolio database. Setup files define reusable tables/views; analytical prose belongs here so it stays beside executable SQL without a second copy of each query.

All latest-period questions use the maximum observed period in the pinned release (2026 Q2). Growth is a fraction; multiply by 100 for percentage points in a display. Amounts are INR. Missing values remain unknown, and registration totals describe a stock within a quarter.

## Question 1: Are source tables complete and unique at their declared grain?

```sql
SELECT
    table_name,
    row_count,
    distinct_keys,
    null_identifiers,
    invalid_quarters,
    negative_values
FROM data_quality_summary
ORDER BY table_name;
```

**Explanation:** Inspect source row counts and basic integrity before interpreting metrics.
**Key insight:** Equal row/key counts and zero identifier/range failures support safe joins. They do not prove historical coverage; Question 2 examines that separately, and the validation notebook reconciles categories and geography.

## Question 2: Where are historical district observations missing?

```sql
SELECT
    period_label,
    COUNT(*) AS district_rows,
    SUM(transaction_count IS NULL) AS missing_transactions,
    SUM(registered_users IS NULL) AS missing_users,
    SUM(registered_merchants IS NULL) AS missing_merchants
FROM district_metrics
GROUP BY period_id, period_label
ORDER BY period_id;
```

**Explanation:** Count unknowns in the union of transaction, user and merchant keys.
**Key insight:** Six historical transaction observations and 1,885 merchant observations are missing. Keeping these rows prevents falsely complete coverage and avoids turning unknowns into zero demand.

## Question 3: How large is the latest national market and how fast is it growing?

```sql
SELECT
    period_label,
    transaction_count,
    transaction_amount,
    registered_users,
    registered_merchants,
    average_transaction_value,
    transaction_qoq,
    tpv_qoq
FROM national_metrics
WHERE period_id = (SELECT MAX(period_id) FROM national_metrics);
```

**Explanation:** Return national totals, weighted ticket size and comparable QoQ growth.
**Key insight:** Q2 2026 has 38.66 billion transactions and INR 45.50 trillion in value. This establishes ecosystem scale; it does not identify local merchant opportunity or merchant revenue.

## Question 4: Which states contribute most transaction activity?

```sql
SELECT
    state,
    transaction_count,
    transaction_amount,
    1e0 * transaction_count / NULLIF(SUM(transaction_count) OVER (), 0)
        AS national_transaction_share
FROM state_metrics
WHERE period_id = (SELECT MAX(period_id) FROM state_metrics)
ORDER BY transaction_count DESC, state;
```

**Explanation:** Calculate shares over the full latest-quarter state population before sorting.
**Key insight:** Maharashtra, Karnataka and Telangana are the largest activity contributors. Volume indicates operating scale, while acceptance gaps require density, growth and local category evidence.

## Question 5: How concentrated is activity within each state?

```sql
SELECT
    state,
    district,
    transaction_count,
    1e0 * transaction_count
        / NULLIF(SUM(transaction_count) OVER (PARTITION BY state), 0)
        AS district_share_of_state,
    RANK() OVER (PARTITION BY state ORDER BY transaction_count DESC) AS state_activity_rank
FROM district_metrics
WHERE period_id = (SELECT MAX(period_id) FROM district_metrics)
ORDER BY state, state_activity_rank, district;
```

**Explanation:** Rank districts inside each state using the appropriate state denominator.
**Key insight:** This separates regional operating centers from nationwide size differences. A state-local leader is not necessarily a high-growth or low-acceptance district.

## Question 6: Which sizeable districts have strong demand growth?

```sql
SELECT
    state,
    district,
    transaction_count,
    registered_users,
    transaction_qoq,
    transaction_yoy,
    user_qoq,
    merchant_qoq
FROM district_metrics
WHERE period_id = (SELECT MAX(period_id) FROM district_metrics)
  AND registered_users >= 100000
  AND transaction_count >= 1000000
  AND transaction_yoy IS NOT NULL
ORDER BY transaction_yoy DESC, state, district
LIMIT 20;
```

**Explanation:** Display both growth and baseline scale instead of ranking percentages alone.
**Key insight:** A large YoY change is stronger screening evidence when the base is meaningful and recent momentum agrees. Growth alone does not explain the mechanism or establish stable district boundaries.

## Question 7: Where does demand outpace merchant-registration growth?

```sql
SELECT
    state,
    district,
    transaction_qoq,
    merchant_qoq,
    transaction_qoq - merchant_qoq AS growth_gap,
    registered_merchants,
    transactions_per_merchant
FROM district_opportunities
WHERE transaction_qoq > merchant_qoq
  AND merchant_qoq >= 0
ORDER BY growth_gap DESC, state, district
LIMIT 20;
```

**Explanation:** Compare demand and registered-merchant momentum within eligible districts.
**Key insight:** A positive growth gap motivates checking active acceptance. The two series have different meanings—quarterly flows versus registration stocks—and district transactions include P2P.

## Question 8: How does state Retail payment mix differ?

```sql
SELECT
    state,
    category,
    transaction_count,
    1e0 * transaction_count
        / NULLIF(SUM(transaction_count) OVER (PARTITION BY state), 0)
        AS state_category_share
FROM state_transaction_categories
WHERE period_id = (SELECT MAX(period_id) FROM state_transaction_categories)
ORDER BY state, category;
```

**Explanation:** Compute payment-purpose shares at their native state-quarter grain.
**Key insight:** Retail share helps interpret commercial relevance of total demand. Do not join category rows directly onto district metrics or assume state mix applies equally to every district.

## Question 9: What is a typical eligible district's registration density?

```sql
SELECT
    COUNT(*) AS eligible_districts,
    AVG(users_per_merchant) AS mean_users_per_merchant,
    STDDEV_SAMP(users_per_merchant) AS sample_standard_deviation,
    MIN(users_per_merchant) AS minimum_users_per_merchant,
    MAX(users_per_merchant) AS maximum_users_per_merchant
FROM district_opportunities;
```

**Explanation:** Summarize spread over the defined eligible universe; notebooks add medians, quartiles, skewness, IQR flags and distributions.
**Key insight:** The eligible-district median is about 15.52 users per merchant, while the mean is about 17.21. The right tail makes a median more representative of a typical eligible district; neither figure is an operating target.

## Question 10: Which business segments emerge from the scoring rules?

```sql
SELECT
    business_segment,
    COUNT(*) AS districts,
    AVG(opportunity_score) AS mean_score,
    AVG(transaction_yoy) AS mean_district_yoy,
    SUM(registered_users) AS registered_users,
    SUM(registered_merchants) AS registered_merchants,
    1e0 * SUM(registered_users) / NULLIF(SUM(registered_merchants), 0)
        AS weighted_users_per_merchant
FROM district_opportunities
GROUP BY business_segment
ORDER BY mean_score DESC;
```

**Explanation:** Compare segment scale and pooled density; mean district growth is explicitly unweighted.
**Key insight:** Segments translate a relative score into research queues. EXPAND and DEFEND are rule-based labels, not evidence of causal opportunity or saturation.

## Question 11: Which ten districts should enter field validation first?

```sql
SELECT
    investigation_rank,
    state,
    district,
    opportunity_score,
    transaction_yoy,
    transaction_qoq,
    users_per_merchant,
    registered_merchants,
    positive_yoy_quarters_last4
FROM investigation_shortlist
WHERE investigation_rank <= 10
ORDER BY investigation_rank;
```

**Explanation:** Rank the positive-momentum investigation pool after scoring the eligible universe.
**Key insight:** West Godavari and Sangareddy lead. All ten have positive YoY growth in the last four calendar quarters, which supports research priority but cannot guarantee future growth.

## Question 12: Do alternative weights retain the same candidates?

```sql
WITH scenario_ranks AS (
    SELECT
        district_key,
        investigation_rank,
        ROW_NUMBER() OVER (ORDER BY equal_weight_score DESC, state, district) AS equal_rank,
        ROW_NUMBER() OVER (ORDER BY no_intensity_score DESC, state, district) AS no_intensity_rank
    FROM investigation_shortlist
)
SELECT
    SUM(investigation_rank <= 10 AND equal_rank <= 10) AS equal_weight_overlap,
    SUM(investigation_rank <= 10 AND no_intensity_rank <= 10) AS no_intensity_overlap
FROM scenario_ranks;
```

**Explanation:** Compare top tens within the same investigation pool, using deterministic tie ordering.
**Key insight:** Equal weights retain nine candidates; removing intensity retains six. Exact rankings depend on analyst priorities, so the six no-intensity survivors warrant stronger research confidence.

## Question 13: Which large markets warrant an activation or coverage review?

```sql
SELECT
    state,
    district,
    registered_users,
    registered_merchants,
    merchants_per_100k_users,
    transaction_yoy,
    merchant_qoq
FROM district_opportunities
WHERE growth_percentile < 0.50
  AND low_penetration_percentile < 0.50
ORDER BY registered_users DESC, state, district
LIMIT 10;
```

**Explanation:** Select large bases with below-median growth and relatively dense merchant registrations.
**Key insight:** These markets can merit activation, retention or category-specific acceptance checks before broad acquisition. The filter is a monitoring signal and does not establish saturation.

## Question 14: Is national growth broad-based across states?

```sql
SELECT
    period_label,
    COUNT(*) AS states_observed,
    COUNT(transaction_yoy) AS states_with_yoy,
    SUM(transaction_yoy > 0) AS states_with_positive_yoy,
    MIN(transaction_yoy) AS minimum_state_yoy,
    MAX(transaction_yoy) AS maximum_state_yoy
FROM state_metrics
GROUP BY period_id, period_label
ORDER BY period_id;
```

**Explanation:** Count growing states and expose the range while retaining the observed-growth denominator.
**Key insight:** The breadth of positive growth complements national totals, which may be dominated by large states. Early quarters lack prior-year comparisons and must not be classified as zero growth.

## Question 15: How geographically concentrated is the investigation shortlist?

```sql
SELECT
    state,
    COUNT(*) AS shortlisted_districts,
    AVG(opportunity_score) AS mean_score
FROM investigation_shortlist
WHERE investigation_rank <= 10
GROUP BY state
ORDER BY shortlisted_districts DESC, state;
```

**Explanation:** Count state representation after selecting the ten investigation candidates.
**Key insight:** Seven of ten are in Andhra Pradesh. Validate district geography and local payment behavior before turning this concentrated signal into a concentrated budget allocation.
