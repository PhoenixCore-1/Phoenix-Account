# Phoenix Account 360 V1.0 — Commercial & Operational View

## 1. Purpose

Phase 7 adds the commercial and operational customer view to Account 360 without taking ownership of Sales or Inventory data.

Account 360 is a unified read experience and command-routing boundary. Sales remains authoritative for quotes, opportunities and sales orders. Inventory remains authoritative for deliveries, POD, returns and physical stock context.

## 2. Scope

The Phase 7 view covers:

- Sales quotes and quote status;
- opportunities where exposed by Sales;
- sales orders and order status;
- commercial totals and currencies;
- delivery records and delivery status;
- proof-of-delivery references/status;
- customer-linked returns;
- operational source references and drill-down metadata;
- bounded pagination and freshness metadata;
- source availability/status;
- tenant and permission enforcement.

## 3. Ownership

Account 360 stores only projection/read-model data needed for its unified experience. It does not create authoritative Sales or Inventory records.

| Data | System of record |
|---|---|
| Quotes | Sales |
| Opportunities | Sales |
| Sales orders | Sales |
| Order status/totals | Sales |
| Deliveries | Inventory |
| POD | Inventory |
| Returns | Inventory |
| Physical stock | Inventory |

## 4. Security

All commercial and operational queries require authenticated tenant context and the appropriate Account 360 permission. Source records must belong to the requested tenant and canonical account.

Suggested permissions:

- `account_360.commercial.view`
- `account_360.operations.view`
- `account_360.commercial.command`
- `account_360.operations.command`

Account 360 must not bypass Core authorization.

## 5. Integration boundary

The view consumes explicit module ports/contracts. It must not access Sales or Inventory databases directly.

Queries are bounded and paginated. Results include source identity and freshness metadata (`source_version` and/or `as_of`) where provided.

Commands are routed to the owning module and require an idempotency key.

## 6. Data integrity

Returned records must be checked against the requested tenant/account boundary. Account 360 must reject cross-account records rather than silently displaying them.

Unavailable or stale source data must be represented as unavailable/stale and must not be presented as current authoritative truth.

## 7. Phase 7 acceptance

Phase 7 is complete when automated tests demonstrate:

1. commercial authorization is enforced;
2. operational authorization is enforced;
3. Sales data is source-linked and account-scoped;
4. Inventory data is source-linked and account-scoped;
5. pagination limits are bounded;
6. freshness metadata is preserved/required where applicable;
7. cross-account results are rejected;
8. commands route to the correct owning module;
9. command idempotency is required;
10. no direct database access is introduced;
11. source failures can be surfaced through the defined integration boundary.
