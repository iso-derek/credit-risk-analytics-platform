"""Project configuration helpers."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

DEFAULT_SYNTHETIC_PATH = RAW_DIR / "synthetic_loan_applications.csv"
DEFAULT_PUBLIC_DATA_PATH = RAW_DIR / "public_credit_dataset.csv"


def configured_credit_data_path() -> Path:
    """Return the configured external credit dataset path, if supplied."""

    configured = os.getenv("CREDIT_DATA_PATH", "").strip()
    return Path(configured) if configured else DEFAULT_PUBLIC_DATA_PATH


def configured_lgd(default: float = 0.45) -> float:
    """Return configured loss given default with a safe fallback."""

    try:
        value = float(os.getenv("CREDIT_LGD", default))
    except ValueError:
        return default
    return min(max(value, 0.0), 1.0)
