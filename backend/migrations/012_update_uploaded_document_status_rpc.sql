-- Review and apply manually. This migration is intentionally not executed by
-- the application or verification scripts.
--
-- Update document processing state only for documents owned through the
-- caller's analysis.
create or replace function public.update_uploaded_document_status(
  p_document_id uuid,
  p_status document_status,
  p_extracted_text text default null,
  p_ocr_used boolean default null,
  p_ocr_confidence double precision default null,
  p_processing_error text default null
)
returns setof public.uploaded_documents
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
  update public.uploaded_documents
  set status = p_status,
      extracted_text = coalesce(p_extracted_text, extracted_text),
      ocr_used = coalesce(p_ocr_used, ocr_used),
      ocr_confidence = coalesce(p_ocr_confidence, ocr_confidence),
      processing_error = p_processing_error
  where id = p_document_id
  returning *;
end;
$$;

revoke all on function public.update_uploaded_document_status(
  uuid, document_status, text, boolean, double precision, text
) from public;
grant execute on function public.update_uploaded_document_status(
  uuid, document_status, text, boolean, double precision, text
) to authenticated;
