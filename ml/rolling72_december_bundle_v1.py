"""Render isolated Rolling72 source and PERS/drift24 SQL from pinned templates.

This generates reviewable files only. Activation, admission, and scheduling
are separate operations. Model, eligibility and outcome logic are inherited
byte for byte apart from the enumerated lane and index names.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

SOURCE_ID = "rolling72-december-source-v1"
PAIR_ID = "rolling72-december-pair-v1"
TEMPLATES = {
    "source": (
        "supabase/sql/rolling72_mvp_research_v1.sql",
        "911dc9a55159b8ec2e3acaf0bc41fb7d5380f860e6aec44bdc637ae1042a7270",
    ),
    "paired": (
        "supabase/sql/rolling72_mvp_paired_drift24_v1.sql",
        "82593342ecc745a2f5d191b783e9d4106d3c2eb328200ba29d3a61308397f06d",
    ),
}
SOURCE_RENAMES = {
    "rolling72_mvp_research_v1": "rolling72_december_source_v1",
    "rolling72-mvp-research-v1": SOURCE_ID,
}
PAIR_RENAMES = {
    "rolling72_mvp_paired_drift24_v1": "rolling72_december_pair_v1",
    "rolling72-mvp-paired-drift24-v1": PAIR_ID,
}
SOURCE_INDEX_RENAMES = {
    "rolling72_mvp_attempt_snapshot_idx": "rolling72_december_attempt_snapshot_idx",
    "rolling72_mvp_seal_capture_idx": "rolling72_december_seal_capture_idx",
}
MANIFEST_TEMPLATES = {
    "source": ("rolling72_mvp_research_v1", "10d6c91af793348993a5c90212b6a340646b42518b6d75ac6b1be3b3864e406d"),
    "paired": ("rolling72_mvp_paired_drift24_v1", "6f8ee5d4e0ac0a3892f8b5525ee10a0c7b02559c04c705147a47677e4260bf0d"),
}


def generate_sql(root: Path) -> dict[str, str]:
    """Return the isolated source and comparator SQL, failing on template drift."""
    replacements = {
        "source": SOURCE_RENAMES | SOURCE_INDEX_RENAMES,
        "paired": SOURCE_RENAMES | PAIR_RENAMES,
    }
    results = {}
    for name, (path, digest) in TEMPLATES.items():
        data = (root / path).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"pinned {name} SQL changed; review before regenerating")
        rendered = data.decode("utf-8")
        for old, new in replacements[name].items():
            if old not in rendered:
                raise ValueError(f"required {name} lane reference absent: {old}")
            rendered = rendered.replace(old, new)
        if any(old in rendered for old in SOURCE_RENAMES | PAIR_RENAMES | SOURCE_INDEX_RENAMES):
            raise ValueError(f"{name} output retains an old lane or index")
        results[name] = rendered
    return results


def generate_manifests(
    root: Path, *, issue_until: str, scoring_until: str, max_fixtures: int,
) -> dict[str, bytes]:
    """Bind an explicitly proposed window to the exact generated SQL bytes."""
    clocks = []
    for clock in (issue_until, scoring_until):
        if not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", clock):
            raise ValueError("deadlines require UTC timestamps to whole seconds")
        clocks.append(datetime.fromisoformat(clock))
    if clocks[1] - clocks[0] < timedelta(hours=78):
        raise ValueError("scoring grace must be at least 78 hours")
    if type(max_fixtures) is not int or not 1 <= max_fixtures <= 1000:
        raise ValueError("max_fixtures must be an integer in [1, 1000]")
    rendered = generate_sql(root)
    result = {}
    for name, (path, digest) in MANIFEST_TEMPLATES.items():
        raw = (root / "ml/artifacts" / path / "activation_manifest.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f"pinned {name} manifest changed")
        manifest = json.loads(raw)
        lane_id = SOURCE_ID if name == "source" else PAIR_ID
        manifest.update(
            lane_id=lane_id, version=lane_id,
            issue_until=issue_until, scoring_until=scoring_until,
            max_fixtures=max_fixtures,
            sql_sha256=hashlib.sha256(rendered[name].encode("utf-8")).hexdigest(),
        )
        if name == "paired":
            manifest.update(
                source_lane_id=SOURCE_ID,
                source_manifest_sha256=hashlib.sha256(result["source"]).hexdigest(),
                source_sql_sha256=hashlib.sha256(rendered["source"].encode("utf-8")).hexdigest(),
            )
        result[name] = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="a new directory for generated SQL")
    parser.add_argument("--issue-until")
    parser.add_argument("--scoring-until")
    parser.add_argument("--max-fixtures", type=int)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    rendered = generate_sql(root)
    options = (args.issue_until, args.scoring_until, args.max_fixtures)
    manifests = {}
    if any(item is not None for item in options):
        if not all(item is not None for item in options):
            parser.error("specify both deadlines and max_fixtures together")
        manifests = generate_manifests(
            root, issue_until=args.issue_until, scoring_until=args.scoring_until,
            max_fixtures=args.max_fixtures,
        )
    args.output.mkdir(mode=0o700, exist_ok=False)
    hashes = {}
    for name, sql in rendered.items():
        raw = sql.encode("utf-8")
        (args.output / f"{name}.sql").write_bytes(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    for name, raw in manifests.items():
        (args.output / f"{name}_manifest.json").write_bytes(raw)
        hashes[f"{name}_manifest"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(hashes, sort_keys=True))


if __name__ == "__main__":
    main()
