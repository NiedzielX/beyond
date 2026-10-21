#!/usr/bin/env python3
from __future__ import annotations

from ml.d2_long_horizon_coverage_audit_v1 import audit


def payload() -> dict:
    rows=[]
    coverage=[]
    for event_id, hours in {
        1:[6,30,54,78],
        2:[6,30,54],
        3:[6,30],
    }.items():
        for h in hours:
            rows.append({
                "ticket_event_id":event_id,
                "bucket_6h":int(h//6),
                "hours_to_kickoff":h,
                "features":{"point_in_time_validated":True,"snapshot_id":event_id*100+int(h)},
            })
        coverage.append({
            "ticket_event_id":event_id,
            "valid_row_count":len(hours),
            "rows_0_24h":sum(0<=h<=24 for h in hours),
            "rows_24_48h":sum(24<h<=48 for h in hours),
            "rows_48_72h":sum(48<h<=72 for h in hours),
            "rows_72_168h":sum(72<h<=168 for h in hours),
        })
    return {
        "ok":True,
        "version":"d2-long-horizon-168-rows-v1",
        "eventCount":3,
        "liveRowCount":len(rows),
        "sampling":{"window_hours":168,"cadence_hours":6},
        "coverage":coverage,
        "liveRows":rows,
    }


def main() -> None:
    result=audit(payload())
    assert result["coverage"]["events_with_rows_beyond_24h"] == 3
    assert result["coverage"]["events_with_rows_beyond_48h"] == 2
    assert result["coverage"]["events_with_rows_beyond_72h"] == 1
    assert result["readiness"]["max_window_ready_for_learned_model_v1_hours"] == 24
    assert result["decision"] == "INSUFFICIENT_EARLY_EVENT_COVERAGE"
    print("d2 long-horizon coverage audit unit checks: PASS")


if __name__ == "__main__":
    main()
