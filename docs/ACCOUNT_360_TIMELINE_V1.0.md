# Phoenix Account 360 V1.0 — Unified Timeline

## Purpose

Phase 9 provides one chronological, tenant-safe account history assembled from approved source-domain events and Account 360 projections.

## Scope

The timeline can represent events from CRM, Sales, Accounts, Inventory, Procurement and approved communication integrations.

Each item retains its source identity and can link back to the authoritative source record.

## Ordering

Timeline consumers must order events deterministically by occurrence time with stable event identity/version information as the tie-breaker. Source sequence/version metadata must be retained when supplied.

Delayed or out-of-order events must not overwrite newer source state. Duplicate events are idempotently ignored.

## Query behavior

Timeline reads are:

- tenant scoped;
- canonical-account scoped;
- permission controlled;
- bounded/paginated;
- filterable by category and source module;
- explicit about freshness;
- capable of representing stale/unavailable projections.

## Source visibility

Each item should expose source/module context so users can distinguish CRM, Sales, Accounts, Inventory, Procurement and communication activity. Source ownership is never transferred to Account 360.

## Drill-down

A timeline item must retain enough source identity to open or request the authoritative source record through an approved service boundary.

## Security

Timeline permission checks are server side. Returned items are revalidated against the requesting tenant and canonical account. Protected communication content remains subject to its own content permission.

## Phase 10 hand-off

The UI may consume `TimelinePage` and `TimelineItem` without directly accessing timeline storage. The UI should present loading, empty, stale, unavailable and error states and preserve source/context badges.
