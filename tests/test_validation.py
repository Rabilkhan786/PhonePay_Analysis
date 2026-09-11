import pandas as pd
import pytest

from phonepe_analytics.validate import validate_quarter_table


def valid_state_row() -> dict:
    return {
        "state": "test state",
        "year": 2026,
        "quarter": 2,
        "period_id": 8105,
        "transaction_count": 10,
        "transaction_amount": 100.0,
        "registered_users": 5,
        "registered_merchants": 2,
    }


def test_validation_reports_negative_values() -> None:
    row = valid_state_row()
    row["transaction_count"] = -1
    checks = pd.DataFrame(validate_quarter_table(pd.DataFrame([row]), "state"))
    failures = checks.set_index("check").loc["negative_transaction_count", "failures"]
    assert failures == 1


def test_validation_reports_duplicate_keys() -> None:
    row = valid_state_row()
    checks = pd.DataFrame(validate_quarter_table(pd.DataFrame([row, row]), "state"))
    failures = checks.set_index("check").loc["duplicate_logical_keys", "failures"]
    assert failures == 1


@pytest.mark.parametrize("quarter", [0, 5])
def test_validation_reports_invalid_quarter(quarter: int) -> None:
    row = valid_state_row()
    row["quarter"] = quarter
    checks = pd.DataFrame(validate_quarter_table(pd.DataFrame([row]), "state"))
    failures = checks.set_index("check").loc["invalid_quarter", "failures"]
    assert failures == 1
