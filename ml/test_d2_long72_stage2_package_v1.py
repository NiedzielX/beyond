#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

MANIFEST = Path("ml/artifacts/d2_long72_stage2_p2_v1/manifest.json")


def main() -> None:
    payload = json.loads(MANIFEST.read_text())

    assert payload["package_id"] == "d2-long72-stage2-p2-observation-maturity-2026-10-21-v1"
    assert payload["status"] == "FROZEN_HISTORICAL_RESEARCH_PACKAGE"
    assert payload["production_allowed"] is False
    assert payload["prospective_evidence_required"] is True

    scope = payload["scope"]
    assert scope["hours_to_kickoff"] == {"lower_exclusive": 24, "upper_inclusive": 72}
    assert scope["historical_event_count"] == 13
    assert scope["historical_row_count"] == 80
    assert scope["evidence_class"] == "EXPOSED_HISTORICAL_R_AND_D"

    assert payload["stage1_expert"]["id"] == "inventory-linear-extrapolation"
    assert payload["stage2_reliability"]["policy_id"] == "P2-observation-maturity"
    assert payload["stage2_reliability"]["observation_weights"] == {
        "first_observation": 0.25,
        "second_observation": 0.6,
        "third_and_later": 1.0,
    }
    assert payload["stage2_reliability"]["time_to_kickoff_weights"] == {
        "60_72h": 0.75,
        "48_60h": 0.9,
        "24_48h": 1.0,
    }
    assert payload["stage2_reliability"]["outcome_labels_allowed_in_policy_logic"] is False

    assert payload["frozen_long72_input"]["artifact_id"] == 12365352293
    assert payload["frozen_long72_input"]["dataset_csv_sha256"] == "2af6209484e7120f08541d82bc7bcd064b0f9ea46dd59bb5e7d2746cb35a214c"
    assert payload["stage1_evidence"]["artifact_id"] == 12365399256
    assert payload["stage1_evidence"]["predictions_csv_sha256"] == "33de331d2c3bf1e385f513c7fa7e28aa8b454a4d49cfe00d48163e6c083a6df5"
    assert payload["stage2_evidence"]["artifact_id"] == 12366826274
    assert payload["stage2_evidence"]["json_sha256"] == "a9daa834e15b4f313b15c3e809033b7d79e4ed4357f61a8f5071e6bf20359d8c"
    assert payload["stage2_evidence"]["predictions_csv_sha256"] == "489ba62156f19d3b915fda1b9f1ef506fb81603d4286a01e8ad4b799c58bce4b"
    assert payload["stage2_evidence"]["selected_policy_id"] == "P2-observation-maturity"

    overall = payload["historical_metrics"]["overall_24_72h"]
    assert overall["anchor_mae"] == 3707.138173646611
    assert overall["stage1_raw_inventory_mae"] == 3254.6809517243155
    assert overall["package_mae"] == 3012.62892731916
    assert overall["package_mae_improvement_vs_anchor"] == 694.5092463274509
    assert overall["event_improvement_rate"] == 0.6153846153846154
    assert overall["worst_event_degradation"] == 1488.344647038306

    band = payload["historical_metrics"]["band_48_72h"]
    assert band["package_mae"] == 3927.674049897368
    assert band["mae_improvement"] == 664.7091810676761
    assert band["event_improvement_rate"] == 0.7

    stability = payload["historical_metrics"]["stability"]
    assert stability["original_exposed_subset_mae_improvement"] > 0
    assert stability["later_exposed_subset_mae_improvement"] > 0

    assert payload["next"] == "forward scoring without retuning"
    print("d2 long72 Stage2 P2 package seal checks: PASS")


if __name__ == "__main__":
    main()
