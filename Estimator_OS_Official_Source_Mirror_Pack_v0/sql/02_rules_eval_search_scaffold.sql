-- Estimator.OS first-pass scaffold additions
-- Purpose:
-- 1) Persist rule compiler artifacts and rule evaluation snapshots.
-- 2) Provide search read-model table/indexes for evaluations and import runs.
-- 3) Keep everything additive and decoupled from published estimate mutation paths.

create extension if not exists pg_trgm;
create extension if not exists pgcrypto;

create table if not exists rule_compile_artifact (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    rule_id text not null,
    rule_code text not null,
    template_version text not null,
    schema_version text not null,
    compiler_version text not null,
    normalization_version text not null default 'seed-pack-v0.1.0',
    canonical_json jsonb not null,
    compiled_jsonlogic jsonb not null,
    canonical_sha256 text not null,
    compile_hash text not null,
    source_yaml text null,
    source_manifest_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (organization_id, rule_code, template_version, compile_hash)
);

create index if not exists idx_rule_compile_artifact_rule
    on rule_compile_artifact (organization_id, rule_code, template_version);

create table if not exists rule_evaluation_snapshot (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    evaluation_id text not null,
    rule_id text not null,
    template_version text not null,
    compile_hash text not null,
    evaluation_hash text not null,
    effective_date date not null,
    status text not null check (status in ('generated','warning','blocked','confirmed','overridden','not_applicable')),
    input_snapshot jsonb not null default '{}'::jsonb,
    output_snapshot jsonb not null default '{}'::jsonb,
    confirmations jsonb not null default '[]'::jsonb,
    overrides jsonb not null default '[]'::jsonb,
    evaluated_at timestamptz not null,
    created_at timestamptz not null default now(),
    unique (organization_id, evaluation_hash)
);

create index if not exists idx_rule_evaluation_snapshot_rule
    on rule_evaluation_snapshot (organization_id, rule_id, template_version, evaluated_at desc);

create index if not exists idx_rule_evaluation_snapshot_status
    on rule_evaluation_snapshot (organization_id, status, evaluated_at desc);

create table if not exists search_documents (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    object_type text not null,
    object_id text not null,
    title text not null,
    subtitle text null,
    body_text text null,
    search_key text not null,
    facets_json jsonb not null default '{}'::jsonb,
    payload_json jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now(),
    tsv tsvector generated always as (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(subtitle, '') || ' ' || coalesce(body_text, ''))
    ) stored,
    unique (organization_id, object_type, object_id)
);

create index if not exists idx_search_documents_tsv
    on search_documents using gin (tsv);

create index if not exists idx_search_documents_trgm
    on search_documents using gin (search_key gin_trgm_ops);

create index if not exists idx_search_documents_scope
    on search_documents (organization_id, object_type, updated_at desc);
