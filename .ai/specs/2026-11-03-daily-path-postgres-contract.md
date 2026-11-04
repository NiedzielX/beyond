# Daily path PostgreSQL contract validation

Status: specified before implementation. Dependency: prepared `supabase/sql/daily_inventory_path_shadow_v1.sql`.

Run the real migration in a disposable PostgreSQL16GitHub Actions service, with minimal synthetic `ticket_events`/`snapshots` scaffolding and browser/service roles. Never connect this test to the production database or use production credentials.

Verify registered artifact identity, legal capture, exact retries, conflicting retries, complete target leads, atomic rollback, source lineage, window/production/target-use rejection, private table permissions, immutable updates/deletes, genuine zero target matching, no future target use, and idempotent scoring/feed. Synthetic historical scoring fixtures in this isolated database are tests only; they are never prospective evidence or historical backfill.

Correct actual migration defects found by these tests while preserving the frozen Python model/parameters, all existing lanes and the prepared lane's capture/scoring semantics. Passing isolated SQL checks is distinct from Deno/OIDC gateway execution and production DB deployment. Keep the new scheduled live workflow disabled.
