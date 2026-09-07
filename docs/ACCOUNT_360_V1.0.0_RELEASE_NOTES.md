# Phoenix Account 360 V1.0.0 — Release Notes

## Status

**FROZEN V1.0.0 BASELINE**

## Included

- Account 360 scope and architecture contracts
- Canonical account identity and source-reference resolution
- Tenant-safe cross-module integration ports
- Financial account view routed to Accounts
- Commercial and operational 360 view
- Communication and relationship view including approved WhatsApp/call boundaries
- Unified account timeline with deterministic ordering and idempotent ingestion
- Framework-neutral Account 360 UI presentation model
- Controlled workflows and source-owned commands
- Phoenix Core AI service integration with protected context and action authorization
- Security, tenant-isolation, idempotency, resilience and bounded-query hardening

## Verification

The complete test suite passed with **127/127 tests**.

## Known limitations

Production connectors depend on the approved Phoenix Core and domain-module contracts. External communication credentials and AI provider/runtime configuration remain outside Account 360. Production performance depends on deployed source integrations and projection/cache strategy.

## Compatibility

The `1.0.0` baseline is intended to be maintained through backward-compatible `1.0.x` patches. New business capabilities, ownership changes or contract changes require a new architecture/version gate.
