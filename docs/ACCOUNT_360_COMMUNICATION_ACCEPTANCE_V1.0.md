# Phoenix Account 360 V1.0 — Phase 8 Acceptance Matrix

## Acceptance criteria

| ID | Criterion | Priority |
|---|---|---|
| A360-025 | Communication data is tenant scoped | Critical |
| A360-026 | Communication/relationship access is server-side permission controlled | Critical |
| A360-027 | Records are associated with the correct canonical account | Critical |
| A360-028 | Contact association is source-linked and tenant safe | High |
| A360-029 | Calls are represented without taking telephony ownership | High |
| A360-030 | WhatsApp/customer communications are represented through an approved boundary | Critical |
| A360-031 | Email is supported only through an approved integration | High |
| A360-032 | Meetings and visits remain CRM/source owned | High |
| A360-033 | Notes, activities, tasks and follow-ups remain source/workflow owned | High |
| A360-034 | Communication metadata can be exposed without exposing protected content | Critical |
| A360-035 | Protected message bodies/recordings/transcripts/attachments require explicit authorization | Critical |
| A360-036 | Account 360 stores no external communication credentials | Critical |
| A360-037 | Queries are bounded/paginated and source linked | High |
| A360-038 | Freshness/stale/unavailable state is explicit | High |
| A360-039 | Communication events are idempotent and safe for delayed/out-of-order delivery | Critical |
| A360-040 | Source drill-down references are preserved | High |
| A360-041 | Communication/relationship commands route to the owning service | Critical |
| A360-042 | Commands use authenticated tenant/user context and idempotency where applicable | Critical |
| A360-043 | Integration failures are observable and recoverable | High |
| A360-044 | Normalized records are compatible with the Phase 9 unified timeline | High |
| A360-045 | Existing Phase 0–7 regression suite remains green | Critical |

## Phase 8 gate

Phase 8 may be marked complete only when all applicable acceptance criteria are implemented and verified by automated tests, with no critical security, identity, ownership or privacy failures.
