from copy import deepcopy
import io
import json
import unittest
from unittest.mock import patch
import urllib.error

from ml.demand_engine.daily_inventory_path_gateway_v1 import DailyInventoryPathGateway, GATEWAY_URL
from ml.demand_engine.daily_inventory_path_dataset_v1 import canonical_hash


class GatewayClientTest(unittest.TestCase):
    def client(self):
        return DailyInventoryPathGateway("synthetic-oidc-not-a-secret")

    def fixture(self):
        return {"ok": True, "version": "daily-inventory-gateway-source-export-v1",
            "production_change": False, "exported_at": "2026-11-03T12:00:00Z",
            "events": [{"id": 1, "club_slug": "test", "provider": "public", "kickoff_at": "2026-11-10T12:00:00Z"}],
            "snapshots": [{"id": 5, "ticket_event_id": 1, "captured_at": "2026-11-03T11:00:00Z",
                           "available_total": 0, "source": "inventory-v1"}]}

    def test_read_only_source_conversion_preserves_zero_source_and_hash(self):
        client = self.client()
        with patch.object(client, "call", return_value=self.fixture()) as call:
            data = client.export()
        call.assert_called_once_with({"action": "export"})
        obs = data["events"][0]["observations"][0]
        self.assertEqual(obs["available_total"], 0)
        self.assertEqual(obs["measurement_key"], "public/inventory-v1")
        self.assertEqual(data["export_sha256"], canonical_hash({k:v for k,v in data.items() if k!="export_sha256"}))

    def test_future_snapshot_or_wrong_source_contract_is_rejected(self):
        for field, value in [("production_change", True), ("version", "wrong")]:
            data = self.fixture(); data[field] = value
            client = self.client()
            with patch.object(client, "call", return_value=data), self.assertRaises(ValueError):
                client.export()
        data = self.fixture()
        data["snapshots"][0]["captured_at"] = "2026-11-03T12:00:01Z"
        client = self.client()
        with patch.object(client, "call", return_value=data), self.assertRaises(ValueError):
            client.export()

    def test_request_uses_pinned_destination_and_never_reveals_server_error_body(self):
        response = io.BytesIO(b'{"ok":true,"result":{}}')
        with patch("urllib.request.urlopen", return_value=response) as request:
            self.client().score()
        req = request.call_args.args[0]
        self.assertEqual(req.full_url, GATEWAY_URL)
        self.assertEqual(req.method, "POST")
        failure = urllib.error.HTTPError(GATEWAY_URL, 403, "sensitive response", {}, None)
        with patch("urllib.request.urlopen", side_effect=failure), self.assertRaisesRegex(ValueError, "HTTP 403") as raised:
            self.client().score()
        self.assertNotIn("synthetic-oidc", str(raised.exception))
        self.assertNotIn("sensitive", str(raised.exception))

    def test_unconfirmed_response_or_mismatched_feed_fails_closed(self):
        with patch("urllib.request.urlopen", return_value=io.BytesIO(b'{"ok":false}')), self.assertRaises(ValueError):
            self.client().score()
        client = self.client()
        with patch.object(client, "call", return_value={"feed": {"version": "wrong"}}), self.assertRaises(ValueError):
            client.feed()

    def test_invalid_capture_is_rejected_before_any_network_call(self):
        client = self.client()
        with patch.object(client, "call") as call, self.assertRaises((ValueError, KeyError)):
            client.capture({"issue": {}, "points": [], "artifact": {}})
        call.assert_not_called()

    def test_token_required(self):
        with self.assertRaises(ValueError):
            DailyInventoryPathGateway("")


if __name__ == "__main__":
    unittest.main()
