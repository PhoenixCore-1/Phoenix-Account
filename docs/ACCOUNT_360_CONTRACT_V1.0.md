# Phoenix Account 360 V1.0 — Module Contract

## 1. Contract principle

Account 360 integrates with Phoenix Core and domain modules through explicit service, adapter and event contracts. It must not connect directly to another module's database.

## 2. Canonical identity

Every Account 360 request and projection is anchored to:

- `tenant_id` — mandatory tenant boundary;
- `account_id` — Phoenix canonical customer/account identity;
- optional source references such as CRM customer ID, Sales customer/order ID, Inventory customer/delivery ID, Procurement reference and Accounts customer/account reference.

Source-local identifiers are references, not alternate canonical identities.

## 3. Core contract

Account 360 requires Core-provided capabilities for:

- authenticated user context;
- tenant context;
- server-side authorization;
- module registration and licensing;
- navigation registration;
- audit/event infrastructure;
- configuration;
- approved service/event transport;
- workflow infrastructure where used.

Core remains responsible for platform identity and tenant isolation.

## 4. Source-domain contracts

### CRM

Account 360 consumes approved CRM services/events for:

- canonical customer/account relationship references;
- contacts and relationship roles;
- interactions;
- calls;
- meetings and visits;
- CRM activities and notes;
- customer relationship status/context.

### Sales

Account 360 consumes approved Sales services/events for:

- quotes;
- sales orders;
- order status;
- commercial totals;
- opportunity references where exposed;
- source record drill-down.

### Inventory

Account 360 consumes approved Inventory services/events for:

- deliveries;
- POD status/reference;
- returns;
- customer-linked operational stock context where exposed;
- source record drill-down.

### Procurement

Account 360 consumes only customer-facing procurement context explicitly exposed by Procurement contracts. It does not assume access to Procurement internals.

### Accounts

Account 360 consumes approved Accounts services/events for:

- financial account identity;
- credit limit and credit status;
- balance and exposure;
- invoices;
- payments;
- allocations;
- customer ledger;
- aging;
- collections context;
- statements;
- tax/VAT context;
- credit notes;
- adjustments;
- disputes;
- financial documents and audit context;
- controlled financial commands.

Accounts remains the financial system of record.

## 5. Event contract requirements

Events consumed by Account 360 must support, where applicable:

- tenant ID;
- canonical account ID;
- source module;
- source record ID;
- event ID;
- event type;
- event timestamp;
- producer/version metadata;
- sequence/version information where available.

Processing must be idempotent. Duplicate events must not create duplicate projection records. Delayed or out-of-order events must not overwrite newer state.

## 6. Query contract requirements

Queries must be:

- tenant scoped;
- permission scoped;
- bounded/paginated;
- source-linked;
- explicit about freshness where projected data is used;
- resilient to unavailable source modules.

## 7. Command contract requirements

Account 360 may request actions but does not execute another module's domain command internally. Commands are routed to the owning module/service.

Financial commands are routed to Accounts. Sales commands are routed to Sales. Inventory commands are routed to Inventory. CRM relationship commands are routed to CRM.

## 8. Error and resilience contract

Integration failures must be observable and must not silently present unavailable data as authoritative. The integration layer must support retry/reconciliation and projection rebuild where applicable.

## 9. Audit contract

User actions, authorization failures, integration failures, controlled commands and material projection operations must be auditable through Phoenix Core/approved audit infrastructure.
