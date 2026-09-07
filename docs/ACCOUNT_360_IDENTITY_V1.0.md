# Phoenix Account 360 V1.0 — Identity Resolution

**Status:** Phase 4 implementation baseline

**Module code:** `account_360`

**Version:** `1.0.0`

## 1. Purpose

Phase 4 establishes the boundary that resolves source-system customer/account records to the canonical Phoenix `account_id` used by Account 360.

Account 360 does not become the customer master. The identity service owns only the resolution/index boundary and delegates persistence through an explicit store/service contract.

## 2. Identity model

A source identity is the tuple:

`source_module + source_entity_type + source_record_id`

It is always interpreted inside a `tenant_id`.

The result is:

`tenant_id + canonical account_id`

Source IDs never become alternate canonical account IDs.

## 3. Resolution rules

1. Every resolution requires authenticated user and tenant context.
2. Tenant scope is mandatory on every lookup and write.
3. An existing source mapping is returned without creating a second account.
4. Strict resolution does not create missing accounts.
5. Explicit `create_if_missing=True` may create a canonical account through the approved identity store boundary.
6. A newly created account must belong to the requesting tenant.
7. Source binding failures are surfaced as identity conflicts rather than silently ignored.
8. Empty identity components are rejected.
9. Cross-tenant mappings must never be returned as valid matches.
10. Source-system ownership remains authoritative outside Account 360.

## 4. Service boundary

`AccountIdentityService` depends on `AccountIdentityStore` rather than a database implementation.

The store contract provides:

- lookup by tenant + source identity;
- lookup by tenant + canonical account ID;
- creation of a canonical account identity;
- binding of a source identity to a canonical account.

This keeps the service independent of SQLite, Core internals, CRM schema, Accounts schema or any other module database.

## 5. Conflict handling

`IdentityConflictError` is raised when an identity cannot safely be resolved, including:

- the identity store returns an account belonging to another tenant;
- source binding fails because the identity cannot be safely established.

`IdentityNotFoundError` is raised when strict resolution cannot find a mapping.

These errors must be observable by the calling application and must not result in silent fallback to another tenant or arbitrary account.

## 6. Canonical account verification

`verify_account()` confirms that a canonical `account_id` exists within the requesting tenant before it is used by downstream Account 360 services.

A canonical account from another tenant is never accepted as a valid result.

## 7. Duplicate prevention

The database schema already enforces tenant-scoped uniqueness for source references. The service must therefore resolve an existing mapping before creating a new one, while the persistence boundary remains responsible for enforcing its uniqueness constraint under concurrent requests.

## 8. Authority and lifecycle

Account creation through this service establishes a canonical identity reference only. It does not create a CRM customer, financial account, sales customer or inventory customer record unless an approved Core/domain command explicitly performs that operation.

Deactivation, merging and master-data lifecycle remain subject to the authoritative customer/account contract. Phase 4 does not implement silent merges.

## 9. Phase 4 acceptance gate

Phase 4 is complete when:

- canonical identity resolution is tenant scoped;
- source identity is explicit and validated;
- existing mappings are reused;
- strict missing resolution fails safely;
- explicit creation binds a source identity safely;
- cross-tenant identity is rejected;
- source-binding conflicts are surfaced;
- canonical account verification is tenant scoped;
- persistence is abstracted behind an explicit boundary;
- automated tests pass;
- no direct cross-module database access exists.
