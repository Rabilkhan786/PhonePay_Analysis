"""Load validated tables into MySQL and export analytical views."""

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from phonepe_analytics.config import PROCESSED_DIR, ROOT_DIR, get_database_settings
from phonepe_analytics.validate import validate_categories, validate_processed_data

LOGGER = logging.getLogger(__name__)
SQL_DIR = ROOT_DIR / "sql"
TABLES = [
    "state_transactions",
    "district_transactions",
    "state_users",
    "district_users",
    "state_merchants",
    "district_merchants",
    "state_transaction_categories",
]


def create_database_engine() -> Engine:
    """Create a reusable SQLAlchemy engine from environment settings."""
    return create_engine(get_database_settings().sqlalchemy_url, pool_pre_ping=True)


def run_sql_file(engine: Engine, file_path: Path) -> None:
    """Execute a project SQL file containing simple semicolon-delimited statements."""
    source = file_path.read_text(encoding="utf-8")
    source = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("--"))
    statements = []
    for statement in source.split(";"):
        cleaned = "\n".join(
            line for line in statement.splitlines() if not line.lstrip().startswith("--")
        ).strip()
        if cleaned:
            statements.append(cleaned)
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def load_processed_tables(engine: Engine) -> dict[str, int]:
    """Replace project tables in one transaction and return loaded row counts."""
    state = pd.read_parquet(PROCESSED_DIR / "state_quarter.parquet")
    district = pd.read_parquet(PROCESSED_DIR / "district_quarter.parquet")
    validate_processed_data(state, district)
    validate_categories(
        state, pd.read_parquet(PROCESSED_DIR / "state_transaction_categories.parquet")
    )
    counts = {}
    with engine.begin() as connection:
        for table in reversed(TABLES):
            connection.execute(text(f"DELETE FROM `{table}`"))
        for table in TABLES:
            frame = pd.read_parquet(PROCESSED_DIR / f"{table}.parquet")
            frame.to_sql(
                table, connection, if_exists="append", index=False, chunksize=1_000, method="multi"
            )
            counts[table] = len(frame)
            LOGGER.info("Loaded %s rows into %s", len(frame), table)
    return counts


def export_views(engine: Engine) -> dict[str, int]:
    """Export MySQL analytical views as portable CSV inputs."""
    output = PROCESSED_DIR / "analysis"
    output.mkdir(parents=True, exist_ok=True)
    views = [
        "state_metrics",
        "district_metrics",
        "national_metrics",
        "district_opportunities",
        "investigation_shortlist",
        "data_quality_summary",
    ]
    counts = {}
    for view in views:
        frame = pd.read_sql_query(text(f"SELECT * FROM `{view}`"), engine)
        order = [column for column in ["state", "district", "period_id"] if column in frame]
        if order:
            frame = frame.sort_values(order)
        frame.to_csv(output / f"{view}.csv", index=False)
        counts[view] = len(frame)
    return counts


def main() -> None:
    """Create tables, load data, build views, and export reconciled outputs."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    engine = create_database_engine()
    run_sql_file(engine, SQL_DIR / "01_schema.sql")
    counts = load_processed_tables(engine)
    for sql_name in [
        "02_data_quality.sql",
        "03_core_analysis.sql",
        "04_growth_analysis.sql",
        "05_opportunity_analysis.sql",
    ]:
        run_sql_file(engine, SQL_DIR / sql_name)
    exported = export_views(engine)
    LOGGER.info("Loaded rows: %s", counts)
    LOGGER.info("Exported analytical rows: %s", exported)
    engine.dispose()


if __name__ == "__main__":
    main()
