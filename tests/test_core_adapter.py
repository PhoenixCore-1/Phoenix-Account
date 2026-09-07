import pytest

from account_360.core_adapter import (
    MODULE_CODE,
    MODULE_NAME,
    MODULE_VERSION,
    AuditRecord,
    CoreAdapter,
    NavigationRegistration,
    UserContext,
)


class FakeAuthorization:
    def __init__(self):
        self.calls = []

    def require_permission(self, context, permission):
        self.calls.append((context, permission))

    def has_permission(self, context, permission):
        return permission == "account_360.view"


class FakeRegistry:
    def __init__(self):
        self.registered = []

    def register(self, registration):
        self.registered.append(registration)

    def is_enabled(self, tenant_id, module_code):
        return tenant_id == "tenant-1" and module_code == MODULE_CODE


class FakeNavigation:
    def __init__(self):
        self.registered = []

    def register(self, navigation):
        self.registered.append(navigation)


class FakeAudit:
    def __init__(self):
        self.records = []

    def record(self, record):
        self.records.append(record)
        return "audit-1"


class FakeEvents:
    def __init__(self):
        self.published = []
        self.subscriptions = []

    def publish(self, tenant_id, event_type, payload):
        self.published.append((tenant_id, event_type, payload))
        return "event-1"

    def subscribe(self, event_types, handler):
        self.subscriptions.append((event_types, handler))


class FakeConfig:
    def get(self, tenant_id, key, default=None):
        return default if tenant_id != "tenant-1" else "configured"


class FakeServices:
    def request(self, context, service, operation, payload):
        return {"service": service, "operation": operation, "payload": payload}


def make_adapter():
    return CoreAdapter(
        authorization=FakeAuthorization(),
        module_registry=FakeRegistry(),
        navigation=FakeNavigation(),
        audit_service=FakeAudit(),
        event_transport=FakeEvents(),
        configuration=FakeConfig(),
        service_transport=FakeServices(),
    )


def test_registration_is_fixed_for_v1():
    registration = CoreAdapter.registration()
    assert registration.code == MODULE_CODE
    assert registration.name == MODULE_NAME
    assert registration.version == MODULE_VERSION


def test_module_and_navigation_register_through_core():
    adapter = make_adapter()
    adapter.register_module()
    adapter.register_navigation(
        NavigationRegistration(MODULE_CODE, "Account 360", "/accounts", "accounts", 20)
    )

    assert adapter.module_registry.registered[0].code == MODULE_CODE
    assert adapter.navigation.registered[0].route == "/accounts"


def test_wrong_module_navigation_is_rejected():
    adapter = make_adapter()
    with pytest.raises(ValueError):
        adapter.register_navigation(
            NavigationRegistration("sales", "Sales", "/sales")
        )


def test_permission_check_requires_user_and_tenant_context():
    adapter = make_adapter()
    context = UserContext("user-1", "tenant-1")
    adapter.require_permission(context, "account_360.view")
    assert adapter.authorization.calls == [(context, "account_360.view")]

    with pytest.raises(ValueError):
        adapter.require_permission(UserContext("user-1", ""), "account_360.view")

    with pytest.raises(ValueError):
        adapter.require_permission(UserContext("", "tenant-1"), "account_360.view")


def test_licensing_is_tenant_scoped():
    adapter = make_adapter()
    assert adapter.is_enabled("tenant-1") is True
    assert adapter.is_enabled("tenant-2") is False


def test_audit_is_forwarded_to_core():
    adapter = make_adapter()
    record = AuditRecord(
        action="account.view",
        tenant_id="tenant-1",
        user_id="user-1",
        resource_type="account",
        resource_id="account-1",
        outcome="SUCCESS",
        metadata={"source": "test"},
    )
    assert adapter.record_audit(record) == "audit-1"
    assert adapter.audit_service.records == [record]


def test_events_are_forwarded_with_tenant_context():
    adapter = make_adapter()
    context = UserContext("user-1", "tenant-1")
    assert adapter.publish_event(context, "account.updated", {"account_id": "account-1"}) == "event-1"
    assert adapter.event_transport.published[0][0] == "tenant-1"


def test_configuration_is_tenant_scoped():
    adapter = make_adapter()
    assert adapter.get_config("tenant-1", "example") == "configured"
    assert adapter.get_config("tenant-2", "example", "fallback") == "fallback"


def test_service_requests_use_authenticated_context():
    adapter = make_adapter()
    context = UserContext("user-1", "tenant-1")
    result = adapter.service_request(context, "accounts", "get_balance", {"account_id": "a1"})
    assert result["service"] == "accounts"
    assert result["operation"] == "get_balance"

    with pytest.raises(ValueError):
        adapter.service_request(UserContext("user-1", ""), "accounts", "get_balance", {})
