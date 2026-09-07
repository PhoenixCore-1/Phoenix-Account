import pytest

from account_360.ai import AIContextItem, AICapability, AIRequest, AIResponse, Account360AI, AI_ACTION_PERMISSION, AI_PERMISSION, COMMUNICATION_CONTENT_PERMISSION
from account_360.core_adapter import UserContext
from account_360.integration import CommandRequest, CrossModuleGateway, QueryRequest
from account_360.timeline import TimelineItem, TimelinePage, UnifiedTimeline


class Auth:
    def __init__(self, permissions=()): self.permissions = set(permissions)
    def require_permission(self, context, permission):
        if permission not in self.permissions: raise PermissionError(permission)
    def has_permission(self, context, permission): return permission in self.permissions


def ctx(user="u1", tenant="t1"): return UserContext(user_id=user, tenant_id=tenant)


def test_query_requires_authenticated_context():
    req = QueryRequest(UserContext("", ""), "sales", "orders", "a1", {}, 1)
    with pytest.raises(ValueError): req.validate()


def test_command_requires_authenticated_context():
    req = CommandRequest(UserContext("", ""), "sales", "create_quote", "a1", {}, "i1")
    with pytest.raises(ValueError): req.validate()


def test_query_rejects_empty_operation():
    req = QueryRequest(ctx(), "sales", "", "a1", {}, 1)
    with pytest.raises(ValueError): req.validate()


def test_query_rejects_page_above_500():
    req = QueryRequest(ctx(), "sales", "orders", "a1", {}, 501)
    with pytest.raises(ValueError): req.validate()


def test_command_requires_idempotency():
    req = CommandRequest(ctx(), "accounts", "start_collection", "a1", {}, "")
    with pytest.raises(ValueError): req.validate()


class Store:
    def __init__(self, items): self.items = items
    def upsert_event(self, item): return True
    def list_events(self, tenant_id, account_id, limit, cursor, category=None, source_module=None):
        return TimelinePage(self.items, "next", "2026-09-07T08:00:00Z", False)


def item(event_id, occurred_at, tenant="t1", account="a1"):
    return TimelineItem(event_id, tenant, account, "sales", "order", event_id, "ORDER", occurred_at, "Order", "sales")


def test_timeline_is_newest_first_even_if_store_is_unsorted():
    store = Store([item("old", "2026-01-01T00:00:00Z"), item("new", "2026-02-01T00:00:00Z")])
    page = UnifiedTimeline(authorization=Auth({"account_360.timeline.view"}), store=store).list(ctx(), "a1")
    assert [x.event_id for x in page.items] == ["new", "old"]


def test_timeline_tie_break_is_deterministic():
    store = Store([item("b", "2026-02-01T00:00:00Z"), item("a", "2026-02-01T00:00:00Z")])
    page = UnifiedTimeline(authorization=Auth({"account_360.timeline.view"}), store=store).list(ctx(), "a1")
    assert [x.event_id for x in page.items] == ["b", "a"]


def test_timeline_rejects_cross_tenant_item():
    store = Store([item("x", "2026-01-01T00:00:00Z", tenant="t2")])
    with pytest.raises(ValueError): UnifiedTimeline(authorization=Auth({"account_360.timeline.view"}), store=store).list(ctx(), "a1")


def test_timeline_rejects_cross_account_item():
    store = Store([item("x", "2026-01-01T00:00:00Z", account="a2")])
    with pytest.raises(ValueError): UnifiedTimeline(authorization=Auth({"account_360.timeline.view"}), store=store).list(ctx(), "a1")


def test_timeline_pagination_is_bounded():
    with pytest.raises(ValueError): UnifiedTimeline(authorization=Auth({"account_360.timeline.view"}), store=Store([])).list(ctx(), "a1", limit=501)


class AI:
    def run(self, request): return AIResponse(request.capability, "ok")

class Executor:
    def execute(self, context, account_id, action, idempotency_key): return {"ok": True}


def test_ai_does_not_send_sensitive_context_without_permission():
    auth = Auth({AI_PERMISSION})
    ai = Account360AI(authorization=auth, ai_service=AI(), action_executor=Executor())
    req = AIRequest(ctx(), "a1", AICapability.SUMMARIZE, (AIContextItem("crm", "note", "n1", "x", sensitive=True),), request_id="r1")
    class Capture:
        def run(self, request):
            assert request.context_items == ()
            return AIResponse(request.capability, "ok")
    ai.ai_service = Capture()
    ai.run(req)


def test_ai_sensitive_context_requires_explicit_content_permission():
    auth = Auth({AI_PERMISSION, COMMUNICATION_CONTENT_PERMISSION})
    ai = Account360AI(authorization=auth, ai_service=AI(), action_executor=Executor())
    req = AIRequest(ctx(), "a1", AICapability.SUMMARIZE, (AIContextItem("whatsapp", "message", "m1", "secret", sensitive=True),), request_id="r1")
    class Capture:
        def run(self, request):
            assert len(request.context_items) == 1
            return AIResponse(request.capability, "ok")
    ai.ai_service = Capture()
    ai.run(req)


def test_ai_action_execution_requires_explicit_action_permission():
    auth = Auth({AI_PERMISSION})
    ai = Account360AI(authorization=auth, ai_service=AI(), action_executor=Executor())
    req = AIRequest(ctx(), "a1", AICapability.EXECUTE_AUTHORIZED_ACTION, (), request_id="r1")
    response = AIResponse(AICapability.PROPOSE_ACTION, "ok", proposed_action={"operation": "x"})
    with pytest.raises(PermissionError): ai.execute_proposed_action(req, response, "id1")


def test_ai_action_execution_requires_idempotency_key():
    auth = Auth({AI_ACTION_PERMISSION})
    ai = Account360AI(authorization=auth, ai_service=AI(), action_executor=Executor())
    req = AIRequest(ctx(), "a1", AICapability.EXECUTE_AUTHORIZED_ACTION, (), request_id="r1")
    response = AIResponse(AICapability.PROPOSE_ACTION, "ok", proposed_action={"operation": "x"})
    with pytest.raises(ValueError): ai.execute_proposed_action(req, response, "")
