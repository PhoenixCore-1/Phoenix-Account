# Phoenix Account 360 V1.0.0 — Deployment & Rollback

## Deployment

1. Confirm the target Phoenix environment supports the `account_360` module contract and required Core services.
2. Deploy package version `1.0.0` using the platform's standard module deployment process.
3. Apply `migrations/001_initial_account_360.sql` using the platform-controlled migration process where the V1.0 schema is not already present.
4. Register `account_360` with Phoenix Core and confirm licensing is enabled for the tenant.
5. Confirm required permissions are configured server-side.
6. Configure approved CRM, Sales, Accounts, Inventory, Procurement and communication service boundaries externally.
7. Confirm no external credentials or provider secrets are placed in the Account 360 package or database.
8. Run the complete regression suite before production promotion.
9. Verify navigation registration, account resolution, integration health and timeline freshness in the target environment.

## Upgrade

V1.0.0 is the initial production baseline. Future releases must use explicit versioned migrations. Do not replace or rewrite the V1.0 baseline migration after deployment.

## Rollback

1. Stop promotion of the affected package.
2. Revert the application package through the standard Phoenix deployment mechanism.
3. Preserve Account 360 audit and projection history unless an approved recovery procedure requires otherwise.
4. Database rollback must use the platform migration/recovery mechanism. Manual production table deletion is not an approved rollback method.
5. If a source integration fails, keep Account 360 available in a documented degraded/stale/unavailable state rather than copying source transactions into local system-of-record tables.
6. Re-run regression and integration health checks before restoring normal traffic.

## Operational principle

Rollback must preserve tenant isolation, source traceability and authoritative ownership. Account 360 may be unavailable or stale, but it must not become an unauthorized financial, CRM, Sales, Inventory or Procurement system of record during recovery.
