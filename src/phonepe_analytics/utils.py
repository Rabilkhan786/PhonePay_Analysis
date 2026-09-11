"""Small shared helpers for names, periods, and safe arithmetic."""

import re

import numpy as np
import pandas as pd


def normalize_geography(value: str) -> str:
    """Standardize a source geography name without guessing renamed areas."""
    normalized = value.lower().replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized.removesuffix(" district").strip()


def make_period_id(year: int, quarter: int) -> int:
    """Create a consecutive integer quarter key."""
    if quarter not in {1, 2, 3, 4}:
        raise ValueError("quarter must be between 1 and 4")
    return year * 4 + quarter - 1


def safe_divide(numerator, denominator):
    """Divide numbers or Series and return null for zero denominators."""
    if isinstance(denominator, pd.Series):
        return numerator.div(denominator.replace(0, np.nan))
    return np.nan if denominator == 0 else numerator / denominator
