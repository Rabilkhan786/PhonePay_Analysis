import numpy as np
import pandas as pd
import pytest

from phonepe_analytics.metrics import add_growth_metrics, add_ratio_metrics, score_opportunities
from phonepe_analytics.utils import safe_divide


def test_safe_divide_returns_null_for_zero() -> None:
    assert np.isnan(safe_divide(10, 0))


def test_ratio_metrics_use_safe_division() -> None:
    frame = pd.DataFrame(
        {
            "transaction_count": [20],
            "transaction_amount": [200.0],
            "registered_users": [10],
            "registered_merchants": [0],
        }
    )
    result = add_ratio_metrics(frame)
    assert result.loc[0, "average_transaction_value"] == 10
    assert np.isnan(result.loc[0, "users_per_merchant"])


def test_growth_requires_consecutive_quarters() -> None:
    frame = pd.DataFrame(
        {
            "state": ["a", "a", "a"],
            "district": ["x", "x", "x"],
            "period_id": [8100, 8101, 8103],
            "transaction_count": [100, 110, 121],
            "transaction_amount": [1_000, 1_100, 1_210],
            "registered_users": [50, 55, 60],
            "registered_merchants": [10, 11, 12],
        }
    )
    result = add_growth_metrics(frame, ["state", "district"])
    assert result.loc[result["period_id"].eq(8101), "transaction_count_qoq"].iat[
        0
    ] == pytest.approx(0.1)
    assert np.isnan(result.loc[result["period_id"].eq(8103), "transaction_count_qoq"].iat[0])


def test_opportunity_score_stays_in_range_and_segments() -> None:
    frame = pd.DataFrame(
        {
            "transaction_count": [1_000_000, 2_000_000, 3_000_000, 4_000_000],
            "registered_users": [100_000, 200_000, 300_000, 400_000],
            "registered_merchants": [1_000, 2_000, 3_000, 4_000],
            "transaction_yoy": [0.1, 0.2, 0.3, 0.4],
            "transactions_per_merchant": [1_000, 1_100, 1_200, 1_300],
            "users_per_merchant": [10, 12, 14, 16],
        }
    )
    result = score_opportunities(frame)
    assert result["opportunity_score"].between(0, 100).all()
    assert set(result["business_segment"]).issubset({"EXPAND", "DEFEND", "DEVELOP", "MONITOR"})
