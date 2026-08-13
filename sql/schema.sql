-- Team A storage layer: trials, drug labels, entities, provenance, vector index.
-- Applied automatically by docker-compose on first container start
-- (mounted into /docker-entrypoint-initdb.d). Re-runnable via `psql -f schema.sql`.

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- Raw payloads: every ingested record is stored here before any transform,
-- so normalization/backfill can be re-run without re-fetching.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_payloads (
    id              SERIAL PRIMARY KEY,
    source          TEXT NOT NULL CHECK (source IN ('clinicaltrials', 'openfda')),
    source_record_id TEXT NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    storage_backend TEXT NOT NULL CHECK (storage_backend IN ('local', 's3')),
    storage_path    TEXT NOT NULL,
    checksum        TEXT NOT NULL,
    UNIQUE (source, source_record_id, checksum)
);

-- ---------------------------------------------------------------------------
-- Canonical entities: one row per (drug|disease|target) canonical ID.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS entities (
    id              SERIAL PRIMARY KEY,
    entity_type     TEXT NOT NULL CHECK (entity_type IN ('drug', 'disease', 'target')),
    source_system   TEXT NOT NULL CHECK (source_system IN ('RXNORM', 'DRUGBANK', 'MONDO', 'MESH', 'HGNC')),
    source_id       TEXT NOT NULL,
    canonical_name  TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_type, source_system, source_id)
);

-- Cache of free-text -> entity resolutions, so normalize_* doesn't re-hit
-- external ontology APIs for strings it has already resolved.
CREATE TABLE IF NOT EXISTS entity_aliases (
    id              SERIAL PRIMARY KEY,
    entity_type     TEXT NOT NULL CHECK (entity_type IN ('drug', 'disease', 'target')),
    alias_text      TEXT NOT NULL,
    entity_id       INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    confidence      NUMERIC(4,3) NOT NULL,
    resolved_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_type, alias_text)
);

-- ---------------------------------------------------------------------------
-- Trials (ClinicalTrials.gov)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trials (
    nct_id              TEXT PRIMARY KEY,
    title               TEXT,
    condition_text      TEXT[] NOT NULL DEFAULT '{}',
    intervention_text   TEXT[] NOT NULL DEFAULT '{}',
    phase               TEXT,
    status              TEXT,
    why_stopped         TEXT,
    enrollment_count    INTEGER,
    eligibility_text    TEXT,
    sponsor             TEXT,
    locations           JSONB NOT NULL DEFAULT '[]',
    embedding           vector(384),
    raw_payload_id      INTEGER REFERENCES raw_payloads(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trial_conditions (
    trial_nct_id TEXT NOT NULL REFERENCES trials(nct_id) ON DELETE CASCADE,
    entity_id    INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    PRIMARY KEY (trial_nct_id, entity_id)
);

CREATE TABLE IF NOT EXISTS trial_interventions (
    trial_nct_id TEXT NOT NULL REFERENCES trials(nct_id) ON DELETE CASCADE,
    entity_id    INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    PRIMARY KEY (trial_nct_id, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_trials_status ON trials(status);
CREATE INDEX IF NOT EXISTS idx_trials_phase ON trials(phase);
CREATE INDEX IF NOT EXISTS idx_trial_conditions_entity ON trial_conditions(entity_id);
CREATE INDEX IF NOT EXISTS idx_trial_interventions_entity ON trial_interventions(entity_id);

-- HNSW index for semantic similarity search over trial text.
CREATE INDEX IF NOT EXISTS idx_trials_embedding_hnsw
    ON trials USING hnsw (embedding vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- Drug labels (openFDA)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS drug_labels (
    id              SERIAL PRIMARY KEY,
    drug_id         INTEGER REFERENCES entities(id),
    brand_name      TEXT,
    generic_name    TEXT,
    condition_id    INTEGER REFERENCES entities(id),
    label_text      TEXT,
    mechanism_text  TEXT,
    approval_date   DATE,
    embedding       vector(384),
    raw_payload_id  INTEGER REFERENCES raw_payloads(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_drug_labels_drug_id ON drug_labels(drug_id);
CREATE INDEX IF NOT EXISTS idx_drug_labels_condition_id ON drug_labels(condition_id);
CREATE INDEX IF NOT EXISTS idx_drug_labels_embedding_hnsw
    ON drug_labels USING hnsw (embedding vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- Provenance: derived_claim_id -> source_record_id[]. This is what makes
-- every other team's outputs citable back to a raw source payload.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provenance (
    id                  SERIAL PRIMARY KEY,
    derived_claim_id    TEXT NOT NULL,
    source_record_type  TEXT NOT NULL CHECK (source_record_type IN ('clinicaltrials', 'openfda')),
    source_record_id    TEXT NOT NULL,
    raw_payload_id       INTEGER REFERENCES raw_payloads(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_provenance_claim ON provenance(derived_claim_id);
