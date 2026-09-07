"""Unified chronological timeline contracts for Phoenix Account 360."""

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .core_adapter import UserContext
from .integration import DomainEvent

TIMELINE_PERMISSION = "account_360.timeline.view"
MAX_PAGE_SIZE = 500


@dataclass(frozen=True)
class TimelineItem:
    event_id: str
    tenant_id: str
    account_id: str
    source_module: str
    source_entity_type: str
    source_record_id: str
    event_type: str
    occurred_at: str
    title: str
    category: str
    summary: str | None = None
    source_version: str | None = None
    source_sequence: int | None = None
    source_reference: str | None = None
    processing_status: str = "PROCESSED"


@dataclass(frozen=True)
class TimelinePage:
    items: Sequence[TimelineItem]
    next_cursor: str | None = None
    as_of: str | None = None
    stale: bool = False


class TimelineStore:
    """Storage boundary for normalized timeline events."""

    def upsert_event(self, item: TimelineItem) -> bool:
        raise NotImplementedError

    def list_events(self, tenant_id: str, account_id: str, limit: int, cursor: str | None,
                    category: str | None = None, source_module: str | None = None) -> TimelinePage:
        raise NotImplementedError


class TimelineSourceUnavailable(Exception):
    """Raised when timeline source/projection data cannot be served."""


class UnifiedTimeline:
    """Normalizes domain events and serves a tenant/account scoped timeline."""

    def __init__(self, *, authorization: Any, store: TimelineStore) -> None:
        self.authorization = authorization
        self.store = store

    def ingest(self, event: DomainEvent) -> bool:
        event.validate()
        if event.account_id is None:
            return False
        item = TimelineItem(
            event_id=event.event_id, tenant_id=event.tenant_id, account_id=event.account_id,
            source_module=event.source_module, source_entity_type=event.source_entity_type,
            source_record_id=event.source_record_id, event_type=event.event_type,
            occurred_at=event.occurred_at,
            title=str(event.payload.get("title") or event.event_type),
            category=str(event.payload.get("category") or event.event_type),
            summary=event.payload.get("summary"), source_version=event.source_version,
            source_sequence=event.source_sequence,
            source_reference=event.payload.get("source_reference"),
        )
        return self.store.upsert_event(item)

    def list(self, context: UserContext, account_id: str, *, limit: int = 100,
             cursor: str | None = None, category: str | None = None,
             source_module: str | None = None) -> TimelinePage:
        if not context.user_id or not context.tenant_id:
            raise ValueError("authenticated tenant context is required")
        if not account_id:
            raise ValueError("account_id is required")
        if limit < 1 or limit > MAX_PAGE_SIZE:
            raise ValueError("limit must be between 1 and 500")
        self.authorization.require_permission(context, TIMELINE_PERMISSION)
        page = self.store.list_events(context.tenant_id, account_id, limit, cursor, category, source_module)
        for item in page.items:
            if item.tenant_id != context.tenant_id or item.account_id != account_id:
                raise ValueError("timeline item violates requested scope")
        # Enforce deterministic newest-first presentation regardless of store ordering.
        ordered = tuple(sorted(page.items, key=lambda item: (item.occurred_at, item.event_id), reverse=True))
        return TimelinePage(ordered, page.next_cursor, page.as_of, page.stale)
