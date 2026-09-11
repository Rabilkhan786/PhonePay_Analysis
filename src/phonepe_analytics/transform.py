"""Transform extracted PhonePe records into tidy analytical tables."""

import logging

import pandas as pd

from phonepe_analytics.config import INTERIM_DIR, PROCESSED_DIR

LOGGER = logging.getLogger(__name__)
KEY_COLUMNS = ["state", "district", "year", "quarter", "period_id"]


def build_quarter_table(records: pd.DataFrame, level: str) -> pd.DataFrame:
    """Join transaction, user, and merchant records at one geographic grain."""
    selected = records.loc[records["level"].eq(level)].copy()
    keys = (
        KEY_COLUMNS
        if level == "district"
        else [column for column in KEY_COLUMNS if column != "district"]
    )
    pieces = []
    for family, metrics in {
        "transaction": ["transaction_count", "transaction_amount"],
        "user": ["registered_users"],
        "merchant": ["registered_merchants"],
    }.items():
        piece = selected.loc[selected["family"].eq(family), keys + metrics]
        if piece.duplicated(keys).any():
            raise ValueError(f"Duplicate {level} {family} keys")
        pieces.append(piece)
    result = pieces[0]
    for piece in pieces[1:]:
        result = result.merge(piece, on=keys, how="outer", validate="one_to_one")
    return result.sort_values(keys).reset_index(drop=True)


def split_analytical_tables(state: pd.DataFrame, district: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create narrow tables used by MySQL while keeping a combined Power BI grain."""
    state_key = ["state", "year", "quarter", "period_id"]
    district_key = ["state", "district", "year", "quarter", "period_id"]
    return {
        "state_transactions": state[state_key + ["transaction_count", "transaction_amount"]].dropna(
            subset=["transaction_count", "transaction_amount"]
        ),
        "district_transactions": district[
            district_key + ["transaction_count", "transaction_amount"]
        ].dropna(subset=["transaction_count", "transaction_amount"]),
        "state_users": state[state_key + ["registered_users"]].dropna(subset=["registered_users"]),
        "district_users": district[district_key + ["registered_users"]].dropna(
            subset=["registered_users"]
        ),
        "state_merchants": state[state_key + ["registered_merchants"]].dropna(
            subset=["registered_merchants"]
        ),
        "district_merchants": district[district_key + ["registered_merchants"]].dropna(
            subset=["registered_merchants"]
        ),
    }


def transform_records(records: pd.DataFrame, categories: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build, type, and return all processed tables."""
    state = build_quarter_table(records, "state")
    district = build_quarter_table(records, "district")
    integer_columns = ["year", "quarter", "period_id"]
    for frame in (state, district, categories):
        for column in integer_columns:
            if column in frame:
                frame[column] = frame[column].astype("int64")
    for frame in (state, district):
        frame["transaction_count"] = frame["transaction_count"].astype("Int64")
        frame["registered_users"] = frame["registered_users"].astype("Int64")
        frame["registered_merchants"] = frame["registered_merchants"].astype("Int64")
    tables = split_analytical_tables(state, district)
    tables.update(
        {
            "state_quarter": state,
            "district_quarter": district,
            "state_transaction_categories": categories,
        }
    )
    return tables


def main() -> None:
    """Transform interim extracts and write CSV and Parquet outputs."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    records = pd.read_parquet(INTERIM_DIR / "hover_records.parquet")
    categories = pd.read_parquet(INTERIM_DIR / "state_transaction_categories.parquet")
    tables = transform_records(records, categories)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)
        frame.to_parquet(PROCESSED_DIR / f"{name}.parquet", index=False)
        LOGGER.info("Wrote %s rows to %s", len(frame), name)


if __name__ == "__main__":
    main()
