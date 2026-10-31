-- Execute in Supabase SQL Editor. Each authenticated account owns only its own workspace.
create table if not exists public.user_workspaces (
  user_id uuid primary key references auth.users(id) on delete cascade,
  payload jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
alter table public.user_workspaces enable row level security;
revoke all on public.user_workspaces from anon;
grant select, insert, update, delete on public.user_workspaces to authenticated;
drop policy if exists workspace_select_own on public.user_workspaces;
drop policy if exists workspace_insert_own on public.user_workspaces;
drop policy if exists workspace_update_own on public.user_workspaces;
drop policy if exists workspace_delete_own on public.user_workspaces;
create policy workspace_select_own on public.user_workspaces for select to authenticated using ((select auth.uid()) = user_id);
create policy workspace_insert_own on public.user_workspaces for insert to authenticated with check ((select auth.uid()) = user_id);
create policy workspace_update_own on public.user_workspaces for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy workspace_delete_own on public.user_workspaces for delete to authenticated using ((select auth.uid()) = user_id);
