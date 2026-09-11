USE phonepe_portfolio;
-- Fixed latest-quarter universe. Thresholds are analyst assumptions, not PhonePe policy.
CREATE OR REPLACE VIEW district_opportunities AS
WITH eligible AS (
 SELECT * FROM district_metrics
 WHERE period_id=(SELECT MAX(period_id) FROM dim_period)
 AND registered_users>=100000 AND registered_merchants>=1000 AND transactions>=1000000
 AND transaction_yoy IS NOT NULL AND transaction_qoq IS NOT NULL
 AND registered_users IS NOT NULL AND registered_merchants>0
), factors AS (
 SELECT *,
 PERCENT_RANK() OVER(ORDER BY transaction_yoy) growth_percentile,
 PERCENT_RANK() OVER(ORDER BY transactions_per_merchant) intensity_percentile,
 PERCENT_RANK() OVER(ORDER BY users_per_merchant) low_penetration_percentile,
 PERCENT_RANK() OVER(ORDER BY registered_users) scale_percentile
 FROM eligible
), scored AS (
 SELECT *,100*(0.30*growth_percentile+0.25*intensity_percentile+0.25*low_penetration_percentile+0.20*scale_percentile) opportunity_score,
 25*(growth_percentile+intensity_percentile+low_penetration_percentile+scale_percentile) equal_weight_score,
 100*(0.40*growth_percentile+0.35*low_penetration_percentile+0.25*scale_percentile) no_intensity_score,
 CASE WHEN growth_percentile>=0.75 AND low_penetration_percentile>=0.75 THEN 'High growth / low relative penetration'
      WHEN growth_percentile<0.50 AND low_penetration_percentile<0.50 THEN 'Established acceptance / slower growth'
      ELSE 'Mixed signals' END market_segment
 FROM factors
)
SELECT *,RANK() OVER(ORDER BY opportunity_score DESC) score_rank,
 ROW_NUMBER() OVER(ORDER BY opportunity_score DESC,state,district) display_rank,
 RANK() OVER(ORDER BY equal_weight_score DESC) equal_weight_rank,
 RANK() OVER(ORDER BY no_intensity_score DESC) no_intensity_rank
FROM scored;

-- Shortlist has positive QoQ and YoY momentum, no declining registration bases.
CREATE OR REPLACE VIEW investigation_shortlist AS
SELECT *,ROW_NUMBER() OVER(ORDER BY opportunity_score DESC,state,district) investigation_rank
FROM district_opportunities
WHERE transaction_qoq>0 AND transaction_yoy>0 AND merchant_qoq>=0 AND user_qoq>=0;
