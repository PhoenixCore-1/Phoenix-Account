# Phoenix Account 360 V1.0 — Domain Model

**Status:** Phase 2 domain model baseline

**Module code:** `account_360`

**Version:** `1.0.0`

## 1. Purpose

This document defines the Account 360 domain model before database implementation. The model contains only data that Account 360 is permitted to own: canonical account references, source mappings, projection state, integration state, and normalized timeline/index data.

Account 360 is an aggregation/projection boundary. It does not become the system of record for CRM, Sales, Inventory, Procurement or Accounts.

## 2. Domain principles

1. Every record is tenant scoped.
2. `account_id` is the canonical Phoenix customer/account identity.
3. Source-system identifiers are references, never alternate canonical identities.
4. Authoritative domain data remains in the owning module.
5. Projected data must retain source identity and freshness/version metadata where applicable.
6. Timeline ingestion must be idempotent.
7. Older/out-of-order source events must not overwrite newer projection state.
8. Account 360 must be rebuildable from approved source contracts/events.
9. No external communication credentials are stored by Account 360.
10. Audit linkage points to Core/approved audit infrastructure rather than creating a parallel audit system.

## 3. Aggregate: Account Reference

The Account Reference represents the Account 360 anchor for a canonical Phoenix account.

### Required concepts

- internal Account 360 record identity;
- `tenant_id`;
- canonical `account_id`;
- lifecycle/status metadata needed by Account 360;
- display/search projection fields only where contractually permitted;
- created/updated timestamps;
- version information.

### Authority

The canonical account identity is resolved through Phoenix Core/approved account identity contracts. Account 360 does not redefine the customer master.

## 4. Aggregate: Source Reference

A Source Reference maps the canonical account to a record in an owning module.

### Attributes

- `tenant_id`;
- `account_id`;
- `source_module`;
- `source_entity_type`;
- `source_record_id`;
- optional source version/revision;
- active/inactive state;
- first-seen/last-seen timestamps;
- freshness metadata.

### Constraint

For a given tenant, canonical account, source module, entity type and source record ID, the mapping must be unique.

## 5. Aggregate: Account Relationship Reference

This represents Account 360-specific relationship/index information where required for unified presentation.

Examples:

- parent account reference;
- child account reference;
- branch/site reference;
- related canonical account;
- relationship type;
- effective dates;
- source reference.

Account 360 does not replace CRM's authoritative relationship model. CRM remains authoritative for CRM relationship semantics.

## 6. Aggregate: Projection State

Projection State records the current Account 360 projection position for a source stream or projection family.

### Attributes

- `tenant_id`;
- `account_id` where account-specific;
- `projection_name`;
- last processed event ID;
- last processed source version/sequence where available;
- last successful processing time;
- projection status;
- rebuild state;
- error metadata;
- updated timestamp.

### Purpose

Supports idempotency, stale-state detection, recovery and projection rebuilds.

## 7. Aggregate: Integration State

Integration State describes the health and availability of an Account 360 source integration.

### Attributes

- `tenant_id`;
- source module/service;
- integration name;
- status: `AVAILABLE`, `DEGRADED`, `STALE`, `UNAVAILABLE`, `ERROR`;
- last successful contact;
- last successful event/query time;
- last failure time;
- retry count;
- next retry time where applicable;
- diagnostic reference;
- updated timestamp.

This state must never be interpreted as domain truth. It describes integration health only.

## 8. Aggregate: Timeline Event

Timeline Event is the normalized Account 360 representation of a source event/activity.

### Required attributes

- internal timeline record ID;
- `tenant_id`;
- `account_id`;
- optional contact reference;
- `source_module`;
- `source_entity_type`;
- `source_record_id`;
- `event_id`;
- `event_type`;
- occurred-at timestamp;
- received-at timestamp;
- producer/version metadata;
- source sequence/version where available;
- normalized title/category;
- optional summary/display payload;
- source drill-down reference;
- processing metadata;
- created timestamp.

### Idempotency

`tenant_id + source_module + event_id` must be unique for event ingestion.

### Ordering

Projection updates must compare source sequence/version where supplied. If unavailable, processing must use a safe event timestamp/version policy and must not assume arrival order is authoritative.

## 9. Contact / Relationship References

Account 360 may maintain lightweight references needed to associate communications and activities to a canonical account/contact.

These are references/projections, not replacement CRM contact records.

Minimum concepts:

- `tenant_id`;
- canonical account ID;
- source contact ID/reference;
- source module;
- display name projection where permitted;
- relationship role where exposed;
- active state;
- source version/freshness.

## 10. Data deliberately excluded from Account 360 ownership

The following must not be implemented as Account 360 system-of-record tables:

- financial ledger entries;
- invoices;
- payments;
- allocations;
- VAT/tax transactions;
- credit notes;
- authoritative credit limits;
- CRM customer master;
- authoritative CRM contacts;
- quotes;
- sales orders;
- physical stock balances;
- warehouse/bin truth;
- procurement purchasing records;
- external communication credentials.

Account 360 may maintain bounded projections/indexes of source information when required for performance and presentation, provided source identity and freshness are retained.

## 11. Domain relationships

```text
Canonical Account
       │
       ├──< Source References >── CRM / Sales / Inventory / Procurement / Accounts
       │
       ├──< Relationship References >── related accounts / branches / sites
       │
       ├──< Contact References >── CRM/communication sources
       │
       ├──< Projection States >── projection families / source streams
       │
       ├──< Integration States >── source integrations
       │
       └──< Timeline Events >── normalized cross-module history
```

## 12. Tenant isolation

Every Account 360-owned persistence record that can contain tenant-specific data must include `tenant_id` and enforce tenant-scoped access at the repository/service boundary. Composite uniqueness and lookup indexes must include tenant scope where appropriate.

## 13. Lifecycle and deletion

Account 360 records should normally be retired/deactivated rather than physically deleted when required for traceability. Source-reference removal must not silently erase audit/timeline history. Retention and deletion rules must follow Phoenix Core policy and source-module contracts.

## 14. Database mapping candidates

The initial relational schema is expected to contain these Account 360-owned tables:

- `account_360_accounts`
- `account_360_source_references`
- `account_360_relationship_references`
- `account_360_contact_references`
- `account_360_projection_states`
- `account_360_integration_states`
- `account_360_timeline_events`

Exact columns, data types, foreign-key strategy and indexes are defined in the schema phase after this domain model is accepted.

## 15. Phase 2 domain-model gate

The domain model is ready for schema implementation when:

- canonical identity is unambiguous;
- tenant scope is present;
- source ownership is explicit;
- no shadow system-of-record data has been introduced;
- event idempotency and ordering are representable;
- freshness/integration state is representable;
- projection rebuild is supportable;
- source drill-down remains possible;
- the model supports the V1.0 Account 360 scope.
