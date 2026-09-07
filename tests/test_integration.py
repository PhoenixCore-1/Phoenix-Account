import pytest

from account_360.core_adapter import UserContext
from account_360.integration import (
    CommandRequest,
    CrossModuleGateway,
    DomainEvent,
    QueryRequest,
    QueryResult,
)


class FakeGatewayPort:
    def __init__(self):
        self.queries = []
        self.commands = []

    def query(self, request):
        self.queries.append(request)
        return QueryResult(request.source_module, request.operation, [{"account_id": request.account_id}], as_of="2026-09-07T08:00:00Z")

    def execute(self, request):
        self.commands.append(request)
        return {"accepted": True, "idempotency_key": request.idempotency_key}


def test_query_is_bounded_and_tenant_context_is_forwarded():
    port = FakeGatewayPort()
    gateway = CrossModuleGateway(port, port)
    request = QueryRequest(
        UserContext("user-1", "tenant-1"), "accounts", "get_balance", "account-1", {}, limit=50
    )
    result = gateway.query(request)
    assert result.records[0]["account_id"] == "account-1"
    assert port.queries[0].context.tenant_id == "tenant-1"


def test_query_rejects_unknown_module():
    request = QueryRequest(UserContext("u", "t"), "unknown", "get", "a", {})
    with pytest.raises(ValueError, match="unsupported source module"):
        request.validate()


def test_query_rejects_unbounded_limit():
    request = QueryRequest(UserContext("u", "t"), "crm", "get", "a", {}, limit=501)
    with pytest.raises(ValueError, match="limit"):
        request.validate()


def test_command_requires_idempotency_key_and_routes_to_owner():
    port = FakeGatewayPort()
    gateway = CrossModuleGateway(port, port)
    request = CommandRequest(UserContext("u", "tenant-1"), "accounts", "request_statement", "a", {}, "cmd-1")
    result = gateway.execute(request)
    assert result["accepted"] is True
    assert port.commands[0].target_module == "accounts"


def test_command_rejects_unknown_target():
    request = CommandRequest(UserContext("u", "t"), "unknown", "do", "a", {}, "cmd-1")
    with pytest.raises(ValueError, match="unsupported target module"):
        request.validate()


def test_domain_event_validates_source_identity():
    event = DomainEvent(
        tenant_id="tenant-1",
        account_id="account-1",
        source_module="crm",
        source_entity_type="activity",
        source_record_id="crm-1",
        event_id="event-1",
        event_type="activity.created",
        occurred_at="2026-09-07T08:00:00Z",
        received_at="2026-09-07T08:00:01Z",
        producer_version="1.0",
        payload={"type": "CALL"},
        source_sequence=10,
    )
    event.validate()


def test_domain_event_rejects_unknown_source():
    event = DomainEvent(
        tenant_id="tenant-1", account_id="a", source_module="unknown",
        source_entity_type="x", source_record_id="r", event_id="e",
        event_type="x.created", occurred_at="now", received_at="now",
        producer_version="1", payload={}
    )
    with pytest.raises(ValueError, match="unsupported source module"):
        event.validate()
