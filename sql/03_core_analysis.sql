CREATE OR REPLACE VIEW state_base AS
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
    1.0 * u.registered_users / NULLIF(m.registered_merchants, 0) AS users_per_merchant,
    1.0 * t.transaction_count / NULLIF(u.registered_users, 0)
        AS transactions_per_registered_user,
    t.transaction_amount / NULLIF(u.registered_users, 0) AS tpv_per_registered_user,
    1.0 * t.transaction_count / NULLIF(m.registered_merchants, 0)
        AS transactions_per_merchant
FROM state_transactions AS t
INNER JOIN state_users AS u
    USING (state, year, quarter, period_id)
LEFT JOIN state_merchants AS m
    USING (state, year, quarter, period_id);

CREATE OR REPLACE VIEW district_base AS
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
    1.0 * u.registered_users / NULLIF(m.registered_merchants, 0) AS users_per_merchant,
    1.0 * t.transaction_count / NULLIF(u.registered_users, 0)
        AS transactions_per_registered_user,
    t.transaction_amount / NULLIF(u.registered_users, 0) AS tpv_per_registered_user,
    1.0 * t.transaction_count / NULLIF(m.registered_merchants, 0)
        AS transactions_per_merchant
FROM district_transactions AS t
INNER JOIN district_users AS u
    USING (state, district, year, quarter, period_id)
LEFT JOIN district_merchants AS m
    USING (state, district, year, quarter, period_id);
