"""Action and workflow orchestration boundary for Account 360."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Protocol

from .core_adapter import AuditRecord, UserContext
from .integration import SUPPORTED_MODULES

ACTION_PERMISSION = "account_360.actions.execute"


class ActionState(str, Enum):
    AVAILABLE = "AVAILABLE"
    DISABLED = "DISABLED"
    UNAVAILABLE = "UNAVAILABLE"
    FORBIDDEN = "FORBIDDEN"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ActionRequest:
    context: UserContext
    action_key: str
    target_module: str
    operation: str
    account_id: str
    payload: Mapping[str, Any]
    idempotency_key: str

    def validate(self) -> None:
        if not self.context.user_id or not self.context.tenant_id:
            raise ValueError("authenticated user and tenant context are required")
        if not self.action_key:
            raise ValueError("action_key is required")
        if self.target_module not in SUPPORTED_MODULES:
            raise ValueError("unsupported target module")
        if not self.operation or not self.account_id:
            raise ValueError("operation and account_id are required")
        if not self.idempotency_key:
            raise ValueError("idempotency_key is required")


@dataclass(frozen=True)
class ActionResult:
    action_key: str
    state: ActionState
    target_module: str
    operation: str
    account_id: str
    result: Mapping[str, Any] | None = None
    source_reference: str | None = None
    message: str | None = None


class OwningCommandPort(Protocol):
    def execute(self, request: ActionRequest) -> Mapping[str, Any]: ...


class ActionAvailabilityPort(Protocol):
    def check(self, request: ActionRequest) -> ActionState: ...


class WorkflowAuditPort(Protocol):
    def record(self, record: AuditRecord) -> str: ...


class Account360ActionService:
    """Routes authorized Account 360 actions to owning services."""

    def __init__(
        self,
        *,
        authorization: Any,
        command_port: OwningCommandPort,
        availability: ActionAvailabilityPort | None = None,
        audit: WorkflowAuditPort | None = None,
    ) -> None:
        self.authorization = authorization
        self.command_port = command_port
        self.availability = availability
        self.audit = audit

    def check(self, request: ActionRequest) -> ActionState:
        request.validate()
        if not self.authorization.has_permission(request.context, ACTION_PERMISSION):
            return ActionState.FORBIDDEN
        if self.availability is None:
            return ActionState.AVAILABLE
        return self.availability.check(request)

    def execute(self, request: ActionRequest) -> ActionResult:
        request.validate()
        self.authorization.require_permission(request.context, ACTION_PERMISSION)
        state = self.check(request)
        if state != ActionState.AVAILABLE:
            return self._result(request, state, message=f"Action is {state.value.lower()}")
        try:
            result = self.command_port.execute(request)
            source_reference = result.get("source_reference")
            action_result = self._result(
                request, ActionState.AVAILABLE, result=result, source_reference=source_reference
            )
            self._audit(request, "SUCCESS", {"state": action_result.state.value})
            return action_result
        except Exception as exc:
            self._audit(request, "ERROR", {"error_type": type(exc).__name__})
            return self._result(request, ActionState.ERROR, message=str(exc))

    def _result(
        self,
        request: ActionRequest,
        state: ActionState,
        *,
        result: Mapping[str, Any] | None = None,
        source_reference: str | None = None,
        message: str | None = None,
    ) -> ActionResult:
        return ActionResult(
            action_key=request.action_key,
            state=state,
            target_module=request.target_module,
            operation=request.operation,
            account_id=request.account_id,
            result=result,
            source_reference=source_reference,
            message=message,
        )

    def _audit(self, request: ActionRequest, outcome: str, metadata: Mapping[str, Any]) -> None:
        if self.audit is None:
            return
        self.audit.record(
            AuditRecord(
                action=f"account_360.action.{request.action_key}",
                tenant_id=request.context.tenant_id,
                user_id=request.context.user_id,
                resource_type="account",
                resource_id=request.account_id,
                outcome=outcome,
                metadata=dict(metadata),
            )
        )
