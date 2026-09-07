import pytest

from account_360.core_adapter import UserContext
from account_360.financial import (
    FINANCIAL_PERMISSION,
    FinancialAccountSummary,
    FinancialAccountView,
    FinancialPage,
    FinancialRecord,
)
from account_360.integration_errors import IntegrationUnavailableError, StaleDataError


class FakeAuthorization:
    def __init__(self):
        self.calls = []

    def require_permission(self, context, permission):
        self.calls.append((context, permission))


class FakeAccounts:
    def __init__(self):
        self.summary_result = FinancialAccountSummary(
            tenant_id="tenant-1", account_id="account-1", balance=100, exposure=100,
            credit_limit=1000, available_credit=900, currency="ZAR", as_of="2026-09-07T08:00:00Z",
            source_version="42", source_reference="accounts/customer/account-1"
        )
        self.page_result = FinancialPage(
            records=[FinancialRecord("inv-1", "invoice", "account-1", 100, "ZAR")],
            next_cursor="next-1", source_version="42", as_of="2026-09-07T08:00:00Z"
        )
        self.commands = []

    def get_summary(self, context, account_id):
        return self.summary_result

    def list_records(self, context, account_id, record_type, limit, cursor):
        return self.page_result

    def execute_command(self, context, account_id, operation, payload, idempotency_key):
        self.commands.append((context, account_id, operation, payload, idempotency_key))
        return {"accepted": True, "idempotency_key": idempotency_key}


def view():
    return FinancialAccountView(FakeAccounts(), FakeAuthorization())


def test_summary_is_permission_controlled_and_source_linked():
    result = view().summary(UserContext("user-1", "tenant-1"), "account-1")
    assert result.balance == 100
    assert result.source_reference == "accounts/customer/account-1"


def test_summary_rejects_cross_tenant_source_result():
    v = view()
    v.accounts.summary_result = FinancialAccountSummary("tenant-2", "account-1", as_of="now")
    with pytest.raises(IntegrationUnavailableError):
        v.summary(UserContext("user-1", "tenant-1"), "account-1")


def test_summary_requires_freshness_metadata():
    v = view()
    v.accounts.summary_result = FinancialAccountSummary("tenant-1", "account-1")
    with pytest.raises(StaleDataError):
        v.summary(UserContext("user-1", "tenant-1"), "account-1")


def test_records_are_bounded_and_account_scoped():
    v = view()
    page = v.records(UserContext("user-1", "tenant-1"), "account-1", "invoice", limit=50)
    assert page.next_cursor == "next-1"
    assert len(page.records) == 1

    with pytest.raises(ValueError, match="limit"):
        v.records(UserContext("user-1", "tenant-1"), "account-1", "invoice", limit=501)


def test_records_reject_mismatched_account():
    v = view()
    v.accounts.page_result = FinancialPage(
        [FinancialRecord("inv-1", "invoice", "account-2")], None, as_of="now"
    )
    with pytest.raises(IntegrationUnavailableError):
        v.records(UserContext("user-1", "tenant-1"), "account-1", "invoice")


def test_financial_command_requires_idempotency_and_routes_to_accounts():
    v = view()
    result = v.command(
        UserContext("user-1", "tenant-1"), "account-1", "request_statement", {}, "cmd-1"
    )
    assert result["accepted"] is True
    assert v.accounts.commands[0][2] == "request_statement"


def test_financial_permission_constant_is_stable():
    assert FINANCIAL_PERMISSION == "account_360.financial.view"


def test_missing_authenticated_context_is_rejected():
    with pytest.raises(ValueError):
        view().summary(UserContext("", "tenant-1"), "account-1")
