-- Review and apply manually. This migration is intentionally not executed by
-- the application or verification scripts.
--
-- Insert uploaded document metadata only for an analysis owned by the caller.
create or replace function public.insert_uploaded_document(
  p_analysis_id uuid,
  p_file_name text,
  p_file_type text,
  p_file_size integer
)
returns setof public.uploaded_documents
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

  return query
  insert into public.uploaded_documents (
    analysis_id,
    uploaded_by,
    file_name,
    file_type,
    status,
    file_size
  )
  values (
    p_analysis_id,
    auth.uid(),
    p_file_name,
    p_file_type,
    'processing',
    p_file_size
  )
  returning *;
end;
$$;

revoke all on function public.insert_uploaded_document(uuid, text, text, integer) from public;
grant execute on function public.insert_uploaded_document(uuid, text, text, integer) to authenticated;
