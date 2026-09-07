from dataclasses import dataclass, field

import pytest

from account_360.core_adapter import UserContext
from account_360.workflows import (
    ACTION_PERMISSION,
    Account360ActionService,
    ActionRequest,
    ActionState,
)


@dataclass
class FakeAuthorization:
    allowed: set[str]

    def has_permission(self, context, permission):
        return permission in self.allowed

    def require_permission(self, context, permission):
        if permission not in self.allowed:
            raise PermissionError(permission)


@dataclass
class FakeCommandPort:
    calls: list = field(default_factory=list)
    result: dict = field(default_factory=lambda: {"source_reference": "sales:quote:Q1", "status": "CREATED"})
    error: Exception | None = None

    def execute(self, request):
        self.calls.append(request)
        if self.error:
            raise self.error
        return self.result


@dataclass
class FakeAvailability:
    state: ActionState = ActionState.AVAILABLE

    def check(self, request):
        return self.state


@dataclass
class FakeAudit:
    records: list = field(default_factory=list)

    def record(self, record):
        self.records.append(record)
        return "audit-1"


def request(**overrides):
    values = dict(
        context=UserContext(user_id="u1", tenant_id="t1"),
        action_key="sales.quote.create",
        target_module="sales",
        operation="create_quote",
        account_id="a1",
        payload={"lines": []},
        idempotency_key="idem-1",
    )
    values.update(overrides)
    return ActionRequest(**values)


def service(allowed=True, **kwargs):
    auth = FakeAuthorization({ACTION_PERMISSION} if allowed else set())
    return Account360ActionService(authorization=auth, command_port=kwargs.pop("command", FakeCommandPort()), **kwargs)


def test_request_requires_authentication_and_tenant():
    with pytest.raises(ValueError):
        request(context=UserContext(user_id="", tenant_id="t1")).validate()
    with pytest.raises(ValueError):
        request(context=UserContext(user_id="u1", tenant_id="")).validate()


def test_request_requires_supported_target_and_idempotency():
    with pytest.raises(ValueError):
        request(target_module="unknown").validate()
    with pytest.raises(ValueError):
        request(idempotency_key="").validate()


def test_check_returns_forbidden_without_action_permission():
    svc = service(allowed=False)
    assert svc.check(request()) == ActionState.FORBIDDEN


def test_execute_requires_action_permission():
    svc = service(allowed=False)
    with pytest.raises(PermissionError):
        svc.execute(request())


def test_check_respects_action_availability():
    svc = service(availability=FakeAvailability(ActionState.UNAVAILABLE))
    assert svc.check(request()) == ActionState.UNAVAILABLE


def test_execute_routes_to_owning_command_port():
    command = FakeCommandPort()
    svc = service(command=command)
    result = svc.execute(request())
    assert result.state == ActionState.AVAILABLE
    assert result.source_reference == "sales:quote:Q1"
    assert command.calls[0].target_module == "sales"
    assert command.calls[0].idempotency_key == "idem-1"


def test_unavailable_action_does_not_execute_command():
    command = FakeCommandPort()
    svc = service(command=command, availability=FakeAvailability(ActionState.DISABLED))
    result = svc.execute(request())
    assert result.state == ActionState.DISABLED
    assert command.calls == []


def test_command_failure_is_not_reported_as_success():
    command = FakeCommandPort(error=RuntimeError("Sales unavailable"))
    svc = service(command=command)
    result = svc.execute(request())
    assert result.state == ActionState.ERROR
    assert "unavailable" in result.message.lower()


def test_success_is_audited():
    audit = FakeAudit()
    svc = service(audit=audit)
    result = svc.execute(request())
    assert result.state == ActionState.AVAILABLE
    assert audit.records[0].tenant_id == "t1"
    assert audit.records[0].resource_id == "a1"
    assert audit.records[0].outcome == "SUCCESS"


def test_failure_is_audited():
    audit = FakeAudit()
    svc = service(audit=audit, command=FakeCommandPort(error=RuntimeError("failed")))
    result = svc.execute(request())
    assert result.state == ActionState.ERROR
    assert audit.records[0].outcome == "ERROR"


def test_action_result_preserves_account_scope():
    svc = service()
    result = svc.execute(request(account_id="a99"))
    assert result.account_id == "a99"
