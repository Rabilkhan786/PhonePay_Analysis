"""Project paths and environment-backed database settings."""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
REPORT_DIR = ROOT_DIR / "reports"
EDA_CHART_DIR = REPORT_DIR / "eda_charts"
POWER_BI_DIR = ROOT_DIR / "powerbi"
LATEST_YEAR = 2026
LATEST_QUARTER = 2


@dataclass(frozen=True)
class DatabaseSettings:
    """Connection values read from environment variables."""

    host: str
    port: int
    database: str
    user: str
    password: str

    @property
    def sqlalchemy_url(self) -> str:
        """Return a PyMySQL SQLAlchemy URL with escaped credentials."""
        return (
            f"mysql+pymysql://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.database}?charset=utf8mb4"
        )


def get_database_settings() -> DatabaseSettings:
    """Read required MySQL settings from the environment.

    Raises:
        RuntimeError: If a required setting is missing or the port is invalid.
    """
    load_dotenv(ROOT_DIR / ".env")
    names = ["MYSQL_HOST", "MYSQL_PORT", "MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD"]
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing MySQL settings: {', '.join(missing)}")
    try:
        port = int(os.environ["MYSQL_PORT"])
    except ValueError as exc:
        raise RuntimeError("MYSQL_PORT must be an integer") from exc
    return DatabaseSettings(
        host=os.environ["MYSQL_HOST"],
        port=port,
        database=os.environ["MYSQL_DATABASE"],
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
    )
