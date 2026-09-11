USE phonepe_portfolio;
-- 1. Activity leaders, with contribution denominators explicit.
SELECT state,transactions,value_inr,state_contribution FROM state_metrics
WHERE period_id=(SELECT MAX(period_id) FROM dim_period) ORDER BY transactions DESC;
-- 2-4. Growth leaders. Inspect base size before discussing percentage growth.
SELECT state,district,registered_users,registered_merchants,transaction_yoy,user_yoy,merchant_yoy
FROM district_metrics WHERE period_id=(SELECT MAX(period_id) FROM dim_period)
AND registered_users>=100000 ORDER BY transaction_yoy DESC;
-- 5-7,9. Large demand and relatively low registration density.
SELECT state,district,users_per_merchant,transactions_per_merchant,market_segment,opportunity_score
FROM district_opportunities ORDER BY opportunity_score DESC;
-- 8. This is a monitoring group, not proof of saturation.
SELECT state,district,merchant_qoq,transaction_yoy,merchants_per_1000_users
FROM district_opportunities WHERE market_segment='Established acceptance / slower growth'
ORDER BY registered_users DESC LIMIT 10;
-- 10. Ten districts to investigate; view includes the entire eligible ranking.
SELECT investigation_rank,state,district,opportunity_score,transaction_qoq,transaction_yoy,
 registered_users,registered_merchants,users_per_merchant,transactions_per_merchant,
 equal_weight_rank,no_intensity_rank
FROM investigation_shortlist WHERE investigation_rank<=10 ORDER BY investigation_rank;
-- Mean and sample standard deviation in MySQL.
-- Median, quartiles and IQR are calculated in the Python analysis script.
SELECT COUNT(*) AS n,
       AVG(users_per_merchant) AS mean_users_per_merchant,
       STDDEV_SAMP(users_per_merchant) AS sample_standard_deviation,
       MIN(users_per_merchant) AS minimum,
       MAX(users_per_merchant) AS maximum
FROM district_opportunities;
