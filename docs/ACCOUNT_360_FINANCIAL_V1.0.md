# Phoenix Account 360 V1.0 — Financial Account View

**Status:** Phase 6 implementation baseline  
**Module:** `account_360`  
**Version:** `1.0.0`

## Purpose

Phase 6 provides the controlled financial view of an account. Accounts remains the authoritative financial system of record. Account 360 only consumes approved Accounts contracts and presents bounded, source-linked financial information.

## Financial coverage

The financial boundary supports:

- credit status;
- credit limit;
- balance and exposure;
- available credit where exposed;
- invoices;
- payments;
- allocations;
- customer ledger records;
- aging;
- collections context;
- statements;
- tax/VAT context;
- credit notes;
- adjustments;
- disputes;
- financial source/document references.

These are represented as read-contract records, not Account 360-owned accounting tables.

## Accounts boundary

`AccountsFinancialPort` is the explicit boundary used by Account 360. Its implementation belongs to the Accounts service/host integration.

Account 360 must not:

- connect directly to the Accounts database;
- calculate or persist an authoritative ledger;
- create duplicate invoices, payments or allocations;
- replace the authoritative credit limit;
- bypass Accounts authorization or transaction handling.

## Security

Financial operations require the Account 360 financial permission `account_360.financial.view`. The authenticated `UserContext` supplies tenant and user identity; callers cannot override tenant scope independently.

The owning Accounts service remains responsible for its own authorization and business validation.

## Freshness and source identity

Financial summaries and paged financial records must carry `as_of` freshness metadata. Source version and source references are retained where available. Missing freshness metadata is treated as unsafe for the financial view rather than silently presenting the result as current.

Returned records must belong to the requested canonical `account_id`, and summary results must belong to the authenticated tenant.

## Pagination

Financial history is bounded to a maximum page size of 500 records and supports cursor-based continuation.

## Controlled financial actions

Account 360 may route a financial command such as a statement request through the Accounts contract. It does not execute financial mutations itself. Commands require an idempotency key and remain auditable through the owning Accounts/Core boundary.

## Phase 6 acceptance gate

Phase 6 is complete when:

1. the financial view uses an explicit Accounts boundary;
2. financial permissions are enforced server-side;
3. tenant and canonical account identity are validated;
4. source freshness metadata is required;
5. financial history is bounded/paginated;
6. source references are retained;
7. financial commands are routed to Accounts with idempotency;
8. cross-tenant or mismatched-account results are rejected;
9. no financial system-of-record tables are introduced into Account 360; and
10. Phase 2–6 regression tests pass.
