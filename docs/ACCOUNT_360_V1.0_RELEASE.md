# Phoenix Account 360 V1.0.0 — Release

**Module:** Account 360  
**Module code:** `account_360`  
**Version:** `1.0.0`  
**Release status:** FROZEN  
**Build branch:** `feature/account-360-v1-build`

## Release declaration

Phoenix Account 360 V1.0.0 is the frozen first production baseline for the Account 360 module.

The V1.0.0 baseline includes the approved scope, contracts, domain model, owned projection schema, Core adapter, identity resolution, cross-module integration boundaries, financial view, commercial/operational 360, communication/relationship view, unified timeline, UI presentation model, workflows/actions, AI service integration, hardening controls, and release-candidate regression suite.

## Test evidence

The complete local regression suite passed:

**127 passed**

No V1.0.0 functionality is to be added after this freeze without a versioned change.

## System-of-record boundary

Account 360 remains a unified view/projection layer. Source systems remain authoritative for financial, CRM, Sales, Inventory, Procurement and communication records. Account 360 does not store external communication credentials or AI provider credentials.

## Schema baseline

The V1.0.0 persistence baseline is represented by `schema.sql` and migration `migrations/001_initial_account_360.sql`.

Future schema changes must use a new versioned migration and must preserve tenant isolation, source traceability, idempotency and system-of-record boundaries.

## Deployment

1. Deploy the `account_360` package through the Phoenix module deployment mechanism.
2. Register the module through Phoenix Core.
3. Apply the approved Account 360 migration through the platform migration process.
4. Configure approved Core/service boundaries externally; do not place provider credentials in this module.
5. Verify module licensing, permissions, navigation and integration health.
6. Run the regression suite before production promotion.

## Rollback

Rollback must be performed through the Phoenix deployment/migration mechanism. Application code may be reverted to the previous approved package. Database rollback must use the platform's controlled migration rollback/recovery procedure; do not manually delete Account 360 production data.

If a source integration is unavailable, Account 360 should degrade to an explicit stale/unavailable state rather than become an independent source of truth.

## Versioning policy

- `1.0.0` = frozen baseline.
- `1.0.x` = backward-compatible patch/security/defect fixes.
- New business scope, ownership changes or contract changes require a new planned version and architecture gate.

## Freeze rule

Any change to V1.0.0 after this release must be explicitly classified as a patch, correction, security fix or new-version work. No silent scope expansion is permitted.
