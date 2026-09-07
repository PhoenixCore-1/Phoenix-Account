# Phoenix Account 360 V1.0 — AI Account Intelligence Contract

**Status:** Phase 12 implementation baseline

**Module code:** `account_360`

**Version:** `1.0.0`

## 1. Purpose

Account 360 consumes Phoenix Core AI services to provide account-specific intelligence. Account 360 does not implement, host, or own an AI provider/runtime.

Phoenix Core remains responsible for provider independence, tenant isolation, authorization, context filtering, governance, audit, usage/cost controls and action authorization.

## 2. Supported capabilities

The Account 360 intelligence boundary supports:

- ASK
- SUMMARIZE
- EXTRACT
- RECOMMEND
- PREDICT
- DETECT
- CLASSIFY
- GENERATE
- PROPOSE_ACTION
- EXECUTE_AUTHORIZED_ACTION

Availability of a capability is configuration- and permission-dependent.

## 3. Context boundary

AI context must be explicitly supplied and tenant/account scoped. The context may contain approved Account 360 projections from CRM, Sales, Accounts, Inventory, Procurement, communications and timeline data.

The context must retain source references and freshness metadata where available. Sensitive communication content is included only when the user has the separate content permission and the source contract allows it.

The AI layer must never discover or query arbitrary databases, tenants or records.

## 4. Request contract

Every request contains:

- authenticated user context;
- tenant ID;
- canonical account ID;
- capability;
- bounded context items;
- user question/instruction where applicable;
- requested output format where applicable;
- optional action intent;
- correlation/request ID.

## 5. Response contract

Responses expose:

- capability;
- result;
- source references used;
- freshness/as-of information where available;
- confidence/uncertainty when supplied by Core AI;
- proposed actions separately from executed actions;
- provider-independent metadata only;
- audit/correlation reference where supplied.

## 6. Action safety

AI may recommend or propose actions. It may execute an action only when:

1. the user is authorized;
2. the action is permitted by Account 360 workflow rules;
3. the owning module authorizes the command;
4. an idempotency key is supplied;
5. Core/approved audit requirements are satisfied.

AI output alone is never sufficient authorization.

## 7. Prohibited behavior

Account 360 AI must not:

- bypass Core authorization;
- bypass owning-module commands;
- invent financial facts when source data is unavailable;
- present stale data as current;
- expose cross-tenant or cross-account information;
- store provider credentials or secrets;
- silently execute destructive/financial actions;
- treat generated text as authoritative source data.

## 8. Governance

AI requests and actions follow Core AI governance, audit and usage/cost controls. Account 360 may supply domain-specific context and capability metadata but cannot weaken Core controls.

## 9. Phase 12 boundary

Phase 12 establishes the Account 360 AI contract and safe orchestration facade. Provider selection, model execution, prompt infrastructure and global AI governance remain Core responsibilities.
