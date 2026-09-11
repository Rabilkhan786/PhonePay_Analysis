USE phonepe_portfolio;
CREATE OR REPLACE VIEW district_metrics AS
WITH history AS (
 SELECT f.*, d.state,d.district,p.year,p.quarter,p.period_label,p.quarter_start,
 LAG(f.period_id) OVER w AS prior_period,
 LAG(transactions) OVER w AS prior_transactions,
 LAG(registered_users) OVER w AS prior_users,
 LAG(registered_merchants) OVER w AS prior_merchants
 FROM fact_district_quarter f
 JOIN dim_district d USING(district_key) JOIN dim_period p USING(period_id)
 WINDOW w AS (PARTITION BY district_key ORDER BY period_id)
)
SELECT h.*,
 (1e0 * h.value_inr)/NULLIF(h.transactions,0) AS average_transaction_value,
 (1e0 * h.registered_users)/NULLIF(h.registered_merchants,0) AS users_per_merchant,
 (1e0 * h.transactions)/NULLIF(h.registered_merchants,0) AS transactions_per_merchant,
 (1e0 * h.value_inr)/NULLIF(h.registered_merchants,0) AS value_per_merchant,
 1000.0*(1e0 * h.registered_merchants)/NULLIF(h.registered_users,0) AS merchants_per_1000_users,
 CASE WHEN h.period_id-prior_period=1 THEN (1e0 * h.transactions)/NULLIF(prior_transactions,0)-1 END AS transaction_qoq,
 CASE WHEN h.period_id-prior_period=1 THEN (1e0 * h.registered_users)/NULLIF(prior_users,0)-1 END AS user_qoq,
 CASE WHEN h.period_id-prior_period=1 THEN (1e0 * h.registered_merchants)/NULLIF(prior_merchants,0)-1 END AS merchant_qoq,
 (1e0 * h.transactions)/NULLIF(y.transactions,0)-1 AS transaction_yoy,
 (1e0 * h.registered_users)/NULLIF(y.registered_users,0)-1 AS user_yoy,
 (1e0 * h.registered_merchants)/NULLIF(y.registered_merchants,0)-1 AS merchant_yoy,
 (1e0 * h.transactions)/NULLIF(s.transactions,0) AS district_share_of_state,
 (1e0 * h.transactions)/NULLIF(SUM(h.transactions) OVER(PARTITION BY h.period_id),0) AS district_share_of_mapped_india
FROM history h LEFT JOIN fact_district_quarter y ON y.district_key=h.district_key AND y.period_id=h.period_id-4
LEFT JOIN fact_state_quarter s ON s.state=h.state AND s.period_id=h.period_id;

CREATE OR REPLACE VIEW state_metrics AS
WITH base AS (
 SELECT s.*, p.year,p.quarter,p.period_label,p.quarter_start,
 c.transactions AS retail_transactions,
 LAG(s.period_id) OVER w AS prior_period,
 LAG(s.transactions) OVER w AS prior_transactions,
 LAG(s.registered_users) OVER w AS prior_users,
 LAG(s.registered_merchants) OVER w AS prior_merchants,
 LAG(c.transactions) OVER w AS prior_retail
 FROM fact_state_quarter s JOIN dim_period p USING(period_id)
 LEFT JOIN fact_state_category c ON c.state=s.state AND c.period_id=s.period_id AND c.category_raw='Retail'
 WINDOW w AS(PARTITION BY s.state ORDER BY s.period_id)
)
SELECT b.*,
 (1e0 * b.value_inr)/NULLIF(b.transactions,0) AS average_transaction_value,
 (1e0 * b.registered_users)/NULLIF(b.registered_merchants,0) AS users_per_merchant,
 (1e0 * b.transactions)/NULLIF(b.registered_merchants,0) AS transactions_per_merchant,
 (1e0 * b.value_inr)/NULLIF(b.registered_merchants,0) AS value_per_merchant,
 1000.0*(1e0 * b.registered_merchants)/NULLIF(b.registered_users,0) AS merchants_per_1000_users,
 CASE WHEN b.period_id-prior_period=1 THEN (1e0 * b.transactions)/NULLIF(prior_transactions,0)-1 END AS transaction_qoq,
 CASE WHEN b.period_id-prior_period=1 THEN (1e0 * b.registered_users)/NULLIF(prior_users,0)-1 END AS user_qoq,
 CASE WHEN b.period_id-prior_period=1 THEN (1e0 * b.registered_merchants)/NULLIF(prior_merchants,0)-1 END AS merchant_qoq,
 CASE WHEN b.period_id-prior_period=1 THEN (1e0 * b.retail_transactions)/NULLIF(prior_retail,0)-1 END AS retail_qoq,
 (1e0 * b.transactions)/NULLIF(y.transactions,0)-1 AS transaction_yoy,
 (1e0 * b.registered_users)/NULLIF(y.registered_users,0)-1 AS user_yoy,
 (1e0 * b.registered_merchants)/NULLIF(y.registered_merchants,0)-1 AS merchant_yoy,
 (1e0 * b.transactions)/NULLIF(SUM(b.transactions) OVER(PARTITION BY b.period_id),0) AS state_contribution
FROM base b LEFT JOIN fact_state_quarter y ON y.state=b.state AND y.period_id=b.period_id-4;

CREATE OR REPLACE VIEW national_metrics AS
WITH totals AS (
 SELECT period_id,SUM(transactions) transactions,SUM(value_inr) value_inr,
 CASE WHEN COUNT(registered_users)=COUNT(*) THEN SUM(registered_users) END registered_users,
 CASE WHEN COUNT(registered_merchants)=COUNT(*) THEN SUM(registered_merchants) END registered_merchants
 FROM fact_state_quarter GROUP BY period_id
)
SELECT t.*,p.period_label,p.quarter_start,
 (1e0 * t.value_inr)/NULLIF(t.transactions,0) average_transaction_value,
 (1e0 * t.transactions)/NULLIF(LAG(t.transactions) OVER(ORDER BY period_id),0)-1 AS transaction_qoq
FROM totals t JOIN dim_period p USING(period_id);
