"""Provider-independent Account 360 AI orchestration contracts."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Protocol, Sequence

from .core_adapter import UserContext

AI_PERMISSION = "account_360.ai.use"
AI_ACTION_PERMISSION = "account_360.ai.action.execute"
COMMUNICATION_CONTENT_PERMISSION = "account_360.communication.content.view"
MAX_CONTEXT_ITEMS = 100


class AICapability(str, Enum):
    ASK = "ASK"
    SUMMARIZE = "SUMMARIZE"
    EXTRACT = "EXTRACT"
    RECOMMEND = "RECOMMEND"
    PREDICT = "PREDICT"
    DETECT = "DETECT"
    CLASSIFY = "CLASSIFY"
    GENERATE = "GENERATE"
    PROPOSE_ACTION = "PROPOSE_ACTION"
    EXECUTE_AUTHORIZED_ACTION = "EXECUTE_AUTHORIZED_ACTION"


@dataclass(frozen=True)
class AIContextItem:
    source_module: str
    source_type: str
    source_id: str
    content: Any
    as_of: str | None = None
    sensitive: bool = False


@dataclass(frozen=True)
class AIRequest:
    context: UserContext
    account_id: str
    capability: AICapability
    context_items: Sequence[AIContextItem]
    instruction: str | None = None
    output_format: str | None = None
    action_intent: Mapping[str, Any] | None = None
    request_id: str = ""

    def validate(self) -> None:
        if not self.context.user_id or not self.context.tenant_id:
            raise ValueError("authenticated user and tenant context are required")
        if not self.account_id:
            raise ValueError("account_id is required")
        if not self.request_id:
            raise ValueError("request_id is required")
        if len(self.context_items) > MAX_CONTEXT_ITEMS:
            raise ValueError("AI context item limit exceeded")
        if self.capability in {AICapability.ASK, AICapability.GENERATE, AICapability.PROPOSE_ACTION} and not self.instruction:
            raise ValueError("instruction is required for this capability")
        for item in self.context_items:
            if not item.source_module or not item.source_type or not item.source_id:
                raise ValueError("AI context items require source identity")


@dataclass(frozen=True)
class AIResponse:
    capability: AICapability
    result: Any
    source_references: Sequence[str] = ()
    as_of: str | None = None
    confidence: float | None = None
    proposed_action: Mapping[str, Any] | None = None
    executed_action: Mapping[str, Any] | None = None
    audit_reference: str | None = None


class CoreAIService(Protocol):
    def run(self, request: AIRequest) -> AIResponse: ...


class AIActionExecutor(Protocol):
    def execute(self, context: UserContext, account_id: str, action: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]: ...


class Account360AI:
    """Safe facade over Core AI and the existing Account 360 action boundary."""

    def __init__(self, *, authorization: Any, ai_service: CoreAIService, action_executor: AIActionExecutor) -> None:
        self.authorization = authorization
        self.ai_service = ai_service
        self.action_executor = action_executor

    def run(self, request: AIRequest) -> AIResponse:
        request.validate()
        self.authorization.require_permission(request.context, AI_PERMISSION)
        filtered = self._filter_context(request)
        safe_request = AIRequest(
            context=request.context,
            account_id=request.account_id,
            capability=request.capability,
            context_items=filtered,
            instruction=request.instruction,
            output_format=request.output_format,
            action_intent=request.action_intent,
            request_id=request.request_id,
        )
        return self.ai_service.run(safe_request)

    def execute_proposed_action(self, request: AIRequest, response: AIResponse, idempotency_key: str) -> Mapping[str, Any]:
        request.validate()
        if request.capability != AICapability.EXECUTE_AUTHORIZED_ACTION:
            raise ValueError("execution requires EXECUTE_AUTHORIZED_ACTION capability")
        self.authorization.require_permission(request.context, AI_ACTION_PERMISSION)
        if not response.proposed_action:
            raise ValueError("an AI proposed action is required")
        if not idempotency_key:
            raise ValueError("idempotency_key is required")
        return self.action_executor.execute(request.context, request.account_id, response.proposed_action, idempotency_key)

    def _filter_context(self, request: AIRequest) -> tuple[AIContextItem, ...]:
        include_sensitive = self.authorization.has_permission(request.context, COMMUNICATION_CONTENT_PERMISSION)
        return tuple(item for item in request.context_items if not item.sensitive or include_sensitive)
