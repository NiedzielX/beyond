-- Exact-body guarded correctness patch; base PERS migration/manifest stay intact.
-- No arithmetic clock adjustment, table/row changes, model changes or cron edits.
do $patch$
declare
 v_body text;
 v_definition text;
 v_hash text;
 v_before text := $before$  issued:=clock_timestamp();
  src_age:=$before$;
 v_after text := $after$  issued:=clock_timestamp();
  -- Preserve the strict completion-before-issue clock contract at microsecond resolution.
  if issued<=calc_done then
   perform pg_catalog.pg_sleep(0.000001);
   issued:=clock_timestamp();
  end if;
  if issued<=calc_done then
   raise exception using errcode='40001', message='MVP_PERSISTENCE_CLOCK_DID_NOT_ADVANCE';
  end if;
  src_age:=$after$;
begin
 select p.prosrc,pg_get_functiondef(p.oid) into v_body,v_definition
 from pg_proc p where p.oid=to_regprocedure('public.issue_rolling72_mvp_persistence_v1(integer)');
 if v_body is null then raise exception 'PERS_CLOCK_GUARD_ISSUER_MISSING'; end if;
 v_hash:=encode(sha256(convert_to(v_body,'UTF8')),'hex');
 if v_hash='f7bc89911b5eddd3d44dd023c3e9af940ddb5ff9a6dcb65db673689fadad4874' then return; end if;
 if v_hash<>'fa0c5cfd9449e3b1fd6af5178e7853f1ae857f8b60c422cacb28d8e05f713750' then raise exception 'PERS_CLOCK_GUARD_UNEXPECTED_BODY'; end if;
 if (length(v_body)-length(replace(v_body,v_before,'')))/length(v_before)<>1 then
  raise exception 'PERS_CLOCK_GUARD_ANCHOR_MISMATCH';
 end if;
 execute replace(v_definition,v_before,v_after);
 select encode(sha256(convert_to(p.prosrc,'UTF8')),'hex') into v_hash
 from pg_proc p where p.oid='public.issue_rolling72_mvp_persistence_v1(integer)'::regprocedure;
 if v_hash is distinct from 'f7bc89911b5eddd3d44dd023c3e9af940ddb5ff9a6dcb65db673689fadad4874' then raise exception 'PERS_CLOCK_GUARD_PATCH_HASH_MISMATCH'; end if;
end
$patch$;
