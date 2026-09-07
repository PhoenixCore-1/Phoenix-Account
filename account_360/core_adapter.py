"""Phoenix Core integration boundary for Account 360.

This module deliberately contains interfaces and value objects only. It does
not know how Phoenix Core authenticates users, stores tenants, enforces
permissions, registers modules, or transports events. Concrete Core wiring is
provided by the host application through these contracts.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence


MODULE_CODE = "account_360"
MODULE_NAME = "Account 360"
MODULE_VERSION = "1.0.0"


@dataclass(frozen=True)
class UserContext:
    """Authenticated Phoenix user context supplied by Core."""

    user_id: str
    tenant_id: str
    session_id: str | None = None
    roles: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModuleRegistration:
    """Registration metadata Account 360 exposes to Core."""

    code: str = MODULE_CODE
    name: str = MODULE_NAME
    version: str = MODULE_VERSION


@dataclass(frozen=True)
class NavigationRegistration:
    """Navigation entry requested through the Core navigation service."""

    module_code: str
    label: str
    route: str
    icon: str | None = None
    order: int = 0


@dataclass(frozen=True)
class AuditRecord:
    """Audit information sent to Core; Account 360 stores no audit ledger."""

    action: str
    tenant_id: str
    user_id: str | None
    resource_type: str
    resource_id: str | None
    outcome: str
    metadata: Mapping[str, Any]


class CoreAuthorization(Protocol):
    """Server-side authorization contract supplied by Phoenix Core."""

    def require_permission(self, context: UserContext, permission: str) -> None:
        """Raise a Core-defined authorization error when access is denied."""
        ...

    def has_permission(self, context: UserContext, permission: str) -> bool:
        """Return whether the authenticated user has the requested permission."""
        ...


class CoreModuleRegistry(Protocol):
    """Core module registration/licensing contract."""

    def register(self, registration: ModuleRegistration) -> None:
        ...

    def is_enabled(self, tenant_id: str, module_code: str) -> bool:
        ...


class CoreNavigation(Protocol):
    """Core-owned navigation registration contract."""

    def register(self, navigation: NavigationRegistration) -> None:
        ...


class CoreAudit(Protocol):
    """Core audit/event infrastructure contract."""

    def record(self, record: AuditRecord) -> str:
        """Return the Core audit reference for the recorded operation."""
        ...


class CoreEventTransport(Protocol):
    """Approved service/event transport boundary."""

    def publish(self, tenant_id: str, event_type: str, payload: Mapping[str, Any]) -> str:
        ...

    def subscribe(self, event_types: Sequence[str], handler: Any) -> None:
        ...


class CoreConfiguration(Protocol):
    """Tenant-aware configuration access supplied by Core."""

    def get(self, tenant_id: str, key: str, default: Any = None) -> Any:
        ...


class CoreServiceTransport(Protocol):
    """Approved service-to-service request boundary."""

    def request(
        self,
        context: UserContext,
        service: str,
        operation: str,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        ...


class CoreAdapter:
    """Thin Account 360 facade over Phoenix Core contracts.

    Account 360 domain/application services should depend on this facade or
    narrower interfaces, never on Core database objects or implementation
    details.
    """

    def __init__(
        self,
        *,
        authorization: CoreAuthorization,
        module_registry: CoreModuleRegistry,
        navigation: CoreNavigation,
        audit: CoreAudit,
        event_transport: CoreEventTransport,
        configuration: CoreConfiguration,
        service_transport: CoreServiceTransport,
    ) -> None:
        self.authorization = authorization
        self.module_registry = module_registry
        self.navigation = navigation
        self.audit = audit
        self.event_transport = event_transport
        self.configuration = configuration
        self.service_transport = service_transport

    @staticmethod
    def registration() -> ModuleRegistration:
        return ModuleRegistration()

    def register_module(self) -> None:
        self.module_registry.register(self.registration())

    def register_navigation(self, navigation: NavigationRegistration) -> None:
        if navigation.module_code != MODULE_CODE:
            raise ValueError("Navigation must belong to Account 360")
        self.navigation.register(navigation)

    def require_permission(self, context: UserContext, permission: str) -> None:
        if not context.tenant_id:
            raise ValueError("tenant_id is required")
        if not context.user_id:
            raise ValueError("user_id is required")
        self.authorization.require_permission(context, permission)

    def is_enabled(self, tenant_id: str) -> bool:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        return self.module_registry.is_enabled(tenant_id, MODULE_CODE)

    def audit(self, record: AuditRecord) -> str:
        if record.tenant_id == "":
            raise ValueError("tenant_id is required")
        return self.audit.record(record)

    def publish_event(
        self,
        context: UserContext,
        event_type: str,
        payload: Mapping[str, Any],
    ) -> str:
        if not context.tenant_id:
            raise ValueError("tenant_id is required")
        return self.event_transport.publish(context.tenant_id, event_type, payload)

    def subscribe_events(self, event_types: Sequence[str], handler: Any) -> None:
        self.event_transport.subscribe(event_types, handler)

    def get_config(self, tenant_id: str, key: str, default: Any = None) -> Any:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        return self.configuration.get(tenant_id, key, default)

    def service_request(
        self,
        context: UserContext,
        service: str,
        operation: str,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        if not context.tenant_id:
            raise ValueError("tenant_id is required")
        return self.service_transport.request(context, service, operation, payload)
