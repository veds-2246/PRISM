-- Review and apply manually. This migration is intentionally not executed by
-- the application or verification scripts.
--
-- RLS remains enabled. The policy permits evidence inserts only when the
-- recommendation belongs to an analysis owned by the authenticated user.
do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'recommendation_evidence'
      and policyname = 'Users can insert evidence for own recommendations'
  ) then
    create policy "Users can insert evidence for own recommendations"
      on public.recommendation_evidence
      for insert
      to authenticated
      with check (
        exists (
          select 1
          from public.recommendations as recommendation
          join public.analyses as analysis
            on analysis.id = recommendation.analysis_id
          where recommendation.id = recommendation_evidence.recommendation_id
            and analysis.user_id = auth.uid()
        )
      );
  end if;
end
$$;
