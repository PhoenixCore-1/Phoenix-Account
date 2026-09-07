# Phoenix Account 360 V1.0 — Communication & Relationship Contract

## 1. Contract principle

Account 360 consumes communication and relationship information through approved service/event boundaries. It does not access CRM, communicator, WhatsApp, telephony or email databases directly.

## 2. Source ownership

| Domain | Authoritative owner | Account 360 role |
|---|---|---|
| Contacts | CRM | Reference/projection |
| Relationship roles | CRM | Reference/projection |
| Calls | Approved CRM/communication service | Reference/projection |
| WhatsApp | Approved communication service/CRM integration | Reference/projection |
| Email | Approved email/CRM integration | Reference/projection |
| Meetings | CRM | Reference/projection |
| Visits | CRM | Reference/projection |
| Notes | CRM/source system | Reference/projection |
| Activities | CRM | Reference/projection |
| Tasks | CRM/workflow owner | Reference/projection |
| Follow-ups | CRM/workflow owner | Reference/projection |

## 3. Canonical reference contract

Every communication/relationship record supplied to Account 360 must provide, where applicable:

- tenant ID;
- canonical account ID;
- contact/reference ID where applicable;
- source module/provider;
- source entity type;
- source record ID;
- event/interaction ID where applicable;
- occurred/created timestamp;
- source version or sequence where available.

## 4. Communication record contract

A communication record should support the following normalized fields:

- `record_id`;
- `account_id`;
- `contact_id` when available;
- `source_module`;
- `source_entity_type`;
- `source_record_id`;
- `communication_type` (`CALL`, `WHATSAPP`, `EMAIL`, `MEETING`, `VISIT`, `NOTE`, `ACTIVITY`, `TASK`, `FOLLOW_UP`);
- `direction` where applicable;
- `status`;
- `subject/title`;
- participant references;
- occurred timestamp;
- source version/sequence where available;
- content availability classification;
- source drill-down reference.

Full content is optional and must only be returned where authorized by the owning service.

## 5. Query contract

Communication queries must accept authenticated Core context and canonical account scope. Results must be bounded/paginated and include source/freshness metadata where projected.

Queries must reject or prevent cross-tenant and cross-account data leakage.

## 6. Event contract

Communication events must follow the Account 360 domain-event requirements and include enough identity/version information to process duplicates and out-of-order events safely.

At minimum, events must identify tenant, source, event ID, event type, timestamp and source record. Canonical account/contact references should be supplied when known.

## 7. Content access contract

Communication metadata and communication content are separate authorization concerns. A user may be allowed to see that a communication occurred without being allowed to read its content.

The owning service must enforce content-level permissions before returning protected bodies, transcripts, recordings or attachments.

## 8. Command contract

Commands initiated from Account 360 must be routed to the owning service. Examples:

- create/request CRM task;
- create/request follow-up;
- open source conversation;
- initiate an approved communication action.

Commands must carry authenticated tenant/user context and use idempotency controls where the operation is not naturally idempotent.

## 9. Provider boundary

External communication providers must remain behind an approved integration boundary. Provider credentials, OAuth secrets, API keys, session tokens and connection secrets must never be stored by Account 360.

## 10. Failure and freshness

If CRM or a communication provider is unavailable, Account 360 must distinguish unavailable/stale source data from authoritative current data. Integration failure must be observable and retry/reconciliation capable.

## 11. Phase 9 hand-off

The normalized communication contract must be compatible with the existing `account_360_timeline_events` model so Phase 9 can consume communication events without redefining source ownership or identity.
