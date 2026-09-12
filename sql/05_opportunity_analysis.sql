DROP TABLE IF EXISTS district_opportunities;
CREATE TABLE district_opportunities AS
WITH stability AS (
    SELECT
        m.*,
        SUM(CASE WHEN transaction_yoy > 0 THEN 1 ELSE 0 END) OVER (
            PARTITION BY district_key ORDER BY period_id RANGE BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS positive_yoy_quarters_last4,
        AVG(transaction_yoy) OVER (
            PARTITION BY district_key ORDER BY period_id RANGE BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS average_yoy_last4
    FROM district_metrics AS m
),
latest AS (
    SELECT *
    FROM stability
    WHERE period_id = (SELECT MAX(period_id) FROM district_metrics)
      AND registered_users >= 100000
      AND registered_merchants >= 1000
      AND transaction_count >= 1000000
      AND transaction_yoy IS NOT NULL
      AND transaction_qoq IS NOT NULL
),
ranked AS (
    SELECT
        latest.*,
        PERCENT_RANK() OVER (ORDER BY transaction_yoy) AS growth_percentile,
        PERCENT_RANK() OVER (ORDER BY transactions_per_merchant) AS intensity_percentile,
        PERCENT_RANK() OVER (ORDER BY users_per_merchant) AS low_penetration_percentile,
        PERCENT_RANK() OVER (ORDER BY registered_users) AS scale_percentile
    FROM latest
),
scored AS (
    SELECT
        ranked.*,
        ROUND(100.0 * (
            0.30 * growth_percentile
          + 0.25 * intensity_percentile
          + 0.25 * low_penetration_percentile
          + 0.20 * scale_percentile
        ), 10) AS opportunity_score,
        ROUND(100.0 * (
            0.25 * growth_percentile
          + 0.25 * intensity_percentile
          + 0.25 * low_penetration_percentile
          + 0.25 * scale_percentile
        ), 10) AS equal_weight_score,
        ROUND(100.0 * (
            0.40 * growth_percentile
          + 0.35 * low_penetration_percentile
          + 0.25 * scale_percentile
        ), 10) AS no_intensity_score
    FROM ranked
),
segmented AS (
    SELECT
        scored.*,
        PERCENT_RANK() OVER (ORDER BY opportunity_score) AS opportunity_percentile
    FROM scored
)
SELECT
    segmented.*,
    CASE
        WHEN opportunity_percentile >= 0.75 AND low_penetration_percentile >= 0.50 THEN 'EXPAND'
        WHEN scale_percentile >= 0.75 AND low_penetration_percentile < 0.50 THEN 'DEFEND'
        WHEN opportunity_percentile >= 0.50 THEN 'DEVELOP'
        ELSE 'MONITOR'
    END AS business_segment,
    RANK() OVER (ORDER BY opportunity_score DESC) AS opportunity_rank,
    RANK() OVER (ORDER BY equal_weight_score DESC) AS equal_weight_rank,
    RANK() OVER (ORDER BY no_intensity_score DESC) AS no_intensity_rank
FROM segmented;

CREATE INDEX idx_district_opportunities_rank ON district_opportunities (opportunity_rank);
CREATE INDEX idx_district_opportunities_segment ON district_opportunities (business_segment);

CREATE OR REPLACE VIEW investigation_shortlist AS
SELECT
    o.*,
    ROW_NUMBER() OVER (ORDER BY opportunity_score DESC, state, district) AS investigation_rank
FROM district_opportunities AS o
WHERE transaction_qoq > 0
  AND transaction_yoy > 0
  AND user_qoq >= 0
  AND merchant_qoq >= 0;
