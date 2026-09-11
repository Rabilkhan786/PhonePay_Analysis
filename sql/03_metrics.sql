CREATE OR REPLACE VIEW state_metrics AS
WITH base AS (
    SELECT
        t.state,
        t.year,
        t.quarter,
        t.period_id,
        CONCAT(t.year, '-Q', t.quarter) AS period_label,
        t.transaction_count,
        t.transaction_amount,
        u.registered_users,
        m.registered_merchants,
        t.transaction_amount / NULLIF(t.transaction_count, 0) AS average_transaction_value,
        100000.0 * m.registered_merchants / NULLIF(u.registered_users, 0)
            AS merchants_per_100k_users,
        1.0 * u.registered_users / NULLIF(m.registered_merchants, 0)
            AS users_per_merchant,
        1.0 * t.transaction_count / NULLIF(u.registered_users, 0)
            AS transactions_per_registered_user,
        t.transaction_amount / NULLIF(u.registered_users, 0)
            AS tpv_per_registered_user,
        1.0 * t.transaction_count / NULLIF(m.registered_merchants, 0)
            AS transactions_per_merchant
    FROM state_transactions AS t
    INNER JOIN state_users AS u
        USING (state, year, quarter, period_id)
    LEFT JOIN state_merchants AS m
        USING (state, year, quarter, period_id)
),
history AS (
    SELECT
        b.*,
        LAG(b.period_id) OVER (
            PARTITION BY b.state
            ORDER BY b.period_id
        ) AS prior_period_id,
        LAG(b.transaction_count) OVER (
            PARTITION BY b.state
            ORDER BY b.period_id
        ) AS prior_transaction_count,
        LAG(b.transaction_amount) OVER (
            PARTITION BY b.state
            ORDER BY b.period_id
        ) AS prior_transaction_amount,
        LAG(b.registered_users) OVER (
            PARTITION BY b.state
            ORDER BY b.period_id
        ) AS prior_registered_users,
        LAG(b.registered_merchants) OVER (
            PARTITION BY b.state
            ORDER BY b.period_id
        ) AS prior_registered_merchants
    FROM base AS b
)
SELECT
    h.*,
    CASE
        WHEN h.period_id - h.prior_period_id = 1
        THEN 1.0 * h.transaction_count / NULLIF(h.prior_transaction_count, 0) - 1
    END AS transaction_qoq,
    CASE
        WHEN h.period_id - h.prior_period_id = 1
        THEN 1.0 * h.transaction_amount / NULLIF(h.prior_transaction_amount, 0) - 1
    END AS tpv_qoq,
    CASE
        WHEN h.period_id - h.prior_period_id = 1
        THEN 1.0 * h.registered_users / NULLIF(h.prior_registered_users, 0) - 1
    END AS user_qoq,
    CASE
        WHEN h.period_id - h.prior_period_id = 1
        THEN 1.0 * h.registered_merchants / NULLIF(h.prior_registered_merchants, 0) - 1
    END AS merchant_qoq,
    1.0 * h.transaction_count / NULLIF(y.transaction_count, 0) - 1
        AS transaction_yoy
FROM history AS h
LEFT JOIN base AS y
    ON h.state = y.state
   AND h.period_id = y.period_id + 4;


