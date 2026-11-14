-- Hookclip data model (architecture §6). Run in the Supabase SQL editor
-- or `supabase db push`. The worker's local SQLite schema (app/db.py)
-- mirrors this exactly; the deploy swaps the backend, not the model.
-- Auth is Supabase Auth (users.id = auth.users id); the `users` table here
-- holds plan/credits only.

create table if not exists users (
  id uuid primary key,
  email text unique not null,
  plan text not null default 'free',
  credits integer not null default 60,
  created_at timestamptz not null default now()
);

create table if not exists projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id),
  source_url text not null,
  source_type text not null,
  title text,
  duration_sec double precision,
  status text not null default 'queued',
  created_at timestamptz not null default now()
);

create table if not exists jobs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id),
  kind text not null default 'process',
  clip_id uuid references clips(id),
  stage text not null default 'queued',
  progress double precision not null default 0,
  error text,
  attempts integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists transcripts (
  project_id uuid primary key references projects(id),
  segments_json jsonb not null,
  words_json jsonb not null
);

create table if not exists chat_windows (
  project_id uuid not null references projects(id),
  window_start double precision not null,
  msg_count integer not null,
  velocity_ratio double precision not null,
  primary key (project_id, window_start)
);

create table if not exists moments (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id),
  start_sec double precision not null,
  end_sec double precision not null,
  signals_json jsonb not null,
  score integer not null default 0,
  score_reason text,
  created_at timestamptz not null default now()
);

create table if not exists hooks (
  id uuid primary key default gen_random_uuid(),
  moment_id uuid not null references moments(id),
  text text not null,
  rank integer not null
);

create table if not exists clips (
  id uuid primary key default gen_random_uuid(),
  moment_id uuid not null references moments(id),
  status text not null default 'draft',
  caption_style text not null default 'bold',
  hook_text text,
  trim_start double precision,
  trim_end double precision,
  export_path text,
  format text not null default '9:16',
  created_at timestamptz not null default now()
);

create table if not exists credit_ledger (
  id bigserial primary key,
  user_id uuid not null references users(id),
  delta integer not null,
  reason text not null,
  created_at timestamptz not null default now()
);

create table if not exists waitlist (
  id bigserial primary key,
  email text unique not null,
  role text,
  created_at timestamptz not null default now()
);

-- Row-level security: keep it simple in P0 — the worker uses the service
-- role key and enforces ownership in the API. Enable RLS per table at
-- deploy time if direct client access is ever added.
