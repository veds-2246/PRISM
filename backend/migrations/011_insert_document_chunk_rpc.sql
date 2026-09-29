-- Review and apply manually. This migration is intentionally not executed by
-- the application or verification scripts.
--
-- Insert document chunks only for documents owned through the caller's analysis.
create or replace function public.insert_document_chunk(
  p_document_id uuid,
  p_chunk_index integer,
  p_content text,
  p_page_number integer default null,
  p_token_count integer default null
)
returns setof public.document_chunks
language plpgsql
security definer
set search_path = public
as $$
begin
  if not exists (
    select 1
    from public.uploaded_documents as document
    join public.analyses as analysis
      on analysis.id = document.analysis_id
    where document.id = p_document_id
      and analysis.user_id = auth.uid()
  ) then
    raise exception 'Document does not belong to the authenticated user'
      using errcode = '42501';
  end if;

  return query
  insert into public.document_chunks (
    document_id,
    chunk_index,
    content,
    page_number,
    token_count
  )
  values (
    p_document_id,
    p_chunk_index,
    p_content,
    p_page_number,
    p_token_count
  )
  returning *;
end;
$$;

revoke all on function public.insert_document_chunk(uuid, integer, text, integer, integer) from public;
grant execute on function public.insert_document_chunk(uuid, integer, text, integer, integer) to authenticated;