CREATE OR REPLACE VIEW district_metrics AS
WITH base AS (
    SELECT
        t.state,
        t.district,
        CONCAT(t.state, '|', t.district) AS district_key,
        t.year,
        t.quarter,
        t.period_id,
        CONCAT(t.year, '-Q', t.quarter) AS period_label,
        t.transaction_count,
        t.transaction_amount,
        u.registered_users,
        m.registered_merchants,
        t.transaction_amount / NULLIF(t.transaction_count, 0) AS average_transaction_value,
        100000.0 * m.registered_merchants / NULLIF(u.registered_users, 0)
            AS merchants_per_100k_users,
        1.0 * u.registered_users / NULLIF(m.registered_merchants, 0)
            AS users_per_merchant,
        1.0 * t.transaction_count / NULLIF(u.registered_users, 0)
            AS transactions_per_registered_user,
        t.transaction_amount / NULLIF(u.registered_users, 0)
            AS tpv_per_registered_user,
        1.0 * t.transaction_count / NULLIF(m.registered_merchants, 0)
            AS transactions_per_merchant
    FROM district_transactions AS t
    INNER JOIN district_users AS u
        USING (state, district, year, quarter, period_id)
    LEFT JOIN district_merchants AS m
        USING (state, district, year, quarter, period_id)
),
history AS (
    SELECT
        b.*,
        LAG(b.period_id) OVER (
            PARTITION BY b.district_key
            ORDER BY b.period_id
        ) AS prior_period_id,
        LAG(b.transaction_count) OVER (
            PARTITION BY b.district_key
            ORDER BY b.period_id
        ) AS prior_transaction_count,
        LAG(b.transaction_amount) OVER (
            PARTITION BY b.district_key
            ORDER BY b.period_id
        ) AS prior_transaction_amount,
        LAG(b.registered_users) OVER (
            PARTITION BY b.district_key
            ORDER BY b.period_id
        ) AS prior_registered_users,
        LAG(b.registered_merchants) OVER (
            PARTITION BY b.district_key
            ORDER BY b.period_id
        ) AS prior_registered_merchants
    FROM base AS b
)
SELECT
    h.*,
    CASE
        WHEN h.period_id - h.prior_period_id = 1
        THEN 1.0 * h.transaction_count / NULLIF(h.prior_transaction_count, 0) - 1
    END AS transaction_qoq,
    CASE
        WHEN h.period_id - h.prior_period_id = 1
        THEN 1.0 * h.transaction_amount / NULLIF(h.prior_transaction_amount, 0) - 1
    END AS tpv_qoq,
    CASE
        WHEN h.period_id - h.prior_period_id = 1
        THEN 1.0 * h.registered_users / NULLIF(h.prior_registered_users, 0) - 1
    END AS user_qoq,
    CASE
        WHEN h.period_id - h.prior_period_id = 1
        THEN 1.0 * h.registered_merchants / NULLIF(h.prior_registered_merchants, 0) - 1
    END AS merchant_qoq,
    1.0 * h.transaction_count / NULLIF(y.transaction_count, 0) - 1
        AS transaction_yoy
FROM history AS h
LEFT JOIN base AS y
    ON h.district_key = y.district_key
   AND h.period_id = y.period_id + 4;


CREATE OR REPLACE VIEW national_metrics AS
WITH totals AS (
    SELECT
        year,
        quarter,
        period_id,
        CONCAT(year, '-Q', quarter) AS period_label,
        SUM(transaction_count) AS transaction_count,
        SUM(transaction_amount) AS transaction_amount,
        SUM(registered_users) AS registered_users,
        CASE
            WHEN COUNT(registered_merchants) = COUNT(*)
            THEN SUM(registered_merchants)
        END AS registered_merchants
    FROM state_metrics
    GROUP BY
        year,
        quarter,
        period_id
),
history AS (
    SELECT
        t.*,
        LAG(t.transaction_count) OVER (
            ORDER BY t.period_id
        ) AS prior_transaction_count,
        LAG(t.transaction_amount) OVER (
            ORDER BY t.period_id
        ) AS prior_transaction_amount
    FROM totals AS t
)
SELECT
    h.*,
    h.transaction_amount / NULLIF(h.transaction_count, 0)
        AS average_transaction_value,
    1.0 * h.transaction_count / NULLIF(h.prior_transaction_count, 0) - 1
        AS transaction_qoq,
    1.0 * h.transaction_amount / NULLIF(h.prior_transaction_amount, 0) - 1
        AS tpv_qoq
FROM history AS h;
