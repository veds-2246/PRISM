-- Review and apply manually. This migration is intentionally not executed by
-- the application or verification scripts.
--
-- The RPC performs the ownership check explicitly, then inserts on behalf of
-- the authenticated user while keeping RLS enabled on the base table.
create or replace function public.insert_extracted_requirements(
  p_analysis_id uuid,
  p_requirements jsonb
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if not exists (
    select 1
    from public.analyses as analysis
    where analysis.id = p_analysis_id
      and analysis.user_id = auth.uid()
  ) then
    raise exception 'Analysis does not belong to the authenticated user'
      using errcode = '42501';
  end if;

  insert into public.extracted_requirements (
    analysis_id,
    requirement_type,
    requirement_value
  )
  select
    p_analysis_id,
    requirement->>'requirement_type',
    requirement->>'requirement_value'
  from jsonb_array_elements(p_requirements) as requirement;
end;
$$;

revoke all on function public.insert_extracted_requirements(uuid, jsonb) from public;
grant execute on function public.insert_extracted_requirements(uuid, jsonb) to authenticated;
