from dataclasses import dataclass

import pytest

from account_360.commercial_operational import (
    COMMERCIAL_COMMAND_PERMISSION,
    COMMERCIAL_VIEW_PERMISSION,
    OPERATIONS_COMMAND_PERMISSION,
    OPERATIONS_VIEW_PERMISSION,
    CommercialOperationalView,
    CommercialPage,
    CommercialRecord,
    OperationalPage,
    OperationalRecord,
)
from account_360.core_adapter import UserContext


@dataclass
class FakeAuthorization:
    allowed: set[str]

    def require_permission(self, context, permission):
        if permission not in self.allowed:
            raise PermissionError(permission)


class FakeCommercial:
    def __init__(self, page):
        self.page = page
        self.calls = []

    def list_records(self, context, account_id, record_type, limit, cursor):
        self.calls.append((account_id, record_type, limit, cursor))
        return self.page

    def execute_command(self, context, account_id, operation, payload, idempotency_key):
        self.calls.append((account_id, operation, payload, idempotency_key))
        return {"module": "sales", "operation": operation}


class FakeOperations:
    def __init__(self, page):
        self.page = page
        self.calls = []

    def list_records(self, context, account_id, record_type, limit, cursor):
        self.calls.append((account_id, record_type, limit, cursor))
        return self.page

    def execute_command(self, context, account_id, operation, payload, idempotency_key):
        self.calls.append((account_id, operation, payload, idempotency_key))
        return {"module": "inventory", "operation": operation}


def context():
    return UserContext(user_id="u1", tenant_id="t1")


def test_commercial_query_is_authorized_source_linked_and_bounded():
    page = CommercialPage(
        records=[CommercialRecord("q1", "quote", "a1", "OPEN", 1000, "ZAR", "2026-09-01", "sales:quote:q1")],
        next_cursor="next", source_version="v4", as_of="2026-09-07T06:00:00Z"
    )
    auth = FakeAuthorization({COMMERCIAL_VIEW_PERMISSION})
    source = FakeCommercial(page)
    view = CommercialOperationalView(auth, source, FakeOperations(OperationalPage([], None, None, None)))

    result = view.list_commercial(context(), "a1", limit=50, cursor="c1")

    assert result == page
    assert source.calls == [("a1", None, 50, "c1")]


def test_commercial_permission_is_enforced():
    view = CommercialOperationalView(FakeAuthorization(set()), FakeCommercial(CommercialPage([], None, None, None)), FakeOperations(OperationalPage([], None, None, None)))
    with pytest.raises(PermissionError):
        view.list_commercial(context(), "a1")


def test_operations_permission_is_enforced():
    view = CommercialOperationalView(FakeAuthorization(set()), FakeCommercial(CommercialPage([], None, None, None)), FakeOperations(OperationalPage([], None, None, None)))
    with pytest.raises(PermissionError):
        view.list_operations(context(), "a1")


def test_cross_account_commercial_record_is_rejected():
    page = CommercialPage([CommercialRecord("q1", "quote", "a2", "OPEN", 100, "ZAR", None, "sales:quote:q1")], None, "v1", "now")
    view = CommercialOperationalView(FakeAuthorization({COMMERCIAL_VIEW_PERMISSION}), FakeCommercial(page), FakeOperations(OperationalPage([], None, None, None)))
    with pytest.raises(ValueError, match="requested account"):
        view.list_commercial(context(), "a1")


def test_cross_account_operational_record_is_rejected():
    page = OperationalPage([OperationalRecord("d1", "delivery", "a2", "DELIVERED", None, "inventory:delivery:d1")], None, "v1", "now")
    view = CommercialOperationalView(FakeAuthorization({OPERATIONS_VIEW_PERMISSION}), FakeCommercial(CommercialPage([], None, None, None)), FakeOperations(page))
    with pytest.raises(ValueError, match="requested account"):
        view.list_operations(context(), "a1")


def test_page_limit_is_bounded():
    view = CommercialOperationalView(FakeAuthorization({COMMERCIAL_VIEW_PERMISSION}), FakeCommercial(CommercialPage([], None, None, None)), FakeOperations(OperationalPage([], None, None, None)))
    with pytest.raises(ValueError):
        view.list_commercial(context(), "a1", limit=501)


def test_commercial_command_routes_to_sales_and_requires_idempotency():
    source = FakeCommercial(CommercialPage([], None, None, None))
    view = CommercialOperationalView(FakeAuthorization({COMMERCIAL_COMMAND_PERMISSION}), source, FakeOperations(OperationalPage([], None, None, None)))
    assert view.execute_commercial(context(), "a1", "cancel_quote", {"reason": "test"}, "idem-1")["module"] == "sales"
    with pytest.raises(ValueError):
        view.execute_commercial(context(), "a1", "cancel_quote", {}, "")


def test_operations_command_routes_to_inventory_and_requires_idempotency():
    source = FakeOperations(OperationalPage([], None, None, None))
    view = CommercialOperationalView(FakeAuthorization({OPERATIONS_COMMAND_PERMISSION}), FakeCommercial(CommercialPage([], None, None, None)), source)
    assert view.execute_operations(context(), "a1", "request_return", {"reason": "test"}, "idem-2")["module"] == "inventory"
    with pytest.raises(ValueError):
        view.execute_operations(context(), "a1", "request_return", {}, "")
