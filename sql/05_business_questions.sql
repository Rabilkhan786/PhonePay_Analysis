-- Question 1: What is the latest national PhonePe payment snapshot?
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

-- Explanation:
-- Returns the latest national scale and growth metrics used to frame the rest of the analysis.
-- Key insight:
-- This establishes whether the ecosystem is expanding and provides the denominator for regional comparisons.


-- Question 2: Which states have the highest transaction activity in the latest quarter?
SELECT
    state,
    transaction_count,
    transaction_amount,
    registered_users,
    registered_merchants,
    merchants_per_100k_users
FROM state_metrics
WHERE period_id = (SELECT MAX(period_id) FROM state_metrics)
ORDER BY transaction_count DESC
LIMIT 15;

-- Explanation:
-- Ranks the largest state markets by transaction volume while retaining scale and merchant-penetration context.
-- Key insight:
-- High transaction volume identifies commercially important markets, but size alone does not indicate expansion need.


-- Question 3: Which large states are growing fastest quarter over quarter?
SELECT
    state,
    transaction_count,
    registered_users,
    transaction_qoq,
    tpv_qoq,
    user_qoq,
    merchant_qoq
FROM state_metrics
WHERE period_id = (SELECT MAX(period_id) FROM state_metrics)
  AND registered_users >= 1000000
  AND transaction_qoq IS NOT NULL
ORDER BY transaction_qoq DESC
LIMIT 15;

-- Explanation:
-- Compares recent momentum among states with a meaningful registered-user base.
-- Key insight:
-- A size filter prevents very small markets from dominating a percentage-growth ranking.


-- Question 4: Which sizeable districts have the strongest year-over-year transaction growth?
SELECT
    state,
    district,
    registered_users,
    registered_merchants,
    transaction_count,
    transaction_yoy,
    transaction_qoq
FROM district_metrics
WHERE period_id = (SELECT MAX(period_id) FROM district_metrics)
  AND registered_users >= 100000
  AND registered_merchants >= 1000
  AND transaction_count >= 1000000
  AND transaction_yoy IS NOT NULL
ORDER BY transaction_yoy DESC
LIMIT 20;

-- Explanation:
-- Finds high-growth districts after applying minimum scale and comparability thresholds.
-- Key insight:
-- Same-quarter YoY growth is more suitable than raw QoQ alone for identifying sustained momentum.


-- Question 5: Which high-demand districts have comparatively low merchant penetration?
SELECT
    state,
    district,
    transaction_count,
    registered_users,
    registered_merchants,
    merchants_per_100k_users,
    users_per_merchant
FROM district_metrics
WHERE period_id = (SELECT MAX(period_id) FROM district_metrics)
  AND registered_users >= 100000
  AND transaction_count >= 1000000
  AND registered_merchants > 0
ORDER BY merchants_per_100k_users ASC, transaction_count DESC
LIMIT 20;

-- Explanation:
-- Surfaces large active districts where merchant registrations are relatively low compared with the user base.
-- Key insight:
-- Low penetration is only a useful opportunity signal when it appears alongside sufficient demand and market scale.


-- Question 6: Where is registered-user growth outpacing merchant-registration growth?
SELECT
    state,
    district,
    registered_users,
    registered_merchants,
    user_qoq,
    merchant_qoq,
    user_qoq - merchant_qoq AS growth_gap
FROM district_metrics
WHERE period_id = (SELECT MAX(period_id) FROM district_metrics)
  AND user_qoq IS NOT NULL
  AND merchant_qoq IS NOT NULL
  AND registered_users >= 100000
ORDER BY growth_gap DESC
LIMIT 20;

-- Explanation:
-- Measures the latest-quarter gap between user-base growth and merchant-registration growth.
-- Key insight:
-- A wide positive gap can flag markets where user-side reach is expanding faster than merchant-side registration.


-- Question 7: Which districts rank highest on the expansion opportunity score?
SELECT
    opportunity_rank,
    state,
    district,
    opportunity_score,
    business_segment,
    transaction_yoy,
    transaction_qoq,
    registered_users,
    registered_merchants,
    merchants_per_100k_users
FROM district_opportunities
ORDER BY opportunity_rank
LIMIT 20;

-- Explanation:
-- Combines demand growth, transaction intensity, relative merchant penetration, and user scale into one ranked view.
-- Key insight:
-- The score is a prioritisation aid; the underlying metrics should always be reviewed before making a recommendation.


-- Question 8: How many districts fall into each business segment?
SELECT
    business_segment,
    COUNT(*) AS district_count,
    AVG(opportunity_score) AS average_opportunity_score,
    AVG(registered_users) AS average_registered_users,
    AVG(merchants_per_100k_users) AS average_merchants_per_100k_users
FROM district_opportunities
GROUP BY business_segment
ORDER BY average_opportunity_score DESC;

-- Explanation:
-- Summarises the EXPAND, DEFEND, DEVELOP, and MONITOR groups.
-- Key insight:
-- Segment counts show whether the final recommendation is concentrated in a narrow set of markets or spread broadly.


-- Question 9: Which top-ranked districts remain strong when transaction intensity is removed?
SELECT
    opportunity_rank,
    no_intensity_rank,
    state,
    district,
    opportunity_score,
    no_intensity_score,
    transaction_yoy,
    registered_users,
    users_per_merchant
FROM district_opportunities
WHERE opportunity_rank <= 20
  AND no_intensity_rank <= 20
ORDER BY opportunity_rank;

-- Explanation:
-- Tests whether leading districts remain attractive under a score that excludes transactions per merchant.
-- Key insight:
-- Districts that stay highly ranked across scoring assumptions are stronger candidates for field validation.


-- Question 10: What is the latest state-level transaction-category mix?
WITH latest_period AS (
    SELECT MAX(period_id) AS period_id
    FROM state_transaction_categories
)
SELECT
    c.category,
    SUM(c.transaction_count) AS transaction_count,
    1.0 * SUM(c.transaction_count)
        / SUM(SUM(c.transaction_count)) OVER () AS transaction_share
FROM state_transaction_categories AS c
INNER JOIN latest_period AS p
    ON c.period_id = p.period_id
GROUP BY c.category
ORDER BY transaction_count DESC;

-- Explanation:
-- Shows the composition of state-level PhonePe transaction counts in the latest quarter.
-- Key insight:
-- Category mix prevents the analysis from treating all ecosystem transactions as merchant-payment activity.
