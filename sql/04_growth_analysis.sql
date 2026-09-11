-- Materialize once so downstream EDA and scoring reuse indexed metrics.
DROP TABLE IF EXISTS state_metrics;
CREATE TABLE state_metrics AS
WITH lagged AS (
    SELECT
        b.*,
        LAG(period_id) OVER history AS prior_period_id,
        LAG(transaction_count) OVER history AS prior_transactions,
        LAG(transaction_amount) OVER history AS prior_tpv,
        LAG(registered_users) OVER history AS prior_users,
        LAG(registered_merchants) OVER history AS prior_merchants
    FROM state_base AS b
    WINDOW history AS (PARTITION BY state ORDER BY period_id)
)
SELECT
    c.*,
    CASE WHEN c.period_id - c.prior_period_id = 1
        THEN 1e0 * c.transaction_count / NULLIF(c.prior_transactions, 0) - 1 END
        AS transaction_qoq,
    CASE WHEN c.period_id - c.prior_period_id = 1
        THEN 1e0 * c.transaction_amount / NULLIF(c.prior_tpv, 0) - 1 END AS tpv_qoq,
    CASE WHEN c.period_id - c.prior_period_id = 1
        THEN 1e0 * c.registered_users / NULLIF(c.prior_users, 0) - 1 END AS user_qoq,
    CASE WHEN c.period_id - c.prior_period_id = 1
        THEN 1e0 * c.registered_merchants / NULLIF(c.prior_merchants, 0) - 1 END AS merchant_qoq,
    1e0 * c.transaction_count / NULLIF(y.transaction_count, 0) - 1 AS transaction_yoy
FROM lagged AS c
LEFT JOIN state_base AS y
    ON c.state = y.state
   AND c.period_id = y.period_id + 4;

CREATE UNIQUE INDEX idx_state_metrics_geo_period ON state_metrics (state, period_id);

-- Materialize once so downstream EDA and scoring reuse indexed metrics.
DROP TABLE IF EXISTS district_metrics;
CREATE TABLE district_metrics AS
WITH lagged AS (
    SELECT
        b.*,
        LAG(period_id) OVER history AS prior_period_id,
        LAG(transaction_count) OVER history AS prior_transactions,
        LAG(transaction_amount) OVER history AS prior_tpv,
        LAG(registered_users) OVER history AS prior_users,
        LAG(registered_merchants) OVER history AS prior_merchants
    FROM district_base AS b
    WINDOW history AS (PARTITION BY state, district ORDER BY period_id)
)
SELECT
    c.*,
    CASE WHEN c.period_id - c.prior_period_id = 1
        THEN 1e0 * c.transaction_count / NULLIF(c.prior_transactions, 0) - 1 END
        AS transaction_qoq,
    CASE WHEN c.period_id - c.prior_period_id = 1
        THEN 1e0 * c.transaction_amount / NULLIF(c.prior_tpv, 0) - 1 END AS tpv_qoq,
    CASE WHEN c.period_id - c.prior_period_id = 1
        THEN 1e0 * c.registered_users / NULLIF(c.prior_users, 0) - 1 END AS user_qoq,
    CASE WHEN c.period_id - c.prior_period_id = 1
        THEN 1e0 * c.registered_merchants / NULLIF(c.prior_merchants, 0) - 1 END AS merchant_qoq,
    1e0 * c.transaction_count / NULLIF(y.transaction_count, 0) - 1 AS transaction_yoy
FROM lagged AS c
LEFT JOIN district_base AS y
    ON c.state = y.state
   AND c.district = y.district
   AND c.period_id = y.period_id + 4;

CREATE UNIQUE INDEX idx_district_metrics_geo_period ON district_metrics (state, district, period_id);
