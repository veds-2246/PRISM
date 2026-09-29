-- Review and apply manually. This migration is intentionally not executed by
-- the application or verification scripts.
--
-- RLS remains enabled. The policy permits an authenticated user to create
-- audit events only for that same authenticated user's UUID.
do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'audit_logs'
      and policyname = 'Users can insert own audit logs'
  ) then
    create policy "Users can insert own audit logs"
      on public.audit_logs
      for insert
      to authenticated
      with check (user_id = auth.uid());
  end if;
end
$$;
