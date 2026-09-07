"""Cross-module integration contracts for Phoenix Account 360.

These contracts define the boundary Account 360 uses to consume domain data,
receive domain events, and route commands. Implementations belong to the host
or owning modules; Account 360 does not access their databases directly.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .core_adapter import UserContext

SUPPORTED_MODULES = ("crm", "sales", "accounts", "inventory", "procurement")


@dataclass(frozen=True)
class SourceRef:
    tenant_id: str
    account_id: str
    source_module: str
    source_entity_type: str
    source_record_id: str
    source_version: str | None = None


@dataclass(frozen=True)
class QueryRequest:
    context: UserContext
    source_module: str
    operation: str
    account_id: str
    parameters: Mapping[str, Any]
    limit: int = 100
    cursor: str | None = None

    def validate(self) -> None:
        if self.source_module not in SUPPORTED_MODULES:
            raise ValueError("unsupported source module")
        if not self.account_id:
            raise ValueError("account_id is required")
        if self.limit < 1 or self.limit > 500:
            raise ValueError("limit must be between 1 and 500")


@dataclass(frozen=True)
class QueryResult:
    source_module: str
    operation: str
    records: Sequence[Mapping[str, Any]]
    next_cursor: str | None = None
    source_version: str | None = None
    as_of: str | None = None


@dataclass(frozen=True)
class DomainEvent:
    tenant_id: str
    account_id: str | None
    source_module: str
    source_entity_type: str
    source_record_id: str
    event_id: str
    event_type: str
    occurred_at: str
    received_at: str
    producer_version: str
    payload: Mapping[str, Any]
    source_version: str | None = None
    source_sequence: int | None = None

    def validate(self) -> None:
        if self.source_module not in SUPPORTED_MODULES:
            raise ValueError("unsupported source module")
        if not self.tenant_id or not self.event_id:
            raise ValueError("tenant_id and event_id are required")
        if not self.source_record_id or not self.event_type:
            raise ValueError("source_record_id and event_type are required")


@dataclass(frozen=True)
class CommandRequest:
    context: UserContext
    target_module: str
    operation: str
    account_id: str
    payload: Mapping[str, Any]
    idempotency_key: str

    def validate(self) -> None:
        if self.target_module not in SUPPORTED_MODULES:
            raise ValueError("unsupported target module")
        if not self.account_id:
            raise ValueError("account_id is required")
        if not self.operation or not self.idempotency_key:
            raise ValueError("operation and idempotency_key are required")


class ModuleQueryPort(Protocol):
    def query(self, request: QueryRequest) -> QueryResult: ...


class ModuleCommandPort(Protocol):
    def execute(self, request: CommandRequest) -> Mapping[str, Any]: ...


class EventConsumerPort(Protocol):
    def accept(self, event: DomainEvent) -> None: ...


class CrossModuleGateway:
    """Validated boundary for Account 360 cross-module access."""

    def __init__(self, query_port: ModuleQueryPort, command_port: ModuleCommandPort) -> None:
        self.query_port = query_port
        self.command_port = command_port

    def query(self, request: QueryRequest) -> QueryResult:
        request.validate()
        if request.context.tenant_id != request.context.tenant_id:
            raise ValueError("invalid tenant context")
        return self.query_port.query(request)

    def execute(self, request: CommandRequest) -> Mapping[str, Any]:
        request.validate()
        if request.context.tenant_id == "":
            raise ValueError("tenant_id is required")
        return self.command_port.execute(request)
