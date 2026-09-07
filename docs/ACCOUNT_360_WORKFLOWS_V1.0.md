# Phoenix Account 360 V1.0 — Workflows & Actions

**Status:** Phase 11 implementation baseline

Account 360 exposes actionable workflows but does not own the underlying business transactions. Commands are routed to the authoritative owning module/service.

## Action contract

Each action contains an action key, target module, operation, canonical account ID, payload, and idempotency key. Execution requires authenticated tenant context and authorization.

## Owning boundaries

- CRM: activities, notes, follow-ups and relationship actions.
- Sales: quotes and sales orders.
- Accounts: financial records and collection workflows.
- Inventory: deliveries, POD and operational records.
- Approved communication service: customer communication actions.

## Execution rules

1. Validate authenticated user and tenant context.
2. Validate canonical account ID.
3. Validate target module and operation.
4. Check Account 360 action permission.
5. Check owning-module authorization through the command boundary.
6. Require an idempotency key.
7. Route the command without direct database access.
8. Return the owning service result and source reference.
9. Record an auditable action outcome through approved Core infrastructure.
10. Never treat a failed command as successful.

## Idempotency

Repeated requests with the same tenant, account, action and idempotency key must resolve to the same command outcome according to the owning service contract. Account 360 must not generate a second business transaction merely because the client retries.

## Action availability

Actions can be `AVAILABLE`, `DISABLED`, `UNAVAILABLE`, `FORBIDDEN` or `ERROR`. Availability is not a security control; authorization is enforced server-side.

## Resilience

Timeouts, unavailable services and degraded integrations must produce explicit outcomes. Retryable failures may be retried by the host/workflow infrastructure; non-retryable failures must be surfaced without mutation assumptions.

## Automation boundary

Phase 11 provides command orchestration contracts. Scheduled or event-triggered automation may invoke the same command boundary but must retain tenant context, authorization, idempotency and auditability. Business rules remain in the owning module.
