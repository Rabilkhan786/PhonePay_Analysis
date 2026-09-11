"""Load validated tables into MySQL and export analytical views."""

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from phonepe_analytics.config import PROCESSED_DIR, ROOT_DIR, get_database_settings

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

ANALYTICAL_VIEWS = [
    "data_quality_summary",
    "state_metrics",
    "district_metrics",
    "national_metrics",
    "district_opportunities",
    "investigation_shortlist",
]


def create_database_engine() -> Engine:
    """Create a SQLAlchemy engine from environment-backed MySQL settings."""
    return create_engine(
        get_database_settings().sqlalchemy_url,
        pool_pre_ping=True,
    )


def run_sql_file(engine: Engine, file_path: Path) -> None:
    """Execute semicolon-delimited statements from one project SQL file."""
    source = file_path.read_text(encoding="utf-8")
    statements = []

    for statement in source.split(";"):
        cleaned = "\n".join(
            line
            for line in statement.splitlines()
            if not line.lstrip().startswith("--")
        ).strip()
        if cleaned:
            statements.append(cleaned)

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def load_processed_tables(engine: Engine) -> dict[str, int]:
    """Replace MySQL source tables and return loaded row counts."""
    counts = {}

    with engine.begin() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        for table in reversed(TABLES):
            connection.execute(text(f"DELETE FROM `{table}`"))

        for table in TABLES:
            frame = pd.read_parquet(PROCESSED_DIR / f"{table}.parquet")
            frame.to_sql(
                table,
                connection,
                if_exists="append",
                index=False,
                chunksize=1_000,
                method="multi",
            )
            counts[table] = len(frame)
            LOGGER.info("Loaded %s rows into %s", len(frame), table)

        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    return counts


def export_analytical_views(engine: Engine) -> dict[str, int]:
    """Export MySQL views as portable CSV files for notebooks and Power BI."""
    output_dir = PROCESSED_DIR / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    counts = {}
    with engine.connect() as connection:
        for view in ANALYTICAL_VIEWS:
            frame = pd.read_sql_query(
                text(f"SELECT * FROM `{view}`"),
                connection,
            )
            frame.to_csv(output_dir / f"{view}.csv", index=False)
            counts[view] = len(frame)

    return counts


def main() -> None:
    """Create tables, load data, build views, and export analytical outputs."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    engine = create_database_engine()
    run_sql_file(engine, SQL_DIR / "01_schema.sql")

    loaded = load_processed_tables(engine)

    for sql_name in [
        "02_data_quality.sql",
        "03_metrics.sql",
        "04_opportunity.sql",
    ]:
        run_sql_file(engine, SQL_DIR / sql_name)

    exported = export_analytical_views(engine)

    LOGGER.info("Loaded rows: %s", loaded)
    LOGGER.info("Exported analytical rows: %s", exported)


if __name__ == "__main__":
    main()
