-- P9 prospective attempt registry service-role read permission v1.
-- The gateway invokes the non-SECURITY-DEFINER summary function as service_role,
-- so it needs read-only access to the private attempt evidence table.
-- No write privileges are granted; anon/authenticated remain denied.

grant select on private.p9_booking_curve_prospective_attempts_v1 to service_role;

revoke all on private.p9_booking_curve_prospective_attempts_v1 from anon;
revoke all on private.p9_booking_curve_prospective_attempts_v1 from authenticated;
