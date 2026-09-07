from dataclasses import dataclass, field

import pytest

from account_360.ai import (
    AIContextItem,
    AICapability,
    AIRequest,
    AIResponse,
    Account360AI,
    AI_PERMISSION,
    AI_ACTION_PERMISSION,
    COMMUNICATION_CONTENT_PERMISSION,
)
from account_360.core_adapter import UserContext


@dataclass
class FakeAuthorization:
    allowed: set[str]

    def require_permission(self, context, permission):
        if permission not in self.allowed:
            raise PermissionError(permission)

    def has_permission(self, context, permission):
        return permission in self.allowed


@dataclass
class FakeAI:
    requests: list = field(default_factory=list)

    def run(self, request):
        self.requests.append(request)
        return AIResponse(request.capability, {"answer": "ok"})


@dataclass
class FakeExecutor:
    calls: list = field(default_factory=list)

    def execute(self, context, account_id, action, idempotency_key):
        self.calls.append((context, account_id, action, idempotency_key))
        return {"status": "accepted"}


def ctx():
    return UserContext(user_id="u1", tenant_id="t1")


def request(capability=AICapability.ASK, items=(), instruction="Explain account risk"):
    return AIRequest(ctx(), "a1", capability, items, instruction=instruction, request_id="r1")


def test_request_requires_identity_and_request_id():
    with pytest.raises(ValueError):
        AIRequest(UserContext("u1", "t1"), "a1", AICapability.SUMMARIZE, (), request_id="").validate()


def test_context_item_requires_source_identity():
    with pytest.raises(ValueError):
        request(items=(AIContextItem("", "order", "o1", {}),)).validate()


def test_context_is_bounded():
    items = tuple(AIContextItem("sales", "order", str(i), {}) for i in range(101))
    with pytest.raises(ValueError):
        request(items=items).validate()


def test_instruction_required_for_ask():
    with pytest.raises(ValueError):
        request(instruction=None).validate()


def test_ai_permission_is_required():
    service = FakeAI()
    facade = Account360AI(authorization=FakeAuthorization(set()), ai_service=service, action_executor=FakeExecutor())
    with pytest.raises(PermissionError):
        facade.run(request())


def test_ai_context_filters_sensitive_content():
    service = FakeAI()
    facade = Account360AI(authorization=FakeAuthorization({AI_PERMISSION}), ai_service=service, action_executor=FakeExecutor())
    req = request(items=(AIContextItem("crm", "note", "n1", "safe"), AIContextItem("whatsapp", "message", "m1", "secret", sensitive=True)))
    facade.run(req)
    assert [item.source_id for item in service.requests[0].context_items] == ["n1"]


def test_authorized_ai_context_can_include_sensitive_content():
    service = FakeAI()
    auth = FakeAuthorization({AI_PERMISSION, COMMUNICATION_CONTENT_PERMISSION})
    facade = Account360AI(authorization=auth, ai_service=service, action_executor=FakeExecutor())
    req = request(items=(AIContextItem("whatsapp", "message", "m1", "secret", sensitive=True),))
    facade.run(req)
    assert service.requests[0].context_items[0].source_id == "m1"


def test_ai_request_preserves_tenant_account_and_sources():
    service = FakeAI()
    facade = Account360AI(authorization=FakeAuthorization({AI_PERMISSION}), ai_service=service, action_executor=FakeExecutor())
    item = AIContextItem("sales", "order", "o1", {"total": 10}, as_of="2026-09-07T08:00:00Z")
    facade.run(request(items=(item,)))
    sent = service.requests[0]
    assert sent.context.tenant_id == "t1"
    assert sent.account_id == "a1"
    assert sent.context_items[0].as_of == "2026-09-07T08:00:00Z"


def test_proposed_action_cannot_execute_without_action_permission():
    facade = Account360AI(authorization=FakeAuthorization({AI_PERMISSION}), ai_service=FakeAI(), action_executor=FakeExecutor())
    req = request(AICapability.EXECUTE_AUTHORIZED_ACTION, instruction=None)
    response = AIResponse(AICapability.PROPOSE_ACTION, {}, proposed_action={"target_module": "sales", "operation": "create_quote"})
    with pytest.raises(PermissionError):
        facade.execute_proposed_action(req, response, "idem-1")


def test_action_execution_requires_idempotency_key_and_routes_to_executor():
    executor = FakeExecutor()
    auth = FakeAuthorization({AI_PERMISSION, AI_ACTION_PERMISSION})
    facade = Account360AI(authorization=auth, ai_service=FakeAI(), action_executor=executor)
    req = request(AICapability.EXECUTE_AUTHORIZED_ACTION, instruction=None)
    response = AIResponse(AICapability.PROPOSE_ACTION, {}, proposed_action={"target_module": "accounts", "operation": "start_collection"})
    with pytest.raises(ValueError):
        facade.execute_proposed_action(req, response, "")
    result = facade.execute_proposed_action(req, response, "idem-1")
    assert result == {"status": "accepted"}
    assert executor.calls[0][1:] == ("a1", {"target_module": "accounts", "operation": "start_collection"}, "idem-1")


def test_execution_rejects_missing_proposal():
    auth = FakeAuthorization({AI_ACTION_PERMISSION})
    facade = Account360AI(authorization=auth, ai_service=FakeAI(), action_executor=FakeExecutor())
    req = request(AICapability.EXECUTE_AUTHORIZED_ACTION, instruction=None)
    with pytest.raises(ValueError):
        facade.execute_proposed_action(req, AIResponse(AICapability.PROPOSE_ACTION, {}), "idem-1")
