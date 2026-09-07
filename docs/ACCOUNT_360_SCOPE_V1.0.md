# Phoenix Account 360 V1.0 — Scope

**Status:** Architecture baseline for implementation

**Module code:** `account_360`

**Module name:** Account 360

**Version:** `1.0.0`

## 1. Purpose

Account 360 provides the unified customer/account experience across Phoenix. It presents customer relationship, commercial, operational and financial context in one controlled view while preserving ownership of authoritative data in the source module.

Account 360 is a presentation, aggregation, projection and orchestration boundary. It is not a replacement for Accounts, CRM, Sales, Inventory or Procurement.

## 2. V1.0 functional sections

1. Overview
2. Financial Position
3. Credit & Exposure
4. Invoices
5. Orders & Quotes
6. Deliveries & POD
7. Payments & Allocations
8. Customer Ledger
9. Aging & Collections
10. Statements
11. Documents
12. Communication
13. Tax & VAT
14. Credit Notes / Adjustments / Disputes

## 3. Account 360 responsibilities

Account 360 owns:

- unified account presentation;
- cross-module context composition;
- canonical account resolution through approved contracts;
- Account 360-specific projections/indexes where required for performance;
- normalized cross-module timeline data;
- source references and drill-down context;
- Account 360-specific orchestration;
- Account 360-specific UI state and presentation;
- integration health and freshness indicators.

## 4. Explicit non-responsibilities

Account 360 does not own:

- the authoritative customer relationship record owned by CRM;
- quotes or sales orders owned by Sales;
- physical stock or warehouse truth owned by Inventory;
- purchasing truth owned by Procurement;
- financial ledger, invoices, payments, allocations, VAT, credit notes or other financial system-of-record data owned by Accounts;
- Phoenix identity, tenant, authentication, authorization or platform audit infrastructure owned by Core.

## 5. Quick actions

Account 360 may expose quick actions, but execution must be routed to the owning module/service. Examples include:

- create CRM activity;
- create follow-up;
- open/create quote through Sales;
- open/create order through Sales where permitted;
- initiate collection workflow through Accounts;
- open financial record through Accounts;
- open delivery/POD record through Inventory;
- open customer communication through the approved communication integration.

No action may bypass owning-module authorization or business rules.

## 6. Unified account timeline

The Account 360 timeline may present normalized events from:

- CRM interactions, calls, meetings, visits, notes and activities;
- quotes and orders;
- deliveries and POD;
- invoices;
- payments and allocations;
- credit notes and adjustments;
- disputes;
- collection activity;
- documents;
- account status events;
- customer communications where integrated.

Timeline entries must retain source module, source record reference, event type, timestamp, tenant context and version/idempotency information as required by the event contract.

## 7. Communication

Customer communication is part of the V1.0 relationship view. The integration must support the approved communicator/communication service boundary and may include calls, WhatsApp, email, meetings, visits, notes, tasks and follow-ups where those records are exposed by an owning integration.

Account 360 must not directly store or own external communication-system credentials or bypass the approved integration boundary.

## 8. Security

All Account 360 access is tenant-scoped and server-side authorized. Financial information requires the appropriate Accounts permissions. Sensitive communication and customer information must follow source-module and Core authorization rules.

## 9. Data authority rule

Where a value is authoritative in another module, Account 360 may cache or project it for performance but must identify the source and provide authoritative drill-down or retrieval where required. Account 360 must never become a shadow financial ledger.
