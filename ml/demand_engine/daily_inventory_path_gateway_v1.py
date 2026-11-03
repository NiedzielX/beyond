"""GitHub-OIDC client for the prepared, separately deployed shadow gateway."""
from datetime import datetime, timezone
import json
import urllib.error
import urllib.request

from .daily_inventory_path_dataset_v1 import canonical_hash, parse_timestamp
from .daily_inventory_path_ledger_v1 import DailyInventoryPathLedger

GATEWAY_URL = "https://adchzwqboeekhokapxqi.supabase.co/functions/v1/daily_inventory_path_gateway_v1"


class DailyInventoryPathGateway:
    def __init__(self, token: str):
        if not isinstance(token, str) or not token.strip():
            raise ValueError("GitHub OIDC token required")
        self._token = token

    def call(self, body: dict) -> dict:
        request = urllib.request.Request(GATEWAY_URL, method="POST",
            data=json.dumps(body, allow_nan=False).encode(),
            headers={"Authorization": "Bearer " + self._token, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            raise ValueError(f"Daily-path gateway returned HTTP {exc.code}") from None
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise ValueError("Gateway did not confirm success")
        return result

    def export(self) -> dict:
        data = self.call({"action": "export"})
        if data.get("version") != "daily-inventory-gateway-source-export-v1" or data.get("production_change") is not False:
            raise ValueError("Gateway source export contract mismatch")
        as_of = parse_timestamp(data["exported_at"])
        if as_of > datetime.now(timezone.utc):
            raise ValueError("Gateway export cutoff is in the future")
        events = {}
        for event in data["events"]:
            identity = int(event["id"])
            if identity in events or not event.get("provider") or not event.get("club_slug"):
                raise ValueError("Invalid/duplicate gateway event identity")
            events[identity] = {"ticket_event_id": identity, "club_slug": event["club_slug"],
                "provider": event["provider"], "kickoff_at": parse_timestamp(event["kickoff_at"]).isoformat(),
                "observations": []}
        for snapshot in data["snapshots"]:
            event = events[int(snapshot["ticket_event_id"])]
            capture = parse_timestamp(snapshot["captured_at"])
            if capture > as_of:
                raise ValueError("Gateway snapshot exceeds export cutoff")
            event["observations"].append({"snapshot_id": int(snapshot["id"]),
                "captured_at": capture.isoformat(), "available_total": snapshot.get("available_total"),
                "measurement_key": f'{event["provider"]}/{snapshot["source"]}' if snapshot.get("source") else ""})
        result = {"version": "daily-inventory-public-export-v1", "exported_at": as_of.isoformat(),
            "events": list(events.values()), "production_change": False,
            "source_state_metadata_available": False, "source": "controlled_github_oidc_gateway"}
        result["export_sha256"] = canonical_hash(result)
        return result

    def capture(self, attempt: dict) -> dict:
        # Recompute pinned model outputs, source hashes and legal windows before
        # crossing the network. Remote SQL independently validates DB lineage.
        payload, _, _ = DailyInventoryPathLedger._validate(
            attempt["issue"], attempt["points"], attempt["artifact"], datetime.now(timezone.utc))
        return self.call({"action": "capture", "attempt": payload})

    def score(self) -> dict:
        return self.call({"action": "score"})

    def feed(self) -> dict:
        result = self.call({"action": "feed"}).get("feed")
        if (not isinstance(result, dict) or result.get("version") != "daily-inventory-path-preview-v1"
                or result.get("production_change") is not False
                or result.get("evidence_kind") != "research_preview_not_prospective"):
            raise ValueError("Remote feed contract mismatch")
        return result
