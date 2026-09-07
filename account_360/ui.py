"""Framework-neutral Account 360 UI presentation contracts."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from .core_adapter import NavigationRegistration, UserContext

UI_PERMISSION = "account_360.view"
FINANCIAL_PERMISSION = "account_360.financial.view"
COMMUNICATION_CONTENT_PERMISSION = "account_360.communication.content.view"
MAX_PAGE_SIZE = 500


class SectionState(str, Enum):
    LOADING = "LOADING"
    READY = "READY"
    EMPTY = "EMPTY"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    FORBIDDEN = "FORBIDDEN"


@dataclass(frozen=True)
class AccountHeader:
    account_id: str
    display_name: str
    status: str
    primary_contact: str | None = None


@dataclass(frozen=True)
class SectionModel:
    key: str
    label: str
    state: SectionState
    data: Any = None
    as_of: str | None = None
    source_module: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class TimelineItemModel:
    event_id: str
    occurred_at: str
    title: str
    category: str
    source_module: str
    source_record_id: str
    summary: str | None = None
    stale: bool = False


@dataclass(frozen=True)
class QuickAction:
    key: str
    label: str
    target_module: str
    operation: str
    enabled: bool = True
    reason: str | None = None


@dataclass(frozen=True)
class Account360ViewModel:
    account: AccountHeader
    sections: Sequence[SectionModel]
    timeline: Sequence[TimelineItemModel] = field(default_factory=tuple)
    actions: Sequence[QuickAction] = field(default_factory=tuple)
    integration_status: Mapping[str, str] = field(default_factory=dict)


class Account360UI:
    """Builds a safe, framework-neutral presentation model for the host UI."""

    SECTION_DEFINITIONS = (
        ("overview", "Overview"),
        ("financial", "Financial Position"),
        ("credit", "Credit & Exposure"),
        ("invoices", "Invoices"),
        ("orders_quotes", "Orders & Quotes"),
        ("deliveries_pod", "Deliveries & POD"),
        ("payments_allocations", "Payments & Allocations"),
        ("ledger", "Customer Ledger"),
        ("aging_collections", "Aging & Collections"),
        ("statements", "Statements"),
        ("documents", "Documents"),
        ("communication", "Communication & Relationship"),
        ("tax_vat", "Tax & VAT"),
        ("credits_adjustments_disputes", "Credit Notes / Adjustments / Disputes"),
        ("timeline", "Unified Timeline"),
    )

    def __init__(self, *, authorization: Any) -> None:
        self.authorization = authorization

    @staticmethod
    def navigation() -> NavigationRegistration:
        return NavigationRegistration(
            module_code="account_360",
            label="Account 360",
            route="/account-360",
            icon="account",
            order=0,
        )

    def can_view(self, context: UserContext) -> bool:
        self._require_context(context)
        return self.authorization.has_permission(context, UI_PERMISSION)

    def build(
        self,
        context: UserContext,
        account: AccountHeader,
        *,
        section_data: Mapping[str, Any] | None = None,
        section_states: Mapping[str, SectionState] | None = None,
        timeline: Sequence[TimelineItemModel] = (),
        actions: Sequence[QuickAction] = (),
        integration_status: Mapping[str, str] | None = None,
    ) -> Account360ViewModel:
        self._require_context(context)
        if not account.account_id:
            raise ValueError("account_id is required")
        if not self.can_view(context):
            raise PermissionError("Account 360 view permission is required")

        data = section_data or {}
        states = section_states or {}
        sections = []
        for key, label in self.SECTION_DEFINITIONS:
            state = states.get(key, self._default_state(data.get(key)))
            if key in {"financial", "credit", "invoices", "payments_allocations", "ledger", "aging_collections", "statements", "tax_vat", "credits_adjustments_disputes"} and not self.authorization.has_permission(context, FINANCIAL_PERMISSION):
                state = SectionState.FORBIDDEN
            sections.append(SectionModel(key=key, label=label, state=state, data=data.get(key)))

        return Account360ViewModel(
            account=account,
            sections=tuple(sections),
            timeline=tuple(timeline),
            actions=tuple(actions),
            integration_status=dict(integration_status or {}),
        )

    @staticmethod
    def _default_state(value: Any) -> SectionState:
        if value is None:
            return SectionState.EMPTY
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and len(value) == 0:
            return SectionState.EMPTY
        return SectionState.READY

    @staticmethod
    def _require_context(context: UserContext) -> None:
        if not context.user_id or not context.tenant_id:
            raise ValueError("authenticated user and tenant context are required")
