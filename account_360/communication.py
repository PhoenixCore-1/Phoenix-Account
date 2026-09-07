"""Communication and relationship contracts for Phoenix Account 360.

The module owns normalized references/projections only. CRM and approved
communication providers remain authoritative for underlying records.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .core_adapter import UserContext

COMMUNICATION_PERMISSION = "account_360.communication.view"
CONTENT_PERMISSION = "account_360.communication.content"
SUPPORTED_TYPES = (
    "CALL", "WHATSAPP", "EMAIL", "MEETING", "VISIT", "NOTE",
    "ACTIVITY", "TASK", "FOLLOW_UP",
)

@dataclass(frozen=True)
class RelationshipRecord:
    record_id: str
    tenant_id: str
    account_id: str
    contact_id: str | None
    relationship_type: str
    role: str | None
    status: str
    source_module: str
    source_entity_type: str
    source_record_id: str
    source_version: str | None

@dataclass(frozen=True)
class CommunicationRecord:
    record_id: str
    tenant_id: str
    account_id: str
    contact_id: str | None
    source_module: str
    source_entity_type: str
    source_record_id: str
    communication_type: str
    direction: str | None
    status: str
    title: str | None
    occurred_at: str
    source_version: str | None
    source_sequence: int | None
    content_available: bool
    source_reference: str | None

@dataclass(frozen=True)
class CommunicationPage:
    records: Sequence[CommunicationRecord]
    next_cursor: str | None
    source_version: str | None
    as_of: str

@dataclass(frozen=True)
class RelationshipPage:
    records: Sequence[RelationshipRecord]
    next_cursor: str | None
    source_version: str | None
    as_of: str

class CommunicationPort(Protocol):
    def list_communications(self, context: UserContext, account_id: str, communication_type: str | None, limit: int, cursor: str | None) -> CommunicationPage: ...
    def list_relationships(self, context: UserContext, account_id: str, limit: int, cursor: str | None) -> RelationshipPage: ...
    def get_content(self, context: UserContext, account_id: str, record_id: str) -> Mapping[str, Any]: ...
    def execute(self, context: UserContext, account_id: str, operation: str, payload: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]: ...

class CommunicationAccountView:
    def __init__(self, *, authorization: Any, source: CommunicationPort) -> None:
        self.authorization = authorization
        self.source = source

    def list_communications(self, context: UserContext, account_id: str, communication_type: str | None = None, limit: int = 100, cursor: str | None = None) -> CommunicationPage:
        self._authorize(context, COMMUNICATION_PERMISSION)
        self._validate_account(account_id)
        if communication_type is not None and communication_type not in SUPPORTED_TYPES:
            raise ValueError("unsupported communication type")
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        page = self.source.list_communications(context, account_id, communication_type, limit, cursor)
        self._validate_page(page, context, account_id)
        return page

    def list_relationships(self, context: UserContext, account_id: str, limit: int = 100, cursor: str | None = None) -> RelationshipPage:
        self._authorize(context, COMMUNICATION_PERMISSION)
        self._validate_account(account_id)
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        page = self.source.list_relationships(context, account_id, limit, cursor)
        if not page.as_of:
            raise ValueError("relationship freshness metadata is required")
        for record in page.records:
            self._validate_tenant_account(record.tenant_id, record.account_id, context, account_id)
        return page

    def get_content(self, context: UserContext, account_id: str, record_id: str) -> Mapping[str, Any]:
        self._authorize(context, CONTENT_PERMISSION)
        self._validate_account(account_id)
        if not record_id:
            raise ValueError("record_id is required")
        return self.source.get_content(context, account_id, record_id)

    def command(self, context: UserContext, account_id: str, operation: str, payload: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]:
        self._authorize(context, COMMUNICATION_PERMISSION)
        self._validate_account(account_id)
        if not operation or not idempotency_key:
            raise ValueError("operation and idempotency_key are required")
        return self.source.execute(context, account_id, operation, payload, idempotency_key)

    def _authorize(self, context: UserContext, permission: str) -> None:
        if not context.user_id or not context.tenant_id:
            raise ValueError("authenticated tenant context is required")
        self.authorization.require_permission(context, permission)

    @staticmethod
    def _validate_account(account_id: str) -> None:
        if not account_id:
            raise ValueError("account_id is required")

    @staticmethod
    def _validate_tenant_account(tenant_id: str, record_account_id: str, context: UserContext, account_id: str) -> None:
        if tenant_id != context.tenant_id:
            raise ValueError("cross-tenant communication record")
        if record_account_id != account_id:
            raise ValueError("cross-account communication record")

    def _validate_page(self, page: CommunicationPage, context: UserContext, account_id: str) -> None:
        if not page.as_of:
            raise ValueError("communication freshness metadata is required")
        for record in page.records:
            self._validate_tenant_account(record.tenant_id, record.account_id, context, account_id)
            if record.communication_type not in SUPPORTED_TYPES:
                raise ValueError("unsupported communication type")
