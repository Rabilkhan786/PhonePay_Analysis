"""Verify MySQL exports independently and prepare the canonical Power BI inputs."""

import json
import logging

import numpy as np
import pandas as pd

from phonepe_analytics.config import POWER_BI_DIR, PROCESSED_DIR
from phonepe_analytics.metrics import add_growth_metrics, add_ratio_metrics, score_opportunities

ANALYSIS_DIR = PROCESSED_DIR / "analysis"
MEASURES = [
    "transaction_count",
    "transaction_amount",
    "registered_users",
    "registered_merchants",
    "average_transaction_value",
    "users_per_merchant",
    "merchants_per_100k_users",
    "transactions_per_registered_user",
    "tpv_per_registered_user",
    "transactions_per_merchant",
    "transaction_qoq",
    "tpv_qoq",
    "user_qoq",
    "merchant_qoq",
    "transaction_yoy",
]


def descriptive_statistics(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Summarize observed values without imputing nulls or removing outliers."""
    values = frame[columns].astype(float)
    summary = values.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9, 0.95]).T
    summary["missing"] = values.isna().sum()
    summary["skewness"] = values.skew()
    summary["iqr"] = summary["75%"] - summary["25%"]
    low = summary["25%"] - 1.5 * summary["iqr"]
    high = summary["75%"] + 1.5 * summary["iqr"]
    summary["iqr_outliers"] = (values.lt(low) | values.gt(high)).sum()
    return summary.rename_axis("metric")


def verify_sql_exports() -> dict[str, bool]:
    """Compare every ratio, growth measure, score and segment to processed source rows."""
    checks = {}
    for level in ["state", "district"]:
        keys = ["state"] + (["district"] if level == "district" else [])
        raw = pd.read_parquet(PROCESSED_DIR / f"{level}_quarter.parquet")
        # MySQL stores monetary source values as DECIMAL(24, 2).
        raw["transaction_amount"] = raw["transaction_amount"].round(2)
        expected = add_growth_metrics(add_ratio_metrics(raw), keys).set_index([*keys, "period_id"])
        actual = pd.read_csv(ANALYSIS_DIR / f"{level}_metrics.csv").set_index([*keys, "period_id"])
        checks[f"{level}_grain_preserved"] = (
            actual.index.is_unique
            and expected.index.is_unique
            and set(actual.index) == set(expected.index)
        )
        actual = actual.reindex(expected.index)
        for column in MEASURES:
            checks[f"{level}.{column}"] = np.allclose(
                actual[column].to_numpy(dtype=float, na_value=np.nan),
                expected[column].to_numpy(dtype=float, na_value=np.nan),
                rtol=1e-8,
                atol=0.011 if column == "transaction_amount" else 1e-8,
                equal_nan=True,
            )
    district = expected.reset_index()
    latest = district.loc[district.period_id.eq(district.period_id.max())]
    expected_scores = score_opportunities(latest).set_index(["state", "district"])
    actual_scores = pd.read_csv(ANALYSIS_DIR / "district_opportunities.csv").set_index(
        ["state", "district"]
    )
    checks["eligible_universe"] = set(actual_scores.index) == set(expected_scores.index)
    actual_scores = actual_scores.reindex(expected_scores.index)
    for column in [
        "opportunity_score",
        "equal_weight_score",
        "no_intensity_score",
        "opportunity_rank",
        "equal_weight_rank",
        "no_intensity_rank",
    ]:
        checks[column] = np.allclose(actual_scores[column], expected_scores[column], atol=1e-8)
    checks["business_segments"] = actual_scores.business_segment.eq(
        expected_scores.business_segment
    ).all()
    state = pd.read_parquet(PROCESSED_DIR / "state_quarter.parquet")
    national = pd.read_csv(ANALYSIS_DIR / "national_metrics.csv").set_index("period_id")
    for column in MEASURES[:4]:
        totals = state.groupby("period_id")[column].agg(lambda s: s.sum(min_count=len(s)))
        checks[f"national_complete_{column}"] = np.allclose(
            national.reindex(totals.index)[column],
            totals.to_numpy(dtype=float, na_value=np.nan),
            rtol=1e-9,
            atol=1,
            equal_nan=True,
        )
    checks = {key: bool(value) for key, value in checks.items()}
    (ANALYSIS_DIR / "analysis_validation.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise ValueError(f"SQL/Pandas disagreement: {[k for k, v in checks.items() if not v]}")
    return checks


def shortlist_sensitivity(pool: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare alternative weights within the same positive-momentum pool."""
    ordered = pool.sort_values(
        ["opportunity_score", "state", "district"], ascending=[False, True, True]
    )
    top = ordered.head(10).copy()
    base = set(top.district_key)
    rows = []
    for scenario in ["opportunity", "equal_weight", "no_intensity"]:
        ranked = pool.sort_values(
            [f"{scenario}_score", "state", "district"], ascending=[False, True, True]
        )
        ranks = pd.Series(np.arange(1, len(ranked) + 1), index=ranked.district_key)
        top[f"{scenario}_shortlist_rank"] = top.district_key.map(ranks)
        rows.append(
            {"scenario": scenario, "top10_overlap": len(base & set(ranked.head(10).district_key))}
        )
    top["recommendation"] = np.where(
        top.no_intensity_shortlist_rank.le(10),
        "Priority field validation",
        "Investigate; sensitive to intensity weighting",
    )
    return pd.DataFrame(rows), top


def export_power_bi(top: pd.DataFrame) -> None:
    """Refresh only the seven CSVs referenced by the canonical semantic model."""
    output = POWER_BI_DIR / "data"
    output.mkdir(parents=True, exist_ok=True)
    district = pd.read_csv(ANALYSIS_DIR / "district_metrics.csv")
    opportunities = pd.read_csv(ANALYSIS_DIR / "district_opportunities.csv")
    categories = pd.read_parquet(PROCESSED_DIR / "state_transaction_categories.parquet")
    periods = district[["period_id", "year", "quarter", "period_label"]].drop_duplicates()
    periods["Quarter Start"] = pd.to_datetime(
        dict(year=periods.year, month=periods.quarter * 3 - 2, day=1)
    ).dt.strftime("%Y-%m-%d")
    top = top.assign(Action=top.recommendation)
    exports = {
        "Periods": (
            periods,
            {"period_id": "Period ID", "period_label": "Quarter", "Quarter Start": "Quarter Start"},
        ),
        "States": (district[["state"]].drop_duplicates(), {"state": "State"}),
        "Districts": (
            district[["district_key", "state", "district"]].drop_duplicates(),
            {"district_key": "District Key", "state": "State", "district": "District"},
        ),
        "Payments": (
            district,
            {
                "district_key": "District Key",
                "period_id": "Period ID",
                "transaction_count": "Transactions",
                "transaction_amount": "Value INR",
                "registered_users": "Registered Users",
                "registered_merchants": "Registered Merchants",
            },
        ),
        "State_Payments": (
            categories.loc[categories.category.eq("Retail")],
            {
                "state": "State",
                "period_id": "Period ID",
                "transaction_count": "Retail Transactions",
            },
        ),
        "Opportunities": (
            opportunities,
            {
                "district_key": "District Key",
                "opportunity_score": "Score",
                "transaction_yoy": "YoY Growth",
                "users_per_merchant": "Users per Merchant",
                "transactions_per_merchant": "Transactions per Merchant",
                "registered_users": "Users",
                "registered_merchants": "Merchants",
                "business_segment": "Segment",
                "opportunity_rank": "National Rank",
                "low_penetration_percentile": "Low Penetration Percentile",
                "growth_percentile": "Growth Percentile",
                "equal_weight_rank": "Equal Weight Rank",
                "no_intensity_rank": "No Intensity Rank",
            },
        ),
        "Recommendations": (
            top,
            {
                "district_key": "District Key",
                "investigation_rank": "Priority",
                "opportunity_score": "Score",
                "transaction_yoy": "YoY Growth",
                "users_per_merchant": "Users per Merchant",
                "registered_merchants": "Merchants",
                "business_segment": "Segment",
                "positive_yoy_quarters_last4": "Positive YoY Quarters",
                "Action": "Action",
                "no_intensity_shortlist_rank": "Alternative Rank",
            },
        ),
    }
    for name, (frame, columns) in exports.items():
        frame[list(columns)].rename(columns=columns).to_csv(output / f"{name}.csv", index=False)


def main() -> None:
    """Verify SQL results, export statistics and sensitivity, then refresh BI CSVs."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    checks = verify_sql_exports()
    district = pd.read_csv(ANALYSIS_DIR / "district_metrics.csv")
    latest = district.loc[district.period_id.eq(district.period_id.max())]
    descriptive_statistics(latest, MEASURES).to_csv(ANALYSIS_DIR / "descriptive_statistics.csv")
    latest[MEASURES].corr(method="spearman").to_csv(
        ANALYSIS_DIR / "spearman_correlations.csv", index_label="metric"
    )
    pool = pd.read_csv(ANALYSIS_DIR / "investigation_shortlist.csv")
    sensitivity, top = shortlist_sensitivity(pool)
    sensitivity.to_csv(ANALYSIS_DIR / "score_sensitivity.csv", index=False)
    top.to_csv(ANALYSIS_DIR / "top10_recommendations.csv", index=False)
    export_power_bi(top)
    logging.info(
        "Passed %s independent comparisons and refreshed seven Power BI inputs", len(checks)
    )


if __name__ == "__main__":
    main()
