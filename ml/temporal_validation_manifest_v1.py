#!/usr/bin/env python3
"""Persist exact time-respecting fold identities for Beyond experiments."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ml.temporal_validation_v1 import (
    build_expanding_group_folds,
    build_forward_event_folds,
    fold_manifest,
    write_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--protocol-id", required=True)
    parser.add_argument("--source-id")
    parser.add_argument("--mode", choices=["forward-event", "expanding-group"], required=True)
    parser.add_argument("--entity-col", required=True)
    parser.add_argument("--time-col", required=True)
    parser.add_argument("--group-col")
    parser.add_argument("--min-train", type=int, required=True)
    args = parser.parse_args()

    frame = pd.read_csv(args.input_csv)
    if args.mode == "forward-event":
        folds = build_forward_event_folds(
            frame,
            entity_col=args.entity_col,
            time_col=args.time_col,
            min_train_entities=args.min_train,
        )
    else:
        if not args.group_col:
            raise RuntimeError("--group-col is required for expanding-group")
        folds = build_expanding_group_folds(
            frame,
            entity_col=args.entity_col,
            time_col=args.time_col,
            group_col=args.group_col,
            min_train_groups=args.min_train,
        )

    if not folds:
        raise RuntimeError("temporal protocol produced zero evaluation folds")
    manifest = fold_manifest(
        folds,
        protocol_id=args.protocol_id,
        source_id=args.source_id,
    )
    write_manifest(args.output_json, manifest)
    print(
        f"temporal-validation-v1 protocol={args.protocol_id} "
        f"folds={manifest['fold_count']} sha={manifest['folds_sha256']}"
    )


if __name__ == "__main__":
    main()
