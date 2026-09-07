# Phoenix Account 360 V1.0 — Cross-Module Integration

**Status:** Phase 5 implementation baseline  
**Module code:** `account_360`  
**Version:** `1.0.0`

## Purpose

Define the controlled integration boundary between Account 360 and the owning Phoenix domain modules. Account 360 consumes approved contracts and routes commands; it never reads or writes another module's database.

## Supported owning modules

- CRM
- Sales
- Accounts
- Inventory
- Procurement

Communication providers remain behind approved Core/domain communication boundaries and are not treated as an Account 360 credential store.

## Identity rule

Every query and command is tenant scoped and anchored to canonical `account_id`. Source identifiers remain `SourceRef` values and do not replace canonical identity.

## Query contract

`QueryRequest` contains authenticated `UserContext`, source module, operation, canonical account ID, parameters, bounded page size and optional cursor. `QueryResult` carries records plus optional cursor, source version and `as_of` freshness metadata.

The initial boundary permits a maximum page size of 500 records. Implementations remain responsible for server-side authorization and tenant enforcement.

## Event contract

`DomainEvent` carries tenant, canonical account where available, source module/entity/record identity, unique event ID, event type, occurrence/receipt timestamps, producer version, payload and optional source version/sequence.

Consumers must treat `tenant_id + source_module + event_id` as the idempotency identity and must not assume arrival order is authoritative. Projection logic must compare source sequence/version where available.

## Command contract

`CommandRequest` carries authenticated context, target owning module, operation, canonical account ID, payload and mandatory idempotency key. Account 360 does not execute owning-module financial, sales, inventory, CRM or procurement mutations itself.

Commands are routed to the target module through the approved command port. The owning module remains authoritative and performs its own authorization, validation and transaction handling.

## Failure boundary

Source unavailability, timeout, stale data and integration errors must be observable through integration state. Query callers must not fabricate authoritative source data when a source is unavailable. Event consumers must support retry and idempotent replay.

## Security boundary

The integration layer accepts authenticated Core `UserContext`. It does not accept tenant identity as an untrusted override separate from the authenticated context. No credentials, connection strings or direct database handles are stored here.

## Phase 5 acceptance gate

Phase 5 is complete when:

- all supported source modules have explicit contract identities;
- queries are tenant/context scoped and bounded;
- commands require canonical account identity and idempotency keys;
- events contain source identity and event identity;
- unknown modules are rejected;
- no direct cross-module database access exists;
- integration tests pass with the Phase 2–4 regression suite;
- failure/retry and freshness metadata are representable;
- owning modules remain authoritative.
