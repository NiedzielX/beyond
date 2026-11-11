"""Scheduled OIDC-only shadow runtime. Requires the separately deployed gateway.

Restored local ledgers preserve the cloud job history; only newly inserted legal
attempts are published. Historical local records are never backfilled into DB.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

from ml.demand_engine.daily_inventory_path_gateway_v1 import DailyInventoryPathGateway
from ml.demand_engine.daily_inventory_path_ledger_v1 import DailyInventoryPathLedger
from ml.demand_engine.daily_inventory_path_model_v1 import load_model
from ml.demand_engine.daily_inventory_path_dataset_v1 import canonical_hash, parse_timestamp
from ml.run_daily_inventory_path_v1 import _dump, attach_training_support, shadow


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--artifact", default="ml/artifacts/daily_inventory_path_v1.json")
    parser.add_argument("--panel-feed", required=True)
    args = parser.parse_args(argv)
    root = Path(args.runtime)
    root.mkdir(parents=True, exist_ok=True)
    ledger_path = root / "shadow-v1.sqlite"
    gateway = DailyInventoryPathGateway(os.environ.get("DAILY_INVENTORY_PATH_OIDC_TOKEN", ""))
    data = gateway.export()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    _dump(root / f"source-{stamp}.json", data, exclusive=True)
    result = shadow(data, load_model(args.artifact), ledger_path)
    new_ids = {attempt["attempt_id"] for attempt in result["attempts"] if attempt.get("inserted") is True}
    ack_path = root / "remote-published-v1.json"
    acknowledgments = json.loads(ack_path.read_text()) if ack_path.exists() else {}
    published = []
    with DailyInventoryPathLedger(ledger_path) as ledger:
        for attempt in ledger.export_attempts():
            identity = canonical_hash({"issue": attempt["issue"], "model_sha256": attempt["artifact"]["model_sha256"]})
            if identity in acknowledgments:
                continue
            # Retry unacknowledged writes only while still inside their original
            # issue window. A network error must not silently lose an attempt;
            # an expired local record must never become a retrospective DB write.
            issued = parse_timestamp(attempt["issue"]["issued_as_of_at"])
            if not issued <= datetime.now(timezone.utc) <= issued + timedelta(minutes=90):
                continue
            response = gateway.capture(attempt)
            acknowledgments[identity] = response
            _dump(ack_path, acknowledgments)
            published.append(response)
        local_score = ledger.score(data["events"], data["exported_at"])
    remote_score = gateway.score()
    # Remote DB feed retains all previous days even on a fresh GitHub runner.
    _dump(args.panel_feed, attach_training_support(gateway.feed()))
    _dump(root / "gateway-summary.json", {"local": result, "published": published,
        "local_score": local_score, "remote_score": remote_score, "production_change": False})
    print(json.dumps({"new_attempts": len(new_ids), "published_attempts": len(published), "production_change": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
