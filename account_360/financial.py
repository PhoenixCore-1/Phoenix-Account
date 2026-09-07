"""Financial Account 360 read model and Accounts boundary."""

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .core_adapter import UserContext
from .integration_errors import IntegrationUnavailableError, StaleDataError

FINANCIAL_PERMISSION = "account_360.financial.view"


@dataclass(frozen=True)
class FinancialAccountSummary:
    tenant_id: str
    account_id: str
    credit_limit: Any = None
    credit_status: str | None = None
    balance: Any = None
    exposure: Any = None
    available_credit: Any = None
    currency: str | None = None
    source_version: str | None = None
    as_of: str | None = None
    source_reference: str | None = None


@dataclass(frozen=True)
class FinancialRecord:
    record_id: str
    record_type: str
    account_id: str
    amount: Any = None
    currency: str | None = None
    status: str | None = None
    occurred_at: str | None = None
    source_reference: str | None = None


@dataclass(frozen=True)
class FinancialPage:
    records: Sequence[FinancialRecord]
    next_cursor: str | None
    source_version: str | None = None
    as_of: str | None = None


class AccountsFinancialPort(Protocol):
    """Approved Accounts service boundary; Accounts owns financial truth."""

    def get_summary(self, context: UserContext, account_id: str) -> FinancialAccountSummary: ...

    def list_records(
        self,
        context: UserContext,
        account_id: str,
        record_type: str,
        limit: int,
        cursor: str | None,
    ) -> FinancialPage: ...

    def execute_command(
        self,
        context: UserContext,
        account_id: str,
        operation: str,
        payload: Mapping[str, Any],
        idempotency_key: str,
    ) -> Mapping[str, Any]: ...


class FinancialAccountView:
    """Permission-controlled facade over the authoritative Accounts service."""

    MAX_PAGE_SIZE = 500

    def __init__(self, accounts: AccountsFinancialPort, authorization: Any) -> None:
        self.accounts = accounts
        self.authorization = authorization

    def summary(self, context: UserContext, account_id: str) -> FinancialAccountSummary:
        self._authorize(context, account_id)
        summary = self.accounts.get_summary(context, account_id)
        self._validate_summary(context, summary)
        return summary

    def records(
        self,
        context: UserContext,
        account_id: str,
        record_type: str,
        *,
        limit: int = 100,
        cursor: str | None = None,
    ) -> FinancialPage:
        self._authorize(context, account_id)
        if not record_type:
            raise ValueError("record_type is required")
        if limit < 1 or limit > self.MAX_PAGE_SIZE:
            raise ValueError("limit must be between 1 and 500")
        page = self.accounts.list_records(context, account_id, record_type, limit, cursor)
        if page.as_of is None:
            raise StaleDataError("Financial source freshness metadata is required")
        return page

    def command(
        self,
        context: UserContext,
        account_id: str,
        operation: str,
        payload: Mapping[str, Any],
        idempotency_key: str,
    ) -> Mapping[str, Any]:
        self._authorize(context, account_id)
        if not operation or not idempotency_key:
            raise ValueError("operation and idempotency_key are required")
        return self.accounts.execute_command(context, account_id, operation, payload, idempotency_key)

    def _authorize(self, context: UserContext, account_id: str) -> None:
        if not context.user_id or not context.tenant_id:
            raise ValueError("authenticated user and tenant context are required")
        if not account_id:
            raise ValueError("account_id is required")
        self.authorization.require_permission(context, FINANCIAL_PERMISSION)

    @staticmethod
    def _validate_summary(context: UserContext, summary: FinancialAccountSummary) -> None:
        if summary.tenant_id != context.tenant_id:
            raise IntegrationUnavailableError("Financial source returned a cross-tenant record")
        if summary.account_id != summary.account_id:
            raise IntegrationUnavailableError("Financial source returned an invalid account identity")
        if summary.as_of is None:
            raise StaleDataError("Financial summary freshness metadata is required")
