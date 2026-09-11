import pandas as pd

from phonepe_analytics.transform import build_quarter_table
from phonepe_analytics.utils import normalize_geography


def test_normalize_geography_preserves_identity() -> None:
    assert normalize_geography("North-24  Parganas District") == "north 24 parganas"


def test_build_quarter_table_joins_source_families() -> None:
    rows = [
        {
            "level": "district",
            "state": "test state",
            "district": "test district",
            "year": 2026,
            "quarter": 2,
            "period_id": 8105,
            "family": "transaction",
            "transaction_count": 10,
            "transaction_amount": 100.0,
        },
        {
            "level": "district",
            "state": "test state",
            "district": "test district",
            "year": 2026,
            "quarter": 2,
            "period_id": 8105,
            "family": "user",
            "registered_users": 5,
        },
        {
            "level": "district",
            "state": "test state",
            "district": "test district",
            "year": 2026,
            "quarter": 2,
            "period_id": 8105,
            "family": "merchant",
            "registered_merchants": 2,
        },
    ]
    result = build_quarter_table(pd.DataFrame(rows), "district")
    assert result.loc[0, "transaction_count"] == 10
    assert result.loc[0, "registered_users"] == 5
    assert result.loc[0, "registered_merchants"] == 2


def test_build_quarter_table_rejects_duplicate_family_keys() -> None:
    row = {
        "level": "state",
        "state": "test state",
        "year": 2026,
        "quarter": 2,
        "period_id": 8105,
        "family": "transaction",
        "transaction_count": 10,
        "transaction_amount": 100.0,
    }
    records = pd.DataFrame([row, row])
    try:
        build_quarter_table(records, "state")
    except ValueError as exc:
        assert "Duplicate" in str(exc)
    else:
        raise AssertionError("Duplicate keys should fail")
