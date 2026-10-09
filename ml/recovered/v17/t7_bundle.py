"""Portable loader for the exact recovered v1.7 T-7 evidence bundle.

The bundle is stored as a base64-encoded tar.gz so the preserved historical
runtime rows, exact checkpoint states and OOS controls travel with the repo.
This module does not fetch network data and does not depend on the old Library.
"""
from __future__ import annotations

import base64
import io
import tarfile
from pathlib import Path

import pandas as pd

DEFAULT_BUNDLE = Path(__file__).with_name("t7_runtime_bundle.tar.gz.b64")
EXPECTED_FILES = {
    "history.csv",
    "checkpoint.csv",
    "v161_oos.csv",
    "v17_oos.csv",
}


def _read_archive(bundle_path: Path = DEFAULT_BUNDLE) -> dict[str, bytes]:
    encoded = "".join(bundle_path.read_text().split())
    # Text transports may omit terminal '=' characters. Restoring canonical
    # Base64 padding is lossless; tar/gzip parsing below still validates payload
    # integrity and will fail if any non-padding byte is missing/corrupted.
    encoded += "=" * (-len(encoded) % 4)
    payload = base64.b64decode(encoded, validate=True)
    result: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            result[member.name] = extracted.read()

    missing = EXPECTED_FILES - set(result)
    extra = set(result) - EXPECTED_FILES
    if missing or extra:
        raise RuntimeError(
            f"Unexpected T-7 bundle contents; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    return result


def load_t7_frames(bundle_path: Path = DEFAULT_BUNDLE) -> dict[str, pd.DataFrame]:
    raw = _read_archive(bundle_path)
    return {
        name: pd.read_csv(io.BytesIO(content))
        for name, content in raw.items()
    }
