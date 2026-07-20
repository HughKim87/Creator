-- Stage 03 initial schema. Applied inside one transaction by the runner.
-- schema_version 1 (DB schema; independent of the domain serialization v2).

CREATE TABLE schema_meta (
    schema_version INTEGER NOT NULL,
    applied_at TEXT NOT NULL,
    application_version TEXT NOT NULL
);

CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    source_id TEXT,
    lifecycle_status TEXT NOT NULL CHECK (lifecycle_status IN (
        'active', 'waiting_user', 'blocked_external', 'failed', 'completed', 'cancelled')),
    current_phase TEXT NOT NULL CHECK (current_phase IN (
        'intake', 'planning', 'editing', 'technical_validation', 'human_approval', 'delivery')),
    state_version INTEGER NOT NULL CHECK (state_version >= 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_event_id TEXT
);

CREATE TABLE workflow_events (
    event_id TEXT PRIMARY KEY,
    command_id TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL CHECK (length(request_digest) = 64),
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    event_type TEXT NOT NULL,
    prev_lifecycle TEXT NOT NULL,
    next_lifecycle TEXT NOT NULL,
    prev_phase TEXT NOT NULL,
    next_phase TEXT NOT NULL,
    state_version INTEGER NOT NULL CHECK (state_version > 0),
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'agent', 'automation')),
    actor_id TEXT NOT NULL,
    reason TEXT,
    payload_json TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    UNIQUE (project_id, state_version)
);

-- Append-only enforcement for the ordinary execution account.
CREATE TRIGGER workflow_events_no_update
BEFORE UPDATE ON workflow_events
BEGIN
    SELECT RAISE(ABORT, 'workflow_events is append-only');
END;

CREATE TRIGGER workflow_events_no_delete
BEFORE DELETE ON workflow_events
BEGIN
    SELECT RAISE(ABORT, 'workflow_events is append-only');
END;

CREATE TABLE sources (
    source_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    fingerprint_algorithm TEXT NOT NULL CHECK (fingerprint_algorithm = 'sha256'),
    fingerprint_digest TEXT NOT NULL CHECK (length(fingerprint_digest) = 64),
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    locator TEXT NOT NULL,
    media_metadata_json TEXT NOT NULL DEFAULT '{}',
    registered_at TEXT NOT NULL,
    UNIQUE (project_id, fingerprint_digest)
);

CREATE TABLE generations (
    generation_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    status TEXT NOT NULL CHECK (status IN ('open', 'completed', 'failed', 'aborted')),
    baseline_hash TEXT CHECK (baseline_hash IS NULL OR length(baseline_hash) = 64),
    created_at TEXT NOT NULL,
    closed_at TEXT
);

CREATE TABLE artifacts (
    artifact_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    generation_id TEXT NOT NULL REFERENCES generations(generation_id),
    role TEXT NOT NULL CHECK (role IN (
        'draft', 'calibration_candidate', 'approved_baseline', 'current_deliverable',
        'superseded', 'failure_evidence')),
    relative_path TEXT,
    content_sha256 TEXT NOT NULL CHECK (length(content_sha256) = 64),
    size_bytes INTEGER CHECK (size_bytes IS NULL OR size_bytes >= 0),
    tool_version TEXT,
    validation_status TEXT NOT NULL DEFAULT 'pending' CHECK (validation_status IN (
        'pending', 'passed', 'failed', 'not_required')),
    artifact_lifecycle TEXT NOT NULL DEFAULT 'staging' CHECK (artifact_lifecycle IN (
        'staging', 'ready', 'failed', 'quarantined')),
    parent_ids_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE approval_requests (
    request_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    generation_id TEXT REFERENCES generations(generation_id),
    scope TEXT NOT NULL CHECK (scope IN (
        'generation', 'technical_validation', 'human_av', 'waiver')),
    artifact_id TEXT REFERENCES artifacts(artifact_id),
    target_sha256 TEXT CHECK (target_sha256 IS NULL OR length(target_sha256) = 64),
    challenge TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'consumed', 'void')),
    created_at TEXT NOT NULL
);

CREATE TABLE approvals (
    approval_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    generation_id TEXT REFERENCES generations(generation_id),
    scope TEXT NOT NULL CHECK (scope IN (
        'generation', 'technical_validation', 'human_av', 'waiver')),
    decision TEXT NOT NULL CHECK (decision IN ('approved', 'rejected')),
    actor_kind TEXT NOT NULL CHECK (actor_kind IN ('human', 'agent', 'automation')),
    actor_id TEXT NOT NULL,
    provenance_type TEXT,
    provenance_session TEXT,
    request_id TEXT REFERENCES approval_requests(request_id),
    evidence_id TEXT UNIQUE,
    target_sha256 TEXT CHECK (target_sha256 IS NULL OR length(target_sha256) = 64),
    created_at TEXT NOT NULL
);

CREATE TABLE failures (
    failure_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    phase TEXT NOT NULL,
    failure_code TEXT NOT NULL,
    fingerprint TEXT NOT NULL CHECK (length(fingerprint) = 64),
    message TEXT NOT NULL,
    tool TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    linked_event_id TEXT REFERENCES workflow_events(event_id),
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    occurred_at TEXT NOT NULL,
    resolved_at TEXT
);
