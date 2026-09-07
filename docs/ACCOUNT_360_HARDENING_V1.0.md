# Phoenix Account 360 V1.0 — Phase 13 Hardening

## Objective

Harden the V1.0 implementation without expanding business scope.

## Controls

### Tenant and account isolation
- Authenticated tenant context is mandatory at integration boundaries.
- Queries and commands are scoped by canonical account ID.
- Returned projections and timeline records are revalidated against requested tenant/account scope.
- Cross-module database access is prohibited.

### Authorization
- Permission checks remain server-side.
- Financial, timeline, general Account 360, communication content and AI action permissions remain distinct.
- AI output cannot grant authorization.

### Freshness and ordering
- Source versions/sequences and as-of metadata remain part of integration contracts.
- Timeline presentation is deterministic newest-first.
- Duplicate events remain idempotent through the timeline store boundary.
- Source systems remain authoritative; projections remain rebuildable.

### Idempotency
- Mutating commands require idempotency keys.
- AI action execution requires an idempotency key.
- Commands continue to route to owning modules.

### Resilience
- Integration failures are represented through explicit error/state contracts.
- Consumers must surface stale/degraded/unavailable state rather than silently presenting unavailable data as current.

### Performance
- Cross-module and timeline reads are bounded to a maximum page size of 500.
- Cursor pagination is supported by contracts.
- AI context is bounded to 100 items.

### Secrets
- No provider credentials, tokens or session secrets are stored by Account 360.

## Phase 13 exit condition

Run the complete regression suite after the hardening changes. Phase 13 closes only when all existing and new tests pass with no known critical security or contract defects.
