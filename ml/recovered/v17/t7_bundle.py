"""Portable loader for the exact recovered v1.7 T-7 runtime evidence.

The exact historical runtime rows and checkpoint states are stored as ordinary
CSV files next to this module. Calendar features that were deterministic in the
original v1.2 enrichment are derived here, so the persisted history can stay
small and human-auditable.

No network access and no old Library artifact are required.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
HISTORY_FILE = ROOT / "t7_runtime_history.csv"
CHECKPOINT_FILE = ROOT / "t7_checkpoint_state_exact.csv"


def _enrich_calendar(history: pd.DataFrame) -> pd.DataFrame:
    out = history.copy()
    local = pd.to_datetime(out["match_date"], utc=True).dt.tz_convert("Europe/Warsaw")
    out["month"] = local.dt.month
    out["weekday"] = local.dt.weekday
    out["kickoff_minutes"] = local.dt.hour * 60 + local.dt.minute
    day_of_year = local.dt.dayofyear

    out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12.0)
    out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12.0)
    out["doy_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    out["doy_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)
    out["kickoff_sin"] = np.sin(2 * np.pi * out["kickoff_minutes"] / 1440.0)
    out["kickoff_cos"] = np.cos(2 * np.pi * out["kickoff_minutes"] / 1440.0)
    out["is_winter_month"] = out["month"].isin([12, 1, 2]).astype(int)
    out["is_summer_month"] = out["month"].isin([6, 7, 8]).astype(int)
    return out


def load_t7_frames() -> dict[str, pd.DataFrame]:
    history = pd.read_csv(HISTORY_FILE)
    checkpoint = pd.read_csv(CHECKPOINT_FILE)
    if len(history) != 137 or len(checkpoint) != 137:
        raise RuntimeError(
            f"Unexpected exact T-7 evidence row counts: history={len(history)}, "
            f"checkpoint={len(checkpoint)}"
        )
    return {
        "history.csv": _enrich_calendar(history),
        "checkpoint.csv": checkpoint,
    }
