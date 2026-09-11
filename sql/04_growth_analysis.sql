DROP TABLE IF EXISTS state_lagged;
CREATE TABLE state_lagged AS
SELECT
    b.*,
    LAG(period_id) OVER (PARTITION BY state ORDER BY period_id) AS prior_period_id,
    LAG(transaction_count) OVER (PARTITION BY state ORDER BY period_id) AS prior_transactions,
    LAG(transaction_amount) OVER (PARTITION BY state ORDER BY period_id) AS prior_tpv,
    LAG(registered_users) OVER (PARTITION BY state ORDER BY period_id) AS prior_users,
    LAG(registered_merchants) OVER (PARTITION BY state ORDER BY period_id) AS prior_merchants
FROM state_base AS b;

DROP TABLE IF EXISTS state_metrics;
CREATE TABLE state_metrics AS
SELECT
    current.*,
    CASE WHEN current.period_id - current.prior_period_id = 1
        THEN 1.0 * current.transaction_count / NULLIF(current.prior_transactions, 0) - 1 END
        AS transaction_qoq,
    CASE WHEN current.period_id - current.prior_period_id = 1
        THEN 1.0 * current.transaction_amount / NULLIF(current.prior_tpv, 0) - 1 END AS tpv_qoq,
    CASE WHEN current.period_id - current.prior_period_id = 1
        THEN 1.0 * current.registered_users / NULLIF(current.prior_users, 0) - 1 END AS user_qoq,
    CASE WHEN current.period_id - current.prior_period_id = 1
        THEN 1.0 * current.registered_merchants / NULLIF(current.prior_merchants, 0) - 1 END
        AS merchant_qoq,
    1.0 * current.transaction_count / NULLIF(year_ago.transaction_count, 0) - 1 AS transaction_yoy
FROM state_lagged AS current
LEFT JOIN state_base AS year_ago
    ON current.state = year_ago.state
   AND current.period_id = year_ago.period_id + 4;

CREATE INDEX idx_state_metrics_geo_period ON state_metrics (state, period_id);

DROP TABLE IF EXISTS district_lagged;
CREATE TABLE district_lagged AS
SELECT
    b.*,
    LAG(period_id) OVER (PARTITION BY district_key ORDER BY period_id) AS prior_period_id,
    LAG(transaction_count) OVER (PARTITION BY district_key ORDER BY period_id) AS prior_transactions,
    LAG(transaction_amount) OVER (PARTITION BY district_key ORDER BY period_id) AS prior_tpv,
    LAG(registered_users) OVER (PARTITION BY district_key ORDER BY period_id) AS prior_users,
    LAG(registered_merchants) OVER (PARTITION BY district_key ORDER BY period_id) AS prior_merchants
FROM district_base AS b;

DROP TABLE IF EXISTS district_metrics;
CREATE TABLE district_metrics AS
SELECT
    current.*,
    CASE WHEN current.period_id - current.prior_period_id = 1
        THEN 1.0 * current.transaction_count / NULLIF(current.prior_transactions, 0) - 1 END
        AS transaction_qoq,
    CASE WHEN current.period_id - current.prior_period_id = 1
        THEN 1.0 * current.transaction_amount / NULLIF(current.prior_tpv, 0) - 1 END AS tpv_qoq,
    CASE WHEN current.period_id - current.prior_period_id = 1
        THEN 1.0 * current.registered_users / NULLIF(current.prior_users, 0) - 1 END AS user_qoq,
    CASE WHEN current.period_id - current.prior_period_id = 1
        THEN 1.0 * current.registered_merchants / NULLIF(current.prior_merchants, 0) - 1 END
        AS merchant_qoq,
    1.0 * current.transaction_count / NULLIF(year_ago.transaction_count, 0) - 1 AS transaction_yoy
FROM district_lagged AS current
LEFT JOIN district_base AS year_ago
    ON current.state = year_ago.state
   AND current.district = year_ago.district
   AND current.period_id = year_ago.period_id + 4;

CREATE INDEX idx_district_metrics_geo_period
    ON district_metrics (state, district, period_id);
