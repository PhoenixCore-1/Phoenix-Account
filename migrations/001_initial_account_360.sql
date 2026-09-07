-- Phoenix Account 360 V1.0
-- Migration 001: initial Account 360 owned persistence model.
-- Keep this migration aligned with schema.sql for the V1.0 baseline.

PRAGMA foreign_keys = ON;

CREATE TABLE account_360_accounts (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    record_status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (record_status IN ('ACTIVE', 'INACTIVE', 'ARCHIVED')),
    display_name TEXT,
    search_name TEXT,
    source_version TEXT,
    source_updated_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (tenant_id, account_id),
    UNIQUE (tenant_id, id)
);

CREATE INDEX idx_a360_accounts_tenant_display
    ON account_360_accounts (tenant_id, display_name);

CREATE TABLE account_360_source_references (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    source_module TEXT NOT NULL,
    source_entity_type TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    source_version TEXT,
    source_updated_at TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    audit_reference TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, source_module, source_entity_type, source_record_id),
    FOREIGN KEY (tenant_id, account_id)
        REFERENCES account_360_accounts (tenant_id, account_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX idx_a360_source_refs_account
    ON account_360_source_references (tenant_id, account_id);
CREATE INDEX idx_a360_source_refs_source
    ON account_360_source_references (tenant_id, source_module, source_entity_type);

CREATE TABLE account_360_relationship_references (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    related_account_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    source_module TEXT NOT NULL,
    source_entity_type TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    effective_from TEXT,
    effective_to TEXT,
    source_version TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, account_id, related_account_id, relationship_type,
            source_module, source_entity_type, source_record_id),
    CHECK (account_id <> related_account_id),
    FOREIGN KEY (tenant_id, account_id)
        REFERENCES account_360_accounts (tenant_id, account_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, related_account_id)
        REFERENCES account_360_accounts (tenant_id, account_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX idx_a360_relationships_account
    ON account_360_relationship_references (tenant_id, account_id);
CREATE INDEX idx_a360_relationships_related
    ON account_360_relationship_references (tenant_id, related_account_id);

CREATE TABLE account_360_contact_references (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    source_module TEXT NOT NULL,
    source_contact_id TEXT NOT NULL,
    display_name TEXT,
    relationship_role TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    source_version TEXT,
    source_updated_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, account_id, source_module, source_contact_id),
    FOREIGN KEY (tenant_id, account_id)
        REFERENCES account_360_accounts (tenant_id, account_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX idx_a360_contacts_account
    ON account_360_contact_references (tenant_id, account_id);

CREATE TABLE account_360_projection_states (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    projection_name TEXT NOT NULL,
    source_module TEXT NOT NULL,
    last_processed_event_id TEXT,
    last_source_version TEXT,
    last_source_sequence INTEGER,
    last_processed_at TEXT,
    status TEXT NOT NULL DEFAULT 'READY'
        CHECK (status IN ('READY', 'STALE', 'REBUILDING', 'ERROR')),
    error_code TEXT,
    error_message TEXT,
    rebuild_started_at TEXT,
    audit_reference TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, account_id, projection_name, source_module),
    FOREIGN KEY (tenant_id, account_id)
        REFERENCES account_360_accounts (tenant_id, account_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX idx_a360_projection_states_account
    ON account_360_projection_states (tenant_id, account_id, projection_name);

CREATE TABLE account_360_integration_states (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    source_module TEXT NOT NULL,
    integration_name TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('AVAILABLE', 'DEGRADED', 'STALE', 'UNAVAILABLE', 'ERROR')),
    last_success_at TEXT,
    last_event_at TEXT,
    last_failure_at TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    next_retry_at TEXT,
    diagnostic_reference TEXT,
    error_code TEXT,
    error_message TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, source_module, integration_name)
);

CREATE INDEX idx_a360_integration_states_tenant
    ON account_360_integration_states (tenant_id, source_module, status);

CREATE TABLE account_360_timeline_events (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    contact_reference_id TEXT,
    source_module TEXT NOT NULL,
    source_entity_type TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    received_at TEXT NOT NULL,
    producer_version TEXT NOT NULL,
    source_version TEXT,
    source_sequence INTEGER,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    summary TEXT,
    payload_json TEXT,
    source_reference TEXT,
    processing_status TEXT NOT NULL DEFAULT 'PROCESSED'
        CHECK (processing_status IN ('RECEIVED', 'PROCESSED', 'REJECTED', 'ERROR')),
    processing_error TEXT,
    processed_at TEXT,
    audit_reference TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, source_module, event_id),
    FOREIGN KEY (tenant_id, account_id)
        REFERENCES account_360_accounts (tenant_id, account_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, contact_reference_id)
        REFERENCES account_360_contact_references (tenant_id, id)
        ON UPDATE RESTRICT ON DELETE SET NULL
);

CREATE INDEX idx_a360_timeline_account_time
    ON account_360_timeline_events (tenant_id, account_id, occurred_at DESC);
CREATE INDEX idx_a360_timeline_account_category_time
    ON account_360_timeline_events (tenant_id, account_id, category, occurred_at DESC);
CREATE INDEX idx_a360_timeline_source_record
    ON account_360_timeline_events (
        tenant_id, source_module, source_entity_type, source_record_id, source_sequence
    );
