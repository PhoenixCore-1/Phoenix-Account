"""Commercial and operational Account 360 views.

Sales and Inventory remain system-of-record owners. This module only consumes
approved ports and routes commands to the owning domain module.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .core_adapter import UserContext

COMMERCIAL_VIEW_PERMISSION = "account_360.commercial.view"
OPERATIONS_VIEW_PERMISSION = "account_360.operations.view"
COMMERCIAL_COMMAND_PERMISSION = "account_360.commercial.command"
OPERATIONS_COMMAND_PERMISSION = "account_360.operations.command"


@dataclass(frozen=True)
class CommercialRecord:
    record_id: str
    record_type: str
    account_id: str
    status: str
    total: float | None
    currency: str | None
    occurred_at: str | None
    source_reference: str


@dataclass(frozen=True)
class OperationalRecord:
    record_id: str
    record_type: str
    account_id: str
    status: str
    occurred_at: str | None
    source_reference: str


@dataclass(frozen=True)
class CommercialPage:
    records: Sequence[CommercialRecord]
    next_cursor: str | None
    source_version: str | None
    as_of: str | None


@dataclass(frozen=True)
class OperationalPage:
    records: Sequence[OperationalRecord]
    next_cursor: str | None
    source_version: str | None
    as_of: str | None


class CommercialPort(Protocol):
    def list_records(self, context: UserContext, account_id: str, record_type: str | None,
                     limit: int, cursor: str | None) -> CommercialPage: ...

    def execute_command(self, context: UserContext, account_id: str, operation: str,
                        payload: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]: ...


class OperationsPort(Protocol):
    def list_records(self, context: UserContext, account_id: str, record_type: str | None,
                     limit: int, cursor: str | None) -> OperationalPage: ...

    def execute_command(self, context: UserContext, account_id: str, operation: str,
                        payload: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]: ...


class CommercialOperationalView:
    """Tenant/permission-scoped facade over Sales and Inventory contracts."""

    MAX_PAGE_SIZE = 500

    def __init__(self, authorization: Any, commercial: CommercialPort, operations: OperationsPort) -> None:
        self.authorization = authorization
        self.commercial = commercial
        self.operations = operations

    def list_commercial(self, context: UserContext, account_id: str,
                        record_type: str | None = None, limit: int = 100,
                        cursor: str | None = None) -> CommercialPage:
        self._authorize(context, account_id, COMMERCIAL_VIEW_PERMISSION)
        self._validate_page(limit)
        page = self.commercial.list_records(context, account_id, record_type, limit, cursor)
        for record in page.records:
            self._validate_account(record.account_id, account_id)
        return page

    def list_operations(self, context: UserContext, account_id: str,
                        record_type: str | None = None, limit: int = 100,
                        cursor: str | None = None) -> OperationalPage:
        self._authorize(context, account_id, OPERATIONS_VIEW_PERMISSION)
        self._validate_page(limit)
        page = self.operations.list_records(context, account_id, record_type, limit, cursor)
        for record in page.records:
            self._validate_account(record.account_id, account_id)
        return page

    def execute_commercial(self, context: UserContext, account_id: str, operation: str,
                           payload: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]:
        self._authorize(context, account_id, COMMERCIAL_COMMAND_PERMISSION)
        self._validate_command(operation, idempotency_key)
        return self.commercial.execute_command(context, account_id, operation, payload, idempotency_key)

    def execute_operations(self, context: UserContext, account_id: str, operation: str,
                           payload: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]:
        self._authorize(context, account_id, OPERATIONS_COMMAND_PERMISSION)
        self._validate_command(operation, idempotency_key)
        return self.operations.execute_command(context, account_id, operation, payload, idempotency_key)

    def _authorize(self, context: UserContext, account_id: str, permission: str) -> None:
        if not context.user_id or not context.tenant_id:
            raise PermissionError("authenticated tenant context is required")
        if not account_id:
            raise ValueError("account_id is required")
        self.authorization.require_permission(context, permission)

    @staticmethod
    def _validate_account(record_account_id: str, requested_account_id: str) -> None:
        if record_account_id != requested_account_id:
            raise ValueError("source record does not belong to requested account")

    def _validate_page(self, limit: int) -> None:
        if limit < 1 or limit > self.MAX_PAGE_SIZE:
            raise ValueError("limit must be between 1 and 500")

    @staticmethod
    def _validate_command(operation: str, idempotency_key: str) -> None:
        if not operation or not idempotency_key:
            raise ValueError("operation and idempotency_key are required")
