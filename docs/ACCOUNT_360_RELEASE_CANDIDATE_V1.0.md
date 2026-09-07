# Phoenix Account 360 V1.0 — Release Candidate

**Module:** Account 360  
**Module code:** `account_360`  
**Release candidate:** `1.0.0`  
**Branch:** `feature/account-360-v1-build`

## Purpose

This document is the Phase 14 release-candidate gate. It validates the complete Account 360 V1.0 implementation before the final V1.0 freeze.

## Release-candidate checklist

### Automated regression
- Full pytest suite passes.
- All previously closed phase tests remain passing.
- Phase 13 hardening tests remain passing.
- Release-candidate tests pass.

### Package integrity
- Python package imports cleanly.
- Package version is `1.0.0`.
- Build metadata version is `1.0.0`.
- No runtime dependencies are required by the module.
- Package discovery includes `account_360`.

### Schema integrity
- Canonical `schema.sql` is present and syntactically valid.
- Foreign-key enforcement is enabled.
- Required Account 360 projection/reference tables exist.
- No Account 360 table becomes the system of record for financial, CRM, Sales, Inventory or Procurement transactions.

### Architecture regression
- Core remains the security, identity, licensing, navigation and audit boundary.
- Cross-module access remains contract/port based.
- Account 360 has no direct cross-module database access.
- Financial actions remain routed to Accounts.
- Sales actions remain routed to Sales.
- Inventory actions remain routed to Inventory.
- CRM relationship/communication records remain source-owned.
- AI remains consumed through the Core AI service boundary.

### Security regression
- Tenant context is mandatory for protected operations.
- Authenticated user context is mandatory for protected operations.
- Server-side permission checks remain mandatory.
- Sensitive communication content requires the separate content permission.
- AI action execution requires explicit action authorization and idempotency.
- No external communication credentials or provider secrets are stored by Account 360.

### Integration regression
- Source references retain source module/entity/record identity.
- Timeline events are idempotent by tenant/source/event identity.
- Timeline ordering is deterministic.
- Queries and commands are bounded and tenant/account scoped.
- Integration failures can be represented without converting source data into Account 360 ownership.

### Operational release readiness
- Clean checkout can install the package and run the tests.
- Schema can be initialized in a clean SQLite database.
- Existing V1.0 data model is upgrade-safe through the documented migration/version strategy.
- No unresolved critical security, financial authority, tenant-isolation or data-integrity defect remains.

## Known limitations entering V1.0

1. Account 360 is a unified view/projection layer, not a replacement for source systems of record.
2. Real production connectors to CRM, Sales, Inventory, Procurement, Accounts and communication providers depend on their approved Phoenix service/event contracts.
3. External communication credentials are intentionally outside this module and must be supplied through approved Core/provider boundaries.
4. AI provider/runtime selection is intentionally outside this module and remains a Phoenix Core responsibility.
5. Performance characteristics of production integrations depend on source-module latency and the deployed projection/cache strategy.

## Phase 14 exit evidence

The phase is closed only after the full automated suite and release-candidate checks pass on the authoritative build branch, with no unresolved critical defects.

**Phase 14 status:** Pending execution of the release-candidate test suite.
