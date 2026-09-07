from dataclasses import dataclass

import pytest

from account_360.core_adapter import UserContext
from account_360.integration import DomainEvent
from account_360.timeline import TIMELINE_PERMISSION, TimelineItem, TimelinePage, UnifiedTimeline


@dataclass
class FakeAuthorization:
    allowed: bool = True

    def require_permission(self, context, permission):
        if not self.allowed:
            raise PermissionError(permission)


class FakeStore:
    def __init__(self, page=None):
        self.page = page or TimelinePage(items=[])
        self.items = []

    def upsert_event(self, item):
        if any(existing.event_id == item.event_id for existing in self.items):
            return False
        self.items.append(item)
        return True

    def list_events(self, tenant_id, account_id, limit, cursor, category=None, source_module=None):
        return self.page


def context():
    return UserContext(user_id="u1", tenant_id="t1")


def event(**overrides):
    values = dict(
        tenant_id="t1", account_id="a1", source_module="crm",
        source_entity_type="interaction", source_record_id="r1",
        event_id="e1", event_type="CALL", occurred_at="2026-09-07T08:00:00Z",
        received_at="2026-09-07T08:01:00Z", producer_version="1.0",
        payload={"title": "Customer call", "category": "COMMUNICATION", "summary": "Discussed order"},
    )
    values.update(overrides)
    return DomainEvent(**values)


def test_ingest_normalizes_event_and_preserves_source_reference():
    store = FakeStore()
    timeline = UnifiedTimeline(authorization=FakeAuthorization(), store=store)
    assert timeline.ingest(event()) is True
    item = store.items[0]
    assert item.account_id == "a1"
    assert item.source_module == "crm"
    assert item.source_record_id == "r1"
    assert item.title == "Customer call"


def test_duplicate_event_is_idempotent():
    store = FakeStore()
    timeline = UnifiedTimeline(authorization=FakeAuthorization(), store=store)
    assert timeline.ingest(event()) is True
    assert timeline.ingest(event()) is False
    assert len(store.items) == 1


def test_event_without_account_is_not_projected():
    store = FakeStore()
    timeline = UnifiedTimeline(authorization=FakeAuthorization(), store=store)
    assert timeline.ingest(event(account_id=None)) is False
    assert store.items == []


def test_list_requires_permission():
    timeline = UnifiedTimeline(authorization=FakeAuthorization(allowed=False), store=FakeStore())
    with pytest.raises(PermissionError):
        timeline.list(context(), "a1")


def test_list_requires_authenticated_context():
    timeline = UnifiedTimeline(authorization=FakeAuthorization(), store=FakeStore())
    with pytest.raises(ValueError):
        timeline.list(UserContext(user_id="", tenant_id="t1"), "a1")


def test_list_bounds_page_size():
    timeline = UnifiedTimeline(authorization=FakeAuthorization(), store=FakeStore())
    with pytest.raises(ValueError):
        timeline.list(context(), "a1", limit=501)


def test_list_rejects_cross_tenant_item():
    page = TimelinePage(items=[TimelineItem(
        event_id="e1", tenant_id="t2", account_id="a1", source_module="crm",
        source_entity_type="interaction", source_record_id="r1", event_type="CALL",
        occurred_at="2026-09-07T08:00:00Z", title="Call", category="COMMUNICATION"
    )])
    timeline = UnifiedTimeline(authorization=FakeAuthorization(), store=FakeStore(page))
    with pytest.raises(ValueError):
        timeline.list(context(), "a1")


def test_list_rejects_cross_account_item():
    page = TimelinePage(items=[TimelineItem(
        event_id="e1", tenant_id="t1", account_id="a2", source_module="crm",
        source_entity_type="interaction", source_record_id="r1", event_type="CALL",
        occurred_at="2026-09-07T08:00:00Z", title="Call", category="COMMUNICATION"
    )])
    timeline = UnifiedTimeline(authorization=FakeAuthorization(), store=FakeStore(page))
    with pytest.raises(ValueError):
        timeline.list(context(), "a1")


def test_list_passes_filters_and_pagination_to_store():
    class RecordingStore(FakeStore):
        def list_events(self, *args):
            self.args = args
            return self.page

    store = RecordingStore()
    timeline = UnifiedTimeline(authorization=FakeAuthorization(), store=store)
    timeline.list(context(), "a1", limit=25, cursor="c1", category="SALES", source_module="sales")
    assert store.args == ("t1", "a1", 25, "c1", "SALES", "sales")


def test_permission_constant_is_stable():
    assert TIMELINE_PERMISSION == "account_360.timeline.view"
