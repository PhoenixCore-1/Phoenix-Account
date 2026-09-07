# Phoenix Account 360 V1.0 — UI Contract

**Status:** Phase 10 implementation baseline

**Module code:** `account_360`

**Version:** `1.0.0`

## 1. Purpose

The Account 360 UI is the controlled presentation layer for the unified customer/account experience. It composes approved Account 360 services and projections and never bypasses Core or owning-module boundaries.

## 2. Navigation

- Registered through Phoenix Core.
- Display label: `Account 360`.
- Route is module-owned and supplied through the Core navigation contract.
- No independent authentication, tenant switching, or navigation stack.
- Back/drill-down actions return through the Phoenix Core navigation model.

## 3. Screen structure

The V1.0 account screen contains:

1. Account header
2. Overview
3. Financial Position
4. Credit & Exposure
5. Invoices
6. Orders & Quotes
7. Deliveries & POD
8. Payments & Allocations
9. Customer Ledger
10. Aging & Collections
11. Statements
12. Documents
13. Communication & Relationship
14. Tax & VAT
15. Credit Notes / Adjustments / Disputes
16. Unified Timeline
17. Quick actions

The implementation may group related sections into tabs/cards while preserving these capabilities.

## 4. Account header

The header presents the canonical account identity and safe summary context:

- account display name;
- canonical `account_id`;
- account status;
- key relationship/contact context where authorized;
- integration/freshness indicators where relevant.

## 5. Financial presentation

Financial information is displayed only through the Accounts boundary and requires the appropriate financial permission. Typical summary cards include balance, exposure, credit limit, available credit, credit status and currency.

Financial records provide source references, freshness and drill-down context. Account 360 does not calculate or persist an authoritative ledger.

## 6. Commercial and operational presentation

Sales, Inventory and other source-owned information is displayed from approved service contracts. Quotes, orders, deliveries, POD, returns, documents and operational context retain source references and provide source-owned drill-down where available.

## 7. Communication and relationship

Calls, WhatsApp, email, meetings, visits, notes, activities, tasks and follow-ups are presented from approved communication/CRM boundaries. Content and sensitive communication data remain separately permission controlled.

No external communication credentials are stored or exposed by the UI.

## 8. Unified timeline

The timeline is chronological and account scoped. Each item exposes source/module identity, category, event type, timestamp and source reference. Duplicate events are suppressed by the underlying timeline contract. Filters and pagination are bounded.

Timeline entries may display stale/unavailable indicators without pretending that missing source data is current.

## 9. Quick actions

Quick actions are descriptors bound to owning-module commands. The UI may render an action only when permitted and available. Execution must use an idempotency key and route to the owning service.

Examples: create CRM activity, create follow-up, open/create quote, open/create order, initiate collection workflow, open financial record, open delivery/POD, open communication.

## 10. State model

Every section supports explicit states:

- `LOADING` — data is being requested;
- `READY` — data is available and freshness is known;
- `EMPTY` — request succeeded with no records;
- `STALE` — data is available but freshness is outside the approved threshold;
- `DEGRADED` — partial integration/service availability;
- `UNAVAILABLE` — source cannot currently be served;
- `ERROR` — request failed unexpectedly;
- `FORBIDDEN` — the user is not authorized to view the section.

A section state must not leak records from another tenant or account.

## 11. Permissions

Permissions are server-side enforced. UI visibility is a convenience only and is not a security boundary. Financial and protected communication content have distinct permissions.

## 12. Performance

- bounded result sizes;
- pagination for lists/timeline;
- independent section loading;
- no unbounded cross-module queries;
- explicit freshness metadata;
- source drill-down rather than copying full source records into the Account 360 UI model.

## 13. Accessibility and usability

The UI contract requires stable labels, keyboard/focus-safe action semantics where supported by the host UI, readable state indicators, non-color-only status communication, and predictable empty/error states.

## 14. Phase 10 boundary

Phase 10 establishes the reusable UI presentation contract and view-model boundary. A host application may render this model in the Phoenix UI technology selected by Core. Rendering technology must not introduce direct database access or cross-module coupling.
