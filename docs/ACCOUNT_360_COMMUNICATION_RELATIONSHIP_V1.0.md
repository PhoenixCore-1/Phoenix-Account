# Phoenix Account 360 V1.0 — Communication & Relationship 360

## 1. Purpose

Phase 8 adds customer relationship and communication context to Account 360. The objective is to let an authorized user understand the relationship with an account and its contacts without making Account 360 the system of record for communications or CRM activity.

## 2. Scope

Account 360 may present approved source-owned references for:

- customer calls;
- WhatsApp/customer communications;
- emails where an approved integration exists;
- meetings;
- visits;
- CRM notes;
- CRM activities;
- tasks;
- follow-ups;
- source-linked conversations;
- relationship roles and contact context;
- communication timeline entries.

## 3. Ownership boundary

CRM and approved communication providers remain authoritative for underlying communication and relationship records.

Account 360 owns only the references/projections required to provide the unified account experience. It must not become a shadow CRM, message store, telephony platform, WhatsApp platform or email mailbox.

Account 360 must never persist external communication credentials, access tokens, session secrets or provider authentication material.

## 4. Canonical association

Every projected communication or relationship item must be associated with:

- `tenant_id`;
- canonical `account_id`;
- optional canonical/contact reference;
- source module/provider;
- source entity type;
- source record/conversation/message identifier;
- source timestamp/version where available.

A source-local customer/contact ID is a reference and must not replace the canonical Account 360 identity.

## 5. Communication types

### Calls

Expose approved call metadata such as direction, participants, time, duration/status and source reference. Call recordings or transcripts are exposed only where an approved source contract and permission allow them.

### WhatsApp

Expose approved customer communication metadata and source-linked conversation/message references. Account 360 does not store provider credentials and does not independently own the WhatsApp conversation.

### Email

Support email context only where a formally approved integration exists. No assumption is made that Account 360 has direct mailbox access.

### Meetings and visits

Present source-linked meetings/visits with date/time, participants, status, subject/context and source reference where exposed by CRM.

## 6. Relationship context

Account 360 may present:

- contacts;
- contact roles;
- relationship type;
- primary/contact indicators;
- account relationship status;
- interaction history;
- assigned relationship owner where exposed;
- follow-up/task references.

Authoritative contact maintenance remains with CRM.

## 7. Query and projection requirements

Communication queries must be:

- tenant scoped;
- permission scoped;
- account/contact scoped;
- bounded and paginated;
- source linked;
- explicit about freshness when projected data is used;
- resilient to unavailable providers/modules.

Projected communication data must remain rebuildable from approved source contracts/events.

## 8. Commands

Where supported, Account 360 may request communication or relationship actions, but execution belongs to the owning service.

Examples include requesting a CRM follow-up, creating a CRM task, opening a source conversation, or initiating an approved communication action. Account 360 must not directly call an external communication provider outside the approved integration boundary.

Commands require authorization, an idempotency key where applicable, source ownership and Core audit handling.

## 9. Privacy and security

Communication content can contain sensitive customer information. Access must therefore be explicitly permission controlled and tenant isolated.

The implementation must support metadata-only projections where full content is not authorized or not required.

Unauthorized users must not receive message bodies, recordings, transcripts, attachments or other protected communication content merely because they can view an account.

## 10. Timeline compatibility

Phase 8 communication/relationship records must be suitable for ingestion into the Phase 9 unified timeline. Each record must retain enough source identity and timestamp information to support deterministic chronological ordering and source drill-down.

## 11. Non-goals

Phase 8 does not implement:

- a new WhatsApp provider;
- a telephony platform;
- an email server/mailbox;
- CRM master-data ownership;
- an independent message database;
- external communication credentials;
- autonomous outbound communication;
- the Phase 9 unified timeline UI.
