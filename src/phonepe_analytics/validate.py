"""Validate processed PhonePe tables and write an auditable check summary."""

import json
import logging

import pandas as pd

from phonepe_analytics.config import LATEST_QUARTER, LATEST_YEAR, PROCESSED_DIR

LOGGER = logging.getLogger(__name__)


def validate_quarter_table(frame: pd.DataFrame, level: str) -> list[dict]:
    """Run key, identifier, range, missingness, and sign checks."""
    key = ["state", "year", "quarter"]
    if level == "district":
        key.insert(1, "district")
    checks = [
        {
            "check": "duplicate_logical_keys",
            "table": level,
            "failures": int(frame.duplicated(key).sum()),
        },
        {"check": "null_state", "table": level, "failures": int(frame["state"].isna().sum())},
        {
            "check": "invalid_year",
            "table": level,
            "failures": int((~frame["year"].between(2018, LATEST_YEAR)).sum()),
        },
        {
            "check": "invalid_quarter",
            "table": level,
            "failures": int((~frame["quarter"].between(1, 4)).sum()),
        },
    ]
    if level == "district":
        checks.append(
            {
                "check": "null_district",
                "table": level,
                "failures": int(frame["district"].isna().sum()),
            }
        )
    for column in [
        "transaction_count",
        "transaction_amount",
        "registered_users",
        "registered_merchants",
    ]:
        checks.append(
            {
                "check": f"negative_{column}",
                "table": level,
                "failures": int(frame[column].lt(0).sum()),
            }
        )
    latest = frame.loc[frame["year"].eq(LATEST_YEAR) & frame["quarter"].eq(LATEST_QUARTER)]
    core = ["transaction_count", "transaction_amount", "registered_users", "registered_merchants"]
    checks.append(
        {
            "check": "latest_core_values_complete",
            "table": level,
            "failures": int(latest[core].isna().sum().sum()),
        }
    )
    return checks


def reconcile_geographies(state: pd.DataFrame, district: pd.DataFrame) -> pd.DataFrame:
    """Compare state totals with independent sums of district records."""
    metrics = [
        "transaction_count",
        "transaction_amount",
        "registered_users",
        "registered_merchants",
    ]
    district_totals = district.groupby(["state", "period_id"])[metrics].sum(min_count=1)
    state_totals = state.set_index(["state", "period_id"])[metrics]
    return district_totals.sub(state_totals).add_suffix("_difference").reset_index()


def validate_processed_data(
    state: pd.DataFrame, district: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run all validations and raise when a serious rule fails."""
    checks = pd.DataFrame(
        validate_quarter_table(state, "state") + validate_quarter_table(district, "district")
    )
    reconciliation = reconcile_geographies(state, district)
    checks = pd.concat(
        [
            checks,
            pd.DataFrame(
                [
                    {
                        "check": "district_state_count_reconciliation",
                        "table": "geography",
                        "failures": int(reconciliation["transaction_count_difference"].ne(0).sum()),
                    },
                    {
                        "check": "district_state_user_reconciliation",
                        "table": "geography",
                        "failures": int(reconciliation["registered_users_difference"].ne(0).sum()),
                    },
                    {
                        "check": "district_state_merchant_reconciliation",
                        "table": "geography",
                        "failures": int(
                            reconciliation["registered_merchants_difference"].dropna().ne(0).sum()
                        ),
                    },
                    {
                        "check": "district_state_value_reconciliation_over_one_rupee",
                        "table": "geography",
                        "failures": int(
                            reconciliation["transaction_amount_difference"].abs().gt(1).sum()
                        ),
                    },
                ]
            ),
        ],
        ignore_index=True,
    )
    serious = checks.loc[checks["failures"].gt(0)]
    if not serious.empty:
        raise ValueError(f"Processed data failed validation:\n{serious.to_string(index=False)}")
    return checks, reconciliation


def main() -> None:
    """Validate saved processed tables and persist the results."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    state = pd.read_parquet(PROCESSED_DIR / "state_quarter.parquet")
    district = pd.read_parquet(PROCESSED_DIR / "district_quarter.parquet")
    checks, reconciliation = validate_processed_data(state, district)
    checks.to_csv(PROCESSED_DIR / "quality_checks.csv", index=False)
    reconciliation.to_csv(PROCESSED_DIR / "geographic_reconciliation.csv", index=False)
    summary = {row.check: row.failures == 0 for row in checks.itertuples()}
    (PROCESSED_DIR / "validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    LOGGER.info("All %s data-quality checks passed", len(checks))


if __name__ == "__main__":
    main()
