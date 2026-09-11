CREATE OR REPLACE VIEW state_base AS
WITH geography_periods AS (
    SELECT state, year, quarter, period_id FROM state_transactions
    UNION
    SELECT state, year, quarter, period_id FROM state_users
    UNION
    SELECT state, year, quarter, period_id FROM state_merchants
)
SELECT
    k.state,
    k.year,
    k.quarter,
    k.period_id,
    CONCAT(k.year, '-Q', k.quarter) AS period_label,
    t.transaction_count,
    t.transaction_amount,
    u.registered_users,
    m.registered_merchants,
    1e0 * t.transaction_amount / NULLIF(t.transaction_count, 0) AS average_transaction_value,
    1e5 * m.registered_merchants / NULLIF(u.registered_users, 0) AS merchants_per_100k_users,
    1e0 * u.registered_users / NULLIF(m.registered_merchants, 0) AS users_per_merchant,
    1e0 * t.transaction_count / NULLIF(u.registered_users, 0) AS transactions_per_registered_user,
    1e0 * t.transaction_amount / NULLIF(u.registered_users, 0) AS tpv_per_registered_user,
    1e0 * t.transaction_count / NULLIF(m.registered_merchants, 0) AS transactions_per_merchant
FROM geography_periods AS k
LEFT JOIN state_transactions AS t USING (state, year, quarter, period_id)
LEFT JOIN state_users AS u USING (state, year, quarter, period_id)
LEFT JOIN state_merchants AS m USING (state, year, quarter, period_id);

CREATE OR REPLACE VIEW district_base AS
WITH geography_periods AS (
    SELECT state, district, year, quarter, period_id FROM district_transactions
    UNION
    SELECT state, district, year, quarter, period_id FROM district_users
    UNION
    SELECT state, district, year, quarter, period_id FROM district_merchants
)
SELECT
    k.state,
    k.district,
    k.year,
    k.quarter,
    k.period_id,
    CONCAT(k.state, '|', k.district) AS district_key,
    CONCAT(k.year, '-Q', k.quarter) AS period_label,
    t.transaction_count,
    t.transaction_amount,
    u.registered_users,
    m.registered_merchants,
    1e0 * t.transaction_amount / NULLIF(t.transaction_count, 0) AS average_transaction_value,
    1e5 * m.registered_merchants / NULLIF(u.registered_users, 0) AS merchants_per_100k_users,
    1e0 * u.registered_users / NULLIF(m.registered_merchants, 0) AS users_per_merchant,
    1e0 * t.transaction_count / NULLIF(u.registered_users, 0) AS transactions_per_registered_user,
    1e0 * t.transaction_amount / NULLIF(u.registered_users, 0) AS tpv_per_registered_user,
    1e0 * t.transaction_count / NULLIF(m.registered_merchants, 0) AS transactions_per_merchant
FROM geography_periods AS k
LEFT JOIN district_transactions AS t USING (state, district, year, quarter, period_id)
LEFT JOIN district_users AS u USING (state, district, year, quarter, period_id)
LEFT JOIN district_merchants AS m USING (state, district, year, quarter, period_id);

CREATE OR REPLACE VIEW national_metrics AS
WITH totals AS (
    SELECT
        period_id,
        year,
        quarter,
        period_label,
        CASE WHEN COUNT(transaction_count) = COUNT(*) THEN SUM(transaction_count) END
            AS transaction_count,
        CASE WHEN COUNT(transaction_amount) = COUNT(*) THEN SUM(transaction_amount) END
            AS transaction_amount,
        CASE WHEN COUNT(registered_users) = COUNT(*) THEN SUM(registered_users) END
            AS registered_users,
        CASE WHEN COUNT(registered_merchants) = COUNT(*) THEN SUM(registered_merchants) END
            AS registered_merchants
    FROM state_base
    GROUP BY period_id, year, quarter, period_label
)
SELECT
    totals.*,
    1e0 * transaction_amount / NULLIF(transaction_count, 0) AS average_transaction_value,
    CASE WHEN period_id - LAG(period_id) OVER history = 1
        THEN 1e0 * transaction_count / NULLIF(LAG(transaction_count) OVER history, 0) - 1 END
        AS transaction_qoq,
    CASE WHEN period_id - LAG(period_id) OVER history = 1
        THEN 1e0 * transaction_amount / NULLIF(LAG(transaction_amount) OVER history, 0) - 1 END
        AS tpv_qoq
FROM totals
WINDOW history AS (ORDER BY period_id);
