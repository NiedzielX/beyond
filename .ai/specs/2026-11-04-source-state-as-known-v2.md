# Independent source-state feature contract v2

The current daily model cannot see original active/visible-stage metadata or source receipt times. Existing private Stellis raw observations already preserve those fields; fresh read-only audit reconfirmed hidden/null Korona versus explicit-zero Widzew. This is a concrete new information family without partner sales data.

Prepare a separate service-role-only read-only RPC over existing raw rows. Require event creation, source capture and source creation no later than the requested pre-match cutoff; never expose a later promotion link as if known then. Preserve explicit visible0, distinguish active=false/hidden from unknown/malformed metadata, and never mutate raw/public snapshots, promotion rules or frozen v1 inputs. Output source/evidence lineage and honest immutability/identity limits. Future/private metadata must not become historical features.

Acceptance: actual isolated PostgreSQL tests cover bitemporal/event/future cutoffs, zero/hidden/inactive/legacy/invalid flags, late promotion-link masking, role denial and non-mutation. No model fitting, v1 rewiring, live SQL deployment or claim of historical prospective backfill. Add this new information contract to the plan only as prepared research infrastructure for a separately precommitted experiment.
