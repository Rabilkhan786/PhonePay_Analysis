"""Reusable metric and opportunity-score calculations."""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from phonepe_analytics.utils import safe_divide

DEFAULT_WEIGHTS = {
    "transaction_yoy": 0.30,
    "transactions_per_merchant": 0.25,
    "users_per_merchant": 0.25,
    "registered_users": 0.20,
}


def add_ratio_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Add safe, clearly named demand and merchant-penetration ratios."""
    result = frame.copy()
    result["average_transaction_value"] = safe_divide(
        result["transaction_amount"], result["transaction_count"]
    )
    result["users_per_merchant"] = safe_divide(
        result["registered_users"], result["registered_merchants"]
    )
    result["merchants_per_100k_users"] = safe_divide(
        result["registered_merchants"] * 100_000, result["registered_users"]
    )
    result["transactions_per_registered_user"] = safe_divide(
        result["transaction_count"], result["registered_users"]
    )
    result["tpv_per_registered_user"] = safe_divide(
        result["transaction_amount"], result["registered_users"]
    )
    result["transactions_per_merchant"] = safe_divide(
        result["transaction_count"], result["registered_merchants"]
    )
    return result


def add_growth_metrics(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    """Add consecutive-quarter and same-quarter-last-year growth measures."""
    result = frame.sort_values(group_columns + ["period_id"]).copy()
    metrics = [
        "transaction_count",
        "transaction_amount",
        "registered_users",
        "registered_merchants",
    ]
    grouped = result.groupby(group_columns, dropna=False)
    previous_period = grouped["period_id"].shift(1)
    for metric in metrics:
        previous = grouped[metric].shift(1)
        result[
            {
                "transaction_count": "transaction_qoq",
                "transaction_amount": "tpv_qoq",
                "registered_users": "user_qoq",
                "registered_merchants": "merchant_qoq",
            }[metric]
        ] = (safe_divide(result[metric], previous) - 1).where(
            result["period_id"].sub(previous_period).eq(1)
        )
    prior_year = result[group_columns + ["period_id", "transaction_count"]].copy()
    prior_year["period_id"] += 4
    prior_year = prior_year.rename(columns={"transaction_count": "transaction_count_last_year"})
    result = result.merge(
        prior_year, on=group_columns + ["period_id"], how="left", validate="one_to_one"
    )
    result["transaction_yoy"] = (
        safe_divide(result["transaction_count"], result["transaction_count_last_year"]) - 1
    )
    return result


def percentile_rank(series: pd.Series) -> pd.Series:
    """Match the MySQL PERCENT_RANK definition, including tied values."""
    if len(series) <= 1:
        return pd.Series(0.0, index=series.index)
    return (series.rank(method="min") - 1) / (len(series) - 1)


def score_opportunities(
    frame: pd.DataFrame,
    weights: Mapping[str, float] = DEFAULT_WEIGHTS,
    minimum_users: int = 100_000,
    minimum_merchants: int = 1_000,
    minimum_transactions: int = 1_000_000,
) -> pd.DataFrame:
    """Create a defensible 0–100 score for comparable district records."""
    if (
        set(weights) != set(DEFAULT_WEIGHTS)
        or any(not np.isfinite(value) or value < 0 for value in weights.values())
        or not np.isclose(sum(weights.values()), 1.0)
    ):
        raise ValueError(
            "Use the four scoring factors with nonnegative finite weights summing to 1"
        )
    if frame["period_id"].nunique() > 1:
        raise ValueError("Score one quarter at a time")
    eligible = frame.loc[
        frame["registered_users"].ge(minimum_users)
        & frame["registered_merchants"].ge(minimum_merchants)
        & frame["registered_merchants"].gt(0)
        & frame["transaction_count"].ge(minimum_transactions)
    ].dropna(subset=[*DEFAULT_WEIGHTS, "transaction_qoq"])
    result = eligible.copy()
    factors = {
        "transaction_yoy": "growth_percentile",
        "transactions_per_merchant": "intensity_percentile",
        "users_per_merchant": "low_penetration_percentile",
        "registered_users": "scale_percentile",
    }
    for metric, column in factors.items():
        result[column] = percentile_rank(result[metric])
    result["opportunity_score"] = sum(result[factors[m]] * w * 100 for m, w in weights.items())
    result["equal_weight_score"] = 25 * result[list(factors.values())].sum(axis=1)
    result["no_intensity_score"] = 100 * (
        0.40 * result["growth_percentile"]
        + 0.35 * result["low_penetration_percentile"]
        + 0.25 * result["scale_percentile"]
    )
    # Stabilize mathematical ties across MySQL and NumPy floating-point arithmetic.
    scores = ["opportunity_score", "equal_weight_score", "no_intensity_score"]
    result[scores] = result[scores].round(10)
    result["opportunity_percentile"] = percentile_rank(result["opportunity_score"])
    result["business_segment"] = np.select(
        [
            result["opportunity_percentile"].ge(0.75)
            & result["low_penetration_percentile"].ge(0.50),
            result["scale_percentile"].ge(0.75) & result["low_penetration_percentile"].lt(0.50),
            result["opportunity_percentile"].ge(0.50),
        ],
        ["EXPAND", "DEFEND", "DEVELOP"],
        default="MONITOR",
    )
    for score, rank in [
        ("opportunity_score", "opportunity_rank"),
        ("equal_weight_score", "equal_weight_rank"),
        ("no_intensity_score", "no_intensity_rank"),
    ]:
        result[rank] = result[score].rank(method="min", ascending=False).astype(int)
    return result.sort_values(
        ["opportunity_score", "state", "district"], ascending=[False, True, True]
    )
