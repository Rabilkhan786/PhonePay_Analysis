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
        result[f"{metric}_qoq"] = (safe_divide(result[metric], previous) - 1).where(
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
    if not np.isclose(sum(weights.values()), 1.0):
        raise ValueError("Opportunity weights must sum to 1")
    eligible = frame.loc[
        frame["registered_users"].ge(minimum_users)
        & frame["registered_merchants"].ge(minimum_merchants)
        & frame["transaction_count"].ge(minimum_transactions)
    ].dropna(subset=list(weights))
    result = eligible.copy()
    score = pd.Series(0.0, index=result.index)
    for metric, weight in weights.items():
        rank_column = f"{metric}_percentile"
        result[rank_column] = percentile_rank(result[metric])
        score += result[rank_column] * weight * 100
    result["opportunity_score"] = score.clip(0, 100)
    score_q3 = result["opportunity_score"].quantile(0.75)
    score_median = result["opportunity_score"].median()
    scale_q3 = result["registered_users_percentile"].quantile(0.75)
    low_penetration = result["users_per_merchant_percentile"].ge(0.5)
    result["business_segment"] = np.select(
        [
            result["opportunity_score"].ge(score_q3) & low_penetration,
            result["registered_users_percentile"].ge(scale_q3) & ~low_penetration,
            result["opportunity_score"].ge(score_median),
        ],
        ["EXPAND", "DEFEND", "DEVELOP"],
        default="MONITOR",
    )
    return result.sort_values("opportunity_score", ascending=False)
