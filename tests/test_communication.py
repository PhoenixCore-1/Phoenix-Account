from dataclasses import dataclass

import pytest

from account_360.communication import (
    COMMUNICATION_PERMISSION,
    CONTENT_PERMISSION,
    CommunicationAccountView,
    CommunicationPage,
    CommunicationRecord,
    RelationshipPage,
    RelationshipRecord,
)
from account_360.core_adapter import UserContext


@dataclass
class FakeAuthorization:
    allowed: set[str]

    def require_permission(self, context, permission):
        if permission not in self.allowed:
            raise PermissionError(permission)


class FakeSource:
    def __init__(self, page, relationships=None):
        self.page = page
        self.relationships = relationships or RelationshipPage((), None, None, "2026-09-07T08:00:00Z")
        self.calls = []

    def list_communications(self, context, account_id, communication_type, limit, cursor):
        self.calls.append(("communications", account_id, communication_type, limit, cursor))
        return self.page

    def list_relationships(self, context, account_id, limit, cursor):
        self.calls.append(("relationships", account_id, limit, cursor))
        return self.relationships

    def get_content(self, context, account_id, record_id):
        self.calls.append(("content", account_id, record_id))
        return {"record_id": record_id, "body": "protected"}

    def execute(self, context, account_id, operation, payload, idempotency_key):
        self.calls.append(("command", account_id, operation, idempotency_key))
        return {"accepted": True}


def context():
    return UserContext(user_id="u1", tenant_id="t1")


def record(account_id="a1", tenant_id="t1", communication_type="WHATSAPP"):
    return CommunicationRecord("r1", tenant_id, account_id, "c1", "crm", "conversation", "src1", communication_type, "INBOUND", "OPEN", "Hello", "2026-09-07T07:00:00Z", "v1", 1, True, "crm:src1")


def view(page, allowed=None, relationships=None):
    return CommunicationAccountView(authorization=FakeAuthorization(allowed or {COMMUNICATION_PERMISSION, CONTENT_PERMISSION}), source=FakeSource(page, relationships))


def test_communications_are_permission_controlled_and_account_scoped():
    page = CommunicationPage((record(),), None, "v1", "2026-09-07T08:00:00Z")
    assert len(view(page).list_communications(context(), "a1").records) == 1


def test_cross_tenant_communication_rejected():
    with pytest.raises(ValueError, match="cross-tenant"):
        view(CommunicationPage((record(tenant_id="t2"),), None, "v1", "now")).list_communications(context(), "a1")


def test_cross_account_communication_rejected():
    with pytest.raises(ValueError, match="cross-account"):
        view(CommunicationPage((record(account_id="a2"),), None, "v1", "now")).list_communications(context(), "a1")


def test_unsupported_communication_type_rejected():
    with pytest.raises(ValueError, match="unsupported"):
        view(CommunicationPage((), None, "v1", "now")).list_communications(context(), "a1", "SMS")


def test_communication_freshness_required():
    with pytest.raises(ValueError, match="freshness"):
        view(CommunicationPage((record(),), None, "v1", "")).list_communications(context(), "a1")


def test_relationships_are_account_and_tenant_scoped():
    rel = RelationshipRecord("r", "t1", "a1", "c1", "CUSTOMER_CONTACT", "Buyer", "ACTIVE", "crm", "contact", "c1", "v1")
    page = RelationshipPage((rel,), None, "v1", "now")
    assert view(CommunicationPage((), None, "v1", "now"), relationships=page).list_relationships(context(), "a1").records == (rel,)


def test_relationship_cross_tenant_rejected():
    rel = RelationshipRecord("r", "t2", "a1", "c1", "CUSTOMER_CONTACT", None, "ACTIVE", "crm", "contact", "c1", "v1")
    page = RelationshipPage((rel,), None, "v1", "now")
    with pytest.raises(ValueError, match="cross-tenant"):
        view(CommunicationPage((), None, "v1", "now"), relationships=page).list_relationships(context(), "a1")


def test_content_requires_separate_permission():
    v = view(CommunicationPage((), None, "v1", "now"), {COMMUNICATION_PERMISSION})
    with pytest.raises(PermissionError):
        v.get_content(context(), "a1", "r1")


def test_content_is_routed_to_source():
    v = view(CommunicationPage((), None, "v1", "now"))
    assert v.get_content(context(), "a1", "r1")["record_id"] == "r1"


def test_commands_require_idempotency_key():
    v = view(CommunicationPage((), None, "v1", "now"))
    with pytest.raises(ValueError, match="idempotency"):
        v.command(context(), "a1", "create_task", {}, "")


def test_command_routes_to_source():
    v = view(CommunicationPage((), None, "v1", "now"))
    assert v.command(context(), "a1", "create_task", {"title": "Follow up"}, "idem-1")["accepted"] is True


def test_missing_context_rejected():
    v = view(CommunicationPage((), None, "v1", "now"))
    with pytest.raises(ValueError, match="authenticated"):
        v.list_communications(UserContext(user_id="", tenant_id="t1"), "a1")


def test_page_size_is_bounded():
    with pytest.raises(ValueError, match="between 1 and 500"):
        view(CommunicationPage((), None, "v1", "now")).list_communications(context(), "a1", limit=501)


def test_relationship_freshness_required():
    rel = RelationshipPage((), None, "v1", "")
    with pytest.raises(ValueError, match="freshness"):
        view(CommunicationPage((), None, "v1", "now"), relationships=rel).list_relationships(context(), "a1")


def test_record_type_is_validated_from_source():
    with pytest.raises(ValueError, match="unsupported"):
        view(CommunicationPage((record(communication_type="SMS"),), None, "v1", "now")).list_communications(context(), "a1")


def test_account_id_is_required():
    with pytest.raises(ValueError, match="account_id"):
        view(CommunicationPage((), None, "v1", "now")).list_communications(context(), "")
