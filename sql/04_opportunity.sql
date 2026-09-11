CREATE OR REPLACE VIEW district_opportunities AS
WITH stability AS (
    SELECT
        d.*,
        SUM(d.transaction_yoy > 0) OVER (
            PARTITION BY d.district_key
            ORDER BY d.period_id
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS positive_yoy_quarters_last4,
        AVG(d.transaction_yoy) OVER (
            PARTITION BY d.district_key
            ORDER BY d.period_id
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS average_yoy_last4
    FROM district_metrics AS d
),
eligible AS (
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
        e.*,
        PERCENT_RANK() OVER (
            ORDER BY e.transaction_yoy
        ) AS growth_percentile,
        PERCENT_RANK() OVER (
            ORDER BY e.transactions_per_merchant
        ) AS intensity_percentile,
        PERCENT_RANK() OVER (
            ORDER BY e.users_per_merchant
        ) AS low_penetration_percentile,
        PERCENT_RANK() OVER (
            ORDER BY e.registered_users
        ) AS scale_percentile
    FROM eligible AS e
),
scored AS (
    SELECT
        r.*,
        100.0 * (
            0.30 * r.growth_percentile
          + 0.25 * r.intensity_percentile
          + 0.25 * r.low_penetration_percentile
          + 0.20 * r.scale_percentile
        ) AS opportunity_score,
        100.0 * (
            0.25 * r.growth_percentile
          + 0.25 * r.intensity_percentile
          + 0.25 * r.low_penetration_percentile
          + 0.25 * r.scale_percentile
        ) AS equal_weight_score,
        100.0 * (
            0.40 * r.growth_percentile
          + 0.35 * r.low_penetration_percentile
          + 0.25 * r.scale_percentile
        ) AS no_intensity_score
    FROM ranked AS r
),
segmented AS (
    SELECT
        s.*,
        PERCENT_RANK() OVER (
            ORDER BY s.opportunity_score
        ) AS opportunity_percentile
    FROM scored AS s
)
SELECT
    s.*,
    CASE
        WHEN s.opportunity_percentile >= 0.75
         AND s.low_penetration_percentile >= 0.50
            THEN 'EXPAND'
        WHEN s.scale_percentile >= 0.75
         AND s.low_penetration_percentile < 0.50
            THEN 'DEFEND'
        WHEN s.opportunity_percentile >= 0.50
            THEN 'DEVELOP'
        ELSE 'MONITOR'
    END AS business_segment,
    RANK() OVER (
        ORDER BY s.opportunity_score DESC
    ) AS opportunity_rank,
    RANK() OVER (
        ORDER BY s.equal_weight_score DESC
    ) AS equal_weight_rank,
    RANK() OVER (
        ORDER BY s.no_intensity_score DESC
    ) AS no_intensity_rank
FROM segmented AS s;


CREATE OR REPLACE VIEW investigation_shortlist AS
SELECT
    d.*,
    ROW_NUMBER() OVER (
        ORDER BY d.opportunity_score DESC, d.state, d.district
    ) AS investigation_rank
FROM district_opportunities AS d
WHERE d.transaction_qoq > 0
  AND d.transaction_yoy > 0
  AND d.merchant_qoq >= 0
  AND d.user_qoq >= 0;
