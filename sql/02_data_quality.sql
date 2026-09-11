CREATE OR REPLACE VIEW data_quality_summary AS
SELECT 'state_transactions' AS table_name,
       COUNT(*) AS row_count,
       COUNT(DISTINCT CONCAT_WS('|', state, year, quarter)) AS distinct_keys,
       SUM(state IS NULL OR state = '') AS null_identifiers,
       SUM(quarter NOT BETWEEN 1 AND 4) AS invalid_quarters,
       SUM(transaction_count < 0 OR transaction_amount < 0) AS negative_values
FROM state_transactions
UNION ALL
SELECT 'district_transactions', COUNT(*),
       COUNT(DISTINCT CONCAT_WS('|', state, district, year, quarter)),
       SUM(state IS NULL OR state = '' OR district IS NULL OR district = ''),
       SUM(quarter NOT BETWEEN 1 AND 4),
       SUM(transaction_count < 0 OR transaction_amount < 0)
FROM district_transactions
UNION ALL
SELECT 'state_users', COUNT(*),
       COUNT(DISTINCT CONCAT_WS('|', state, year, quarter)),
       SUM(state IS NULL OR state = ''), SUM(quarter NOT BETWEEN 1 AND 4),
       SUM(registered_users < 0)
FROM state_users
UNION ALL
SELECT 'district_users', COUNT(*),
       COUNT(DISTINCT CONCAT_WS('|', state, district, year, quarter)),
       SUM(state IS NULL OR state = '' OR district IS NULL OR district = ''),
       SUM(quarter NOT BETWEEN 1 AND 4), SUM(registered_users < 0)
FROM district_users
UNION ALL
SELECT 'state_merchants', COUNT(*),
       COUNT(DISTINCT CONCAT_WS('|', state, year, quarter)),
       SUM(state IS NULL OR state = ''), SUM(quarter NOT BETWEEN 1 AND 4),
       SUM(registered_merchants < 0)
FROM state_merchants
UNION ALL
SELECT 'district_merchants', COUNT(*),
       COUNT(DISTINCT CONCAT_WS('|', state, district, year, quarter)),
       SUM(state IS NULL OR state = '' OR district IS NULL OR district = ''),
       SUM(quarter NOT BETWEEN 1 AND 4), SUM(registered_merchants < 0)
FROM district_merchants;

