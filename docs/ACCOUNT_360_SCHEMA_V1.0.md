# Phoenix Account 360 — Database Schema V1.0

**Module:** `account_360`  
**Name:** Account 360  
**Version:** `1.0.0`  
**Phase:** 2 — Domain Model & Database Schema  
**Status:** Schema baseline

## 1. Purpose

This schema implements only persistence that Account 360 is permitted to own. It stores canonical account references, source references, lightweight relationship/contact references, projection state, integration health, and normalized timeline events.

It does **not** become the system of record for financial, CRM, Sales, Inventory, Procurement, or external communication data.

## 2. Tables

| Table | Purpose | Authority |
|---|---|---|
| `account_360_accounts` | Tenant-scoped Account 360 account reference and display projection | Core/account-resolution contract |
| `account_360_source_references` | Maps source records to canonical accounts | Owning source module |
| `account_360_relationship_references` | Lightweight cross-account relationship projection | CRM/approved source contract |
| `account_360_contact_references` | Lightweight contact references for Account 360 context | CRM/approved source contract |
| `account_360_projection_states` | Projection processing/version/rebuild state | Account 360 integration layer |
| `account_360_integration_states` | Source integration health and retry state | Account 360 integration layer |
| `account_360_timeline_events` | Normalized cross-module timeline events | Source event + Account 360 projection |

## 3. Tenant Isolation

Every tenant-specific table carries `tenant_id`. Canonical account foreign keys use the composite `(tenant_id, account_id)` boundary so an account reference from one tenant cannot be attached to another tenant's account.

The application/service layer must also enforce tenant scope on every read, write, command, projection and event operation. Database constraints are a second line of defence, not a replacement for server-side authorization.

## 4. Idempotency and Ordering

Timeline ingestion has a database uniqueness boundary on:

`(tenant_id, source_module, event_id)`

This prevents the same source event from being persisted twice for a tenant/source combination.

`source_version` and `source_sequence` are retained where supplied by the source. The schema does not attempt to decide whether an incoming event is newer; the projection/integration service must reject or ignore stale/out-of-order state according to the event contract.

## 5. Freshness and Recovery

Source version/update timestamps are retained on source-backed references. Projection state records the last processed event/version/sequence and processing status. Integration state records availability, failure and retry information.

These records allow Account 360 projections to be marked stale, rebuilt and reconciled without becoming an independent system of record.

## 6. Audit Boundary

Account 360 does not create a parallel audit ledger. `audit_reference` fields provide linkage to Phoenix Core or another approved audit service where required. Audit creation, authorization and retention remain outside this schema.

## 7. Delete and Retention Policy

The schema uses restrictive foreign keys for core account/reference records so historical context is not silently orphaned. Timeline contact references may be set to NULL when the local contact reference is removed.

Application retention/deletion rules must follow Phoenix Core and source-module policy. Deactivation/retirement is preferred over destructive deletion where traceability is required.

## 8. System-of-Record Boundary

The following are deliberately absent from the schema:

- invoices
- payments
- allocations
- ledger entries
- VAT/tax transactions
- credit notes
- authoritative credit limits
- CRM customer/contact master data
- quotes
- Sales orders
- physical stock balances
- warehouse/bin truth
- procurement records
- external communication credentials

Account 360 may project and display these values through approved contracts, but it must not create duplicate authoritative financial or operational truth.

## 9. Migration

`migrations/001_initial_account_360.sql` is the initial migration and mirrors `schema.sql` for the V1.0 baseline.

Future migrations must be additive or explicitly versioned and must preserve existing tenant isolation, source traceability, idempotency and system-of-record boundaries.

## 10. Schema Gate

The Phase 2 database schema is ready for implementation when:

1. the schema loads into the supported development database;
2. database integrity checks pass;
3. required tables and indexes exist;
4. tenant-scoped foreign keys reject cross-tenant references;
5. canonical account uniqueness is enforced per tenant;
6. timeline event idempotency is enforced;
7. relationship self-links are rejected;
8. schema tests pass; and
9. no prohibited system-of-record tables are introduced.
