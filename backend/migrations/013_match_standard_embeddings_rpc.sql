-- Review and apply manually. This migration is intentionally not executed by
-- the application or verification scripts.
--
-- Read-only semantic retrieval for standard embeddings.
create or replace function public.match_standard_embeddings(
  query_embedding vector(768),
  match_count integer,
  p_embedding_model text
)
returns table (
  standard_id uuid,
  standard_version_id uuid,
  similarity_score double precision
)
language plpgsql
security definer
set search_path = public
as $$
begin
  if match_count is null or match_count < 1 or match_count > 20 then
    raise exception 'match_count must be between 1 and 20'
      using errcode = '22023';
  end if;

  return query
  select
    embeddings.standard_id,
    embeddings.standard_version_id,
    1 - (embeddings.embedding <=> query_embedding) as similarity_score
  from public.embeddings as embeddings
  where embeddings.standard_id is not null
    and embeddings.embedding_model = p_embedding_model
  order by embeddings.embedding <=> query_embedding
  limit match_count;
end;
$$;

revoke all on function public.match_standard_embeddings(vector(768), integer, text) from public;
grant execute on function public.match_standard_embeddings(vector(768), integer, text) to authenticated;
