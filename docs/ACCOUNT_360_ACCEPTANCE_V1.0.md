# Phoenix Account 360 V1.0 — Acceptance Matrix

| ID | Area | Acceptance requirement | Priority |
|---|---|---|---|
| A360-001 | Tenant | No account data crosses tenant boundaries | Critical |
| A360-002 | Authorization | Server-side permissions are enforced for every protected operation | Critical |
| A360-003 | Identity | Account 360 resolves one canonical Phoenix account identity | Critical |
| A360-004 | Scope | All 14 V1.0 sections are represented in the module contract | High |
| A360-005 | Financial authority | Financial truth remains owned by Accounts | Critical |
| A360-006 | Financial drill-down | Financial views can identify and drill to authoritative Accounts records | High |
| A360-007 | Database boundary | No direct cross-module database access | Critical |
| A360-008 | CRM | CRM context is source-linked and tenant-safe | High |
| A360-009 | Sales | Quotes/orders are source-linked and tenant-safe | High |
| A360-010 | Inventory | Delivery/POD/return context is source-linked and tenant-safe | High |
| A360-011 | Procurement | Only approved customer-facing Procurement context is consumed | High |
| A360-012 | Accounts | Invoices, payments, ledger, aging and collections use approved Accounts contracts | Critical |
| A360-013 | Timeline | Events from supported domains are normalized without losing source identity | High |
| A360-014 | Idempotency | Duplicate events do not duplicate projection state | Critical |
| A360-015 | Ordering | Delayed/out-of-order events cannot overwrite newer state | High |
| A360-016 | Resilience | Source outages produce explicit unavailable/stale state rather than false authority | Critical |
| A360-017 | Recovery | Projections can be rebuilt/reconciled from source contracts/events | High |
| A360-018 | Performance | Large histories are paginated and bounded | High |
| A360-019 | Navigation | Account 360 follows Phoenix Core navigation/back-stack rules | High |
| A360-020 | Audit | Protected actions and material integration operations are auditable | Critical |
| A360-021 | Commands | Cross-module actions are routed to owning services | Critical |
| A360-022 | Communication | Supported customer communications are associated with canonical account/contact identity | High |
| A360-023 | Licensing | Module availability follows Core licensing/registration | High |
| A360-024 | Regression | Module passes clean-install, migration and integrated regression tests before release | Critical |

## Approval gate

Phase 1 is complete when scope, ownership, identity, contracts, security boundaries and acceptance criteria are internally consistent and approved for implementation.
