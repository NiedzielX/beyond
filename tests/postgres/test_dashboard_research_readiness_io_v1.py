"""Isolated parity tests for key-only dashboard readiness aggregation."""
from __future__ import annotations

import os
from pathlib import Path
import unittest
from urllib.parse import urlparse

import psycopg


ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / "supabase/ops/dashboard_research_readiness_io_v1.sql"
DB_NAME = "dashboard_research_readiness_io_v1_test"


class DashboardResearchReadinessIOV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get("DASHBOARD_READINESS_IO_V1_TEST_DSN", "")
        target = urlparse(dsn)
        if (target.scheme not in {"postgres", "postgresql"}
                or target.hostname not in {"127.0.0.1", "localhost"}
                or target.port != 55440 or target.path != f"/{DB_NAME}"):
            raise RuntimeError(
                f"Only an isolated loopback PostgreSQL16 {DB_NAME} database is allowed"
            )
        cls.db = psycopg.connect(dsn, autocommit=True)
        version = int(cls.db.execute("show server_version_num").fetchone()[0])
        if not 160000 <= version < 170000:
            cls.db.close()
            raise RuntimeError("Dashboard readiness parity tests require PostgreSQL 16")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            cls.db.close()

    def setUp(self):
        self.db.execute("drop function if exists public.get_dashboard_ml_readiness_safe_v1() cascade")
        self.db.execute("drop function if exists public.get_live_signal_study_readiness_v1() cascade")
        self.db.execute("drop function if exists public.get_dashboard_research_readiness_v2() cascade")
        self.db.execute("drop function if exists public.get_multiclub_feature_store_v2() cascade")
        self.db.execute("drop function if exists public.get_model_lab_rows_v1() cascade")
        self.db.execute("drop function if exists public.get_weather_feature_store_v1() cascade")
        self.db.execute("drop function if exists private.dashboard_multiclub_feature_keys_v1() cascade")
        for view in (
            "crossclub_live_signal_study_rows_v2", "live_signal_study_rows_v1",
            "multiclub_feature_store_v4", "multiclub_feature_store_v3",
        ):
            self.db.execute(f"drop view if exists public.{view} cascade")
        for table in (
            "crossclub_baseline_rows_v2", "model_lab_test_rows", "weather_feature_keys",
            "ticket_event_inventory_reference", "ticket_event_outcomes", "snapshots", "ticket_events",
        ):
            self.db.execute(f"drop table if exists public.{table} cascade")
        self.db.execute("create schema if not exists private")
        for role in ("anon", "authenticated", "service_role"):
            if not self.db.execute("select 1 from pg_roles where rolname=%s", (role,)).fetchone():
                self.db.execute(f'create role "{role}" nologin')
        self._create_fixture_schema()
        self._create_old_feature_and_readiness_functions()
        self._seed()
        self.old_keys = self._query_keys("public.get_multiclub_feature_store_v2()")
        self.old_live = self.db.execute(
            "select * from public.get_live_signal_study_readiness_v1()"
        ).fetchone()
        self.old_ml = self.db.execute(
            "select * from public.get_dashboard_ml_readiness_safe_v1()"
        ).fetchone()
        self.old_research = self.db.execute(
            "select * from public.get_dashboard_research_readiness_v2()"
        ).fetchone()
        self.old_protected_bodies = self._protected_bodies()
        self.old_acl = self._readiness_acl()

    def _create_fixture_schema(self):
        self.db.execute("""
          create table public.ticket_events(
            id bigint primary key, club_slug text not null, kickoff_at timestamptz,
            competition text not null
          );
          create table public.snapshots(
            id bigint primary key, ticket_event_id bigint not null,
            captured_at timestamptz not null, available_total integer
          );
          create index snapshots_ticket_event_captured_test_idx
            on public.snapshots(ticket_event_id,captured_at);
          create table public.ticket_event_outcomes(
            ticket_event_id bigint primary key, actual_attendance integer
          );
          create table public.crossclub_baseline_rows_v2(
            ticket_event_id bigint primary key, club_slug text not null
          );
          create table public.model_lab_test_rows(
            ticket_event_id bigint not null, horizon text not null,
            model_version text not null, historical_p50 integer
          );
          create table public.ticket_event_inventory_reference(
            ticket_event_id bigint not null, reference_type text not null,
            reference_value integer, primary key(ticket_event_id,reference_type)
          );
          create table public.weather_feature_keys(
            ticket_event_id bigint not null, horizon text not null,
            primary key(ticket_event_id,horizon)
          );
          grant select on all tables in schema public to service_role;
        """)

    def _create_old_feature_and_readiness_functions(self):
        self.db.execute("""
          create function public.get_multiclub_feature_store_v2()
          returns table(ticket_event_id bigint,club_slug text,horizon text,snapshot_id bigint)
          language sql stable set search_path to 'public' as $old$
          with horizons(label,target_hours,tolerance_hours,ord) as (
            values ('T-30'::text,720.0::numeric,240.0::numeric,1),
                   ('T-14',336.0,96.0,2),('T-7',168.0,48.0,3),
                   ('T-3',72.0,24.0,4),('T-24h',24.0,12.0,5)
          ), candidates as (
            select te.id ticket_event_id,te.club_slug,h.label horizon,s.id snapshot_id,
              row_number() over(partition by te.id,h.label order by
                (extract(epoch from (te.kickoff_at-s.captured_at))/3600.0-h.target_hours) asc,
                s.captured_at desc,s.id desc) rn
            from public.ticket_events te join public.snapshots s on s.ticket_event_id=te.id
            cross join horizons h
            where te.kickoff_at is not null and s.available_total is not null
              and s.captured_at<=te.kickoff_at
              and extract(epoch from (te.kickoff_at-s.captured_at))/3600.0>=h.target_hours
              and extract(epoch from (te.kickoff_at-s.captured_at))/3600.0<=h.target_hours+h.tolerance_hours
          )
          select ticket_event_id,club_slug,horizon,snapshot_id from candidates where rn=1
          $old$;

          create function public.get_weather_feature_store_v1()
          returns table(ticket_event_id bigint,horizon text)
          language sql stable set search_path to 'public' as $old$
            select ticket_event_id,horizon from public.weather_feature_keys
          $old$;

          create function public.get_model_lab_rows_v1()
          returns table(ticket_event_id bigint,horizon text,model_version text,historical_p50 integer)
          language sql stable set search_path to 'public' as $old$
            select ticket_event_id,horizon,model_version,historical_p50 from public.model_lab_test_rows
          $old$;

          create view public.multiclub_feature_store_v3 as
            select f.ticket_event_id,f.club_slug,f.horizon,f.snapshot_id
            from public.get_multiclub_feature_store_v2() f
            left join public.ticket_event_inventory_reference r
              on r.ticket_event_id=f.ticket_event_id and r.reference_type='public_seat_map_size';
          create view public.multiclub_feature_store_v4 as
            select f.* from public.multiclub_feature_store_v3 f
            left join public.get_weather_feature_store_v1() w
              on w.ticket_event_id=f.ticket_event_id and w.horizon=f.horizon;
          create view public.crossclub_live_signal_study_rows_v2 as
            select b.ticket_event_id,b.club_slug,f.horizon,f.snapshot_id
            from public.crossclub_baseline_rows_v2 b
            join public.multiclub_feature_store_v4 f on f.ticket_event_id=b.ticket_event_id;
          create view public.live_signal_study_rows_v1 as
            select ml.ticket_event_id,ml.model_version,ml.horizon
            from public.get_model_lab_rows_v1() ml
            join public.multiclub_feature_store_v3 f
              on f.ticket_event_id=ml.ticket_event_id and f.horizon=ml.horizon
            where ml.historical_p50 is not null;

          create function public.get_live_signal_study_readiness_v1()
          returns table(independent_outcome_events bigint,clubs_with_outcome bigint,
            strict_study_rows bigint,models_with_strict_rows bigint,cross_club_gate_met boolean,
            learned_correction_gate_met boolean,status text)
          language sql stable set search_path to 'public' as $old$
          with outcomes as (
            select count(distinct te.id)::bigint events,count(distinct te.club_slug)::bigint clubs
            from public.ticket_events te join public.ticket_event_outcomes o on o.ticket_event_id=te.id
            where o.actual_attendance is not null
          ), rows as (
            select count(*)::bigint study_rows,count(distinct model_version)::bigint models
            from public.live_signal_study_rows_v1
          )
          select o.events,o.clubs,r.study_rows,r.models,(o.events>=8 and o.clubs>=3),
            (o.events>=20),case when o.events<8 then 'collect_more_independent_outcomes'
             when o.clubs<3 then 'collect_more_club_outcomes'
             when o.events<20 then 'run_exploratory_cross_club_study_no_promotion'
             else 'eligible_for_grouped_live_residual_challenger_benchmark' end
          from outcomes o cross join rows r
          $old$;

          create function public.get_dashboard_ml_readiness_safe_v1()
          returns table(independent_outcome_events bigint,clubs_with_outcome bigint,
            strict_study_rows bigint,models_with_strict_rows bigint,cross_club_gate_met boolean,
            learned_correction_gate_met boolean,status text,cross_club_event_target integer,
            cross_club_club_target integer,learned_correction_event_target integer,generated_at timestamptz)
          language sql stable security definer set search_path to 'public' as $old$
            select r.independent_outcome_events,r.clubs_with_outcome,r.strict_study_rows,
             r.models_with_strict_rows,r.cross_club_gate_met,r.learned_correction_gate_met,r.status,
             8,3,20,now() from public.get_live_signal_study_readiness_v1() r
          $old$;

          create function public.get_dashboard_research_readiness_v2()
          returns table(crossclub_study_events bigint,crossclub_study_clubs bigint,strict_study_rows bigint,
            crossclub_gate_met boolean,crossclub_event_target integer,crossclub_club_target integer,
            independent_outcome_events_total bigint,outcome_clubs_total bigint,
            learned_correction_gate_met boolean,learned_correction_event_target integer,generated_at timestamptz)
          language sql stable security definer set search_path to 'public' as $old$
          with study as (
            select count(distinct ticket_event_id)::bigint events,
             count(distinct club_slug)::bigint clubs,count(*)::bigint rows
            from public.crossclub_live_signal_study_rows_v2
          ), outcomes as (
            select count(*)::bigint events,count(distinct e.club_slug)::bigint clubs
            from public.ticket_event_outcomes o join public.ticket_events e on e.id=o.ticket_event_id
          )
          select study.events,study.clubs,study.rows,study.events>=8 and study.clubs>=3,
            8,3,outcomes.events,outcomes.clubs,outcomes.events>=20,20,now()
          from study cross join outcomes
          $old$;
          revoke all on function public.get_live_signal_study_readiness_v1() from public,anon,authenticated;
          grant execute on function public.get_live_signal_study_readiness_v1() to service_role;
          revoke all on function public.get_dashboard_ml_readiness_safe_v1() from public,anon,authenticated;
          grant execute on function public.get_dashboard_ml_readiness_safe_v1() to service_role;
          revoke all on function public.get_dashboard_research_readiness_v2() from public,anon,authenticated;
          grant execute on function public.get_dashboard_research_readiness_v2() to service_role;
          revoke all on function public.get_multiclub_feature_store_v2() from public,anon,authenticated;
          grant execute on function public.get_multiclub_feature_store_v2() to service_role;
        """)

    def _seed(self):
        # Twenty outcome events across three clubs exercise the strict thresholds.
        events = []
        for event_id in range(1, 22):
            events.append((event_id, f"club-{(event_id - 1) % 3 + 1}",
                           "2026-12-10 20:00:00+00", "Ekstraklasa"))
        events += [(22, "club-1", None, "Ekstraklasa"),
                   (23, "club-2", "2026-12-10 20:00:00+00", "Ekstraklasa"),
                   (24, "club-3", "2026-12-10 20:00:00+00", "Ekstraklasa")]
        self.db.cursor().executemany(
            "insert into public.ticket_events values(%s,%s,%s,%s)", events
        )
        outcomes = [(i, 100 if i <= 20 else None) for i in range(1, 22)]
        self.db.cursor().executemany("insert into public.ticket_event_outcomes values(%s,%s)", outcomes)
        self.db.cursor().executemany(
            "insert into public.crossclub_baseline_rows_v2 values(%s,%s)",
            [(i, f"club-{(i - 1) % 3 + 1}") for i in range(1, 21)],
        )
        kickoff = "2026-12-10 20:00:00+00"
        eligible_hours = (720, 900, 336, 432, 168, 216, 72, 96, 24, 36)
        snapshots = []
        snapshot_id = 1
        for event_id in range(1, 20):
            for hours in eligible_hours:
                captured = self.db.execute(
                    "select (%s::timestamptz - (%s || ' hours')::interval)", (kickoff, hours)
                ).fetchone()[0]
                snapshots.append((snapshot_id, event_id, captured, 500))
                snapshot_id += 1
            if event_id == 1:
                # Exact hour tie: later snapshot ID must win, just like the live v2 selector.
                tied = self.db.execute(
                    "select (%s::timestamptz - interval '720 hours')", (kickoff,)
                ).fetchone()[0]
                snapshots.append((snapshot_id, event_id, tied, 500))
                snapshot_id += 1
        # Event 20 has only three horizons; event 21 only one. Event 23 is beyond
        # every tolerance; event 24 has a NULL total and must not qualify.
        for hours in (720, 336, 72):
            captured = self.db.execute(
                "select (%s::timestamptz - (%s || ' hours')::interval)", (kickoff, hours)
            ).fetchone()[0]
            snapshots.append((snapshot_id, 20, captured, 500)); snapshot_id += 1
        captured = self.db.execute(
            "select (%s::timestamptz - interval '720 hours')", (kickoff,)
        ).fetchone()[0]
        snapshots.append((snapshot_id, 21, captured, 500)); snapshot_id += 1
        captured = self.db.execute(
            "select (%s::timestamptz - interval '961 hours')", (kickoff,)
        ).fetchone()[0]
        snapshots.append((snapshot_id, 23, captured, 500)); snapshot_id += 1
        captured = self.db.execute(
            "select (%s::timestamptz - interval '720 hours')", (kickoff,)
        ).fetchone()[0]
        snapshots.append((snapshot_id, 24, captured, None))
        self.db.cursor().executemany("insert into public.snapshots values(%s,%s,%s,%s)", snapshots)
        self.db.cursor().executemany(
            "insert into public.ticket_event_inventory_reference values(%s,%s,%s)",
            [(i, "public_seat_map_size", 1000) for i in range(1, 22)],
        )
        feature_keys = self._query_keys("public.get_multiclub_feature_store_v2()")
        self.db.cursor().executemany(
            "insert into public.weather_feature_keys values(%s,%s)",
            [(event_id, horizon) for event_id, _club, horizon, _sid in feature_keys
             if (event_id + len(horizon)) % 2 == 0],
        )
        model_rows = [
            (1, "T-30", "model-a", 100), (1, "T-30", "model-b", 110),
            (1, "T-14", "model-null", None), (1, "T-24h", "model-d", 120),
            (21, "T-30", "model-e", 130), (22, "T-30", "model-no-feature", 140),
            (23, "T-30", "model-outside", 150), (24, "T-30", "model-null-total", 160),
        ]
        self.db.cursor().executemany("insert into public.model_lab_test_rows values(%s,%s,%s,%s)", model_rows)

    def _query_keys(self, source: str):
        return self.db.execute(f"select * from {source} order by 1,3").fetchall()

    def _protected_bodies(self):
        rows = self.db.execute("""
          select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),
            md5(pg_get_functiondef(p.oid))
          from pg_proc p join pg_namespace n on n.oid=p.pronamespace
          where (n.nspname='public' and p.proname in
            ('get_multiclub_feature_store_v2','get_model_lab_rows_v1',
             'get_weather_feature_store_v1','get_dashboard_ml_readiness_safe_v1'))
          order by 1,2,3
        """).fetchall()
        return rows

    def _readiness_acl(self):
        return self.db.execute("""
          select p.oid::regprocedure::text,coalesce(array_agg(acl.grantee order by acl.grantee),'{}')
          from pg_proc p
          cross join lateral aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) acl
          where p.oid in (
            'public.get_live_signal_study_readiness_v1()'::regprocedure,
            'public.get_dashboard_research_readiness_v2()'::regprocedure,
            'public.get_dashboard_ml_readiness_safe_v1()'::regprocedure
          ) and acl.privilege_type='EXECUTE'
          group by p.oid order by p.oid::regprocedure::text
        """).fetchall()

    def test_candidate_keys_and_both_readiness_paths_are_result_equivalent(self):
        if not SQL.exists():
            self.fail(f"Missing optimization SQL draft: {SQL}")
        self.db.execute(SQL.read_text(encoding="utf-8"))

        new_keys = self._query_keys("private.dashboard_multiclub_feature_keys_v1()")
        self.assertEqual(new_keys, self.old_keys)
        self.assertEqual(len(new_keys), len({(r[0], r[2]) for r in new_keys}))
        # The duplicate exact-horizon snapshot selects the greatest snapshot ID.
        event_one_t30 = [r for r in new_keys if r[0] == 1 and r[2] == "T-30"]
        self.assertEqual(len(event_one_t30), 1)
        tied_ids = [r[0] for r in self.db.execute(
            "select id from public.snapshots where ticket_event_id=1 and "
            "captured_at=(select min(captured_at) from public.snapshots where ticket_event_id=1 "
            "and captured_at=(select kickoff_at-interval '720 hours' from public.ticket_events where id=1))"
        ).fetchall()]
        self.assertTrue(tied_ids)
        self.assertEqual(event_one_t30[0][3], max(tied_ids))

        new_live = self.db.execute(
            "select * from public.get_live_signal_study_readiness_v1()"
        ).fetchone()
        new_ml = self.db.execute(
            "select * from public.get_dashboard_ml_readiness_safe_v1()"
        ).fetchone()
        new_research = self.db.execute(
            "select * from public.get_dashboard_research_readiness_v2()"
        ).fetchone()
        self.assertEqual(new_live, self.old_live)
        self.assertEqual(new_ml[:-1], self.old_ml[:-1])
        self.assertEqual(new_research[:-1], self.old_research[:-1])
        self.assertEqual(new_live[0:2], (20, 3))
        self.assertTrue(new_live[4] and new_live[5])
        self.assertEqual(new_research[:3], (20, 3, len([r for r in new_keys if r[0] <= 20])))
        self.assertTrue(new_research[3] and new_research[8])

        self.assertEqual(self._protected_bodies(), self.old_protected_bodies)
        self.assertEqual(self._readiness_acl(), self.old_acl)
        helper = self.db.execute("""
          select prosecdef,provolatile,coalesce(proconfig,'{}')
          from pg_proc where oid='private.dashboard_multiclub_feature_keys_v1()'::regprocedure
        """).fetchone()
        self.assertEqual(helper[0:2], (True, "s"))
        self.assertIn('search_path=""', helper[2])
        for role in ("anon", "authenticated"):
            self.assertFalse(self.db.execute(
                "select has_function_privilege(%s,'private.dashboard_multiclub_feature_keys_v1()','execute')",
                (role,),
            ).fetchone()[0])
        self.assertTrue(self.db.execute(
            "select has_function_privilege('service_role','private.dashboard_multiclub_feature_keys_v1()','execute')"
        ).fetchone()[0])

        helper_plan = "\n".join(row[0] for row in self.db.execute(
            "explain (verbose,costs,format text) select * from private.dashboard_multiclub_feature_keys_v1()"
        ).fetchall())
        self.assertNotIn("get_multiclub_feature_store_v2", helper_plan)
        self.assertNotIn("get_live_features_v1_asof", helper_plan)
        self.assertNotIn("get_weather_feature_store_v1", helper_plan)


if __name__ == "__main__":
    unittest.main()
