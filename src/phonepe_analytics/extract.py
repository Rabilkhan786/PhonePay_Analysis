"""Extract state and district records from an official PhonePe Pulse checkout."""

import argparse
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import subprocess

import pandas as pd

from phonepe_analytics.config import INTERIM_DIR, LATEST_QUARTER, LATEST_YEAR
from phonepe_analytics.utils import make_period_id, normalize_geography

LOGGER = logging.getLogger(__name__)


def read_json(file_path: Path) -> dict:
    """Read one JSON file and require a successful PhonePe response."""
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {file_path}") from exc
    if not payload.get("success") or "data" not in payload:
        raise ValueError(f"Unexpected PhonePe response in {file_path}")
    return payload


def extract_hover_records(file_path: Path, family: str, state: str | None = None) -> list[dict]:
    """Extract map-level transaction, user, or merchant records from one file."""
    payload = read_json(file_path)["data"]
    year = int(file_path.parent.name)
    quarter = int(file_path.stem)
    if quarter not in {1, 2, 3, 4}:
        raise ValueError(f"Invalid quarter in {file_path}")
    items = payload.get("hoverDataList")
    if items is None:
        hover_data = payload.get("hoverData")
        if not isinstance(hover_data, dict):
            raise ValueError(f"Missing hover data in {file_path}")
        items = [{"name": name, **values} for name, values in hover_data.items()]
    records = []
    for item in items:
        geography = normalize_geography(item["name"])
        record = {
            "level": "district" if state else "state",
            "state": state or geography,
            "district": geography if state else None,
            "year": year,
            "quarter": quarter,
            "period_id": make_period_id(year, quarter),
            "family": family,
            "raw_name": item["name"],
        }
        if family == "transaction":
            totals = [metric for metric in item["metric"] if metric["type"] == "TOTAL"]
            if len(totals) != 1 or "amount" not in totals[0]:
                raise ValueError(f"Unexpected transaction metrics in {file_path}")
            record.update(
                transaction_count=totals[0]["count"], transaction_amount=totals[0]["amount"]
            )
        else:
            record[f"registered_{'users' if family == 'user' else 'merchants'}"] = item[
                "registeredCount"
            ]
        records.append(record)
    return records


def extract_categories(raw_root: Path) -> pd.DataFrame:
    """Extract state transaction-category counts from aggregated files."""
    records = []
    base = raw_root / "data/aggregated/transaction/country/india/state"
    for file_path in sorted(base.rglob("*.json")):
        state = normalize_geography(file_path.relative_to(base).parts[0])
        year, quarter = int(file_path.parent.name), int(file_path.stem)
        if (year, quarter) > (LATEST_YEAR, LATEST_QUARTER):
            continue
        for item in read_json(file_path)["data"].get("transactionData", []):
            totals = [metric for metric in item["paymentInstruments"] if metric["type"] == "TOTAL"]
            if len(totals) != 1:
                raise ValueError(f"Unexpected category metrics in {file_path}")
            records.append(
                {
                    "state": state,
                    "year": year,
                    "quarter": quarter,
                    "period_id": make_period_id(year, quarter),
                    "category": item["name"],
                    "transaction_count": totals[0]["count"],
                }
            )
    return pd.DataFrame(records)


def extract_source(raw_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Extract the supported source families and return data plus provenance."""
    records = []
    manifest = []
    for family in ("transaction", "user", "merchant"):
        base = raw_root / f"data/map/{family}/hover/country/india"
        for file_path in sorted(base.rglob("*.json")):
            parts = file_path.relative_to(base).parts
            if len(parts) == 2:
                state = None
            elif len(parts) == 4 and parts[0] == "state":
                state = normalize_geography(parts[1])
            else:
                raise ValueError(f"Unexpected source path: {file_path}")
            year, quarter = int(parts[-2]), int(file_path.stem)
            if (year, quarter) > (LATEST_YEAR, LATEST_QUARTER):
                continue
            records.extend(extract_hover_records(file_path, family, state))
            payload = file_path.read_bytes()
            manifest.append(
                {
                    "path": str(file_path.relative_to(raw_root)).replace("\\", "/"),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
    categories = extract_categories(raw_root)
    commit = subprocess.check_output(
        [
            "git",
            "-c",
            f"safe.directory={raw_root.as_posix()}",
            "-C",
            str(raw_root),
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()
    provenance = {
        "repository": "https://github.com/PhonePe/pulse",
        "commit": commit,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_end": f"{LATEST_YEAR}-Q{LATEST_QUARTER}",
        "hover_files": manifest,
    }
    return pd.DataFrame(records), categories, provenance


def main() -> None:
    """Run extraction and write unchanged record values to interim Parquet files."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw", type=Path, required=True, help="Official Pulse repository checkout"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    LOGGER.info("Extraction started from %s", args.raw)
    records, categories, provenance = extract_source(args.raw.resolve())
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    records.to_parquet(INTERIM_DIR / "hover_records.parquet", index=False)
    categories.to_parquet(INTERIM_DIR / "state_transaction_categories.parquet", index=False)
    (INTERIM_DIR / "source_manifest.json").write_text(
        json.dumps(provenance, indent=2), encoding="utf-8"
    )
    LOGGER.info("Extracted %s map records and %s category records", len(records), len(categories))


if __name__ == "__main__":
    main()
