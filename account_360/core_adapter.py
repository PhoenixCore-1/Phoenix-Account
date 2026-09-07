"""Phoenix Core integration boundary for Account 360."""

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

MODULE_CODE = "account_360"
MODULE_NAME = "Account 360"
MODULE_VERSION = "1.0.0"

@dataclass(frozen=True)
class UserContext:
    user_id: str
    tenant_id: str
    session_id: str | None = None
    roles: tuple[str, ...] = ()

@dataclass(frozen=True)
class ModuleRegistration:
    code: str = MODULE_CODE
    name: str = MODULE_NAME
    version: str = MODULE_VERSION

@dataclass(frozen=True)
class NavigationRegistration:
    module_code: str
    label: str
    route: str
    icon: str | None = None
    order: int = 0

@dataclass(frozen=True)
class AuditRecord:
    action: str
    tenant_id: str
    user_id: str | None
    resource_type: str
    resource_id: str | None
    outcome: str
    metadata: Mapping[str, Any]

class CoreAuthorization(Protocol):
    def require_permission(self, context: UserContext, permission: str) -> None: ...
    def has_permission(self, context: UserContext, permission: str) -> bool: ...

class CoreModuleRegistry(Protocol):
    def register(self, registration: ModuleRegistration) -> None: ...
    def is_enabled(self, tenant_id: str, module_code: str) -> bool: ...

class CoreNavigation(Protocol):
    def register(self, navigation: NavigationRegistration) -> None: ...

class CoreAudit(Protocol):
    def record(self, record: AuditRecord) -> str: ...

class CoreEventTransport(Protocol):
    def publish(self, tenant_id: str, event_type: str, payload: Mapping[str, Any]) -> str: ...
    def subscribe(self, event_types: Sequence[str], handler: Any) -> None: ...

class CoreConfiguration(Protocol):
    def get(self, tenant_id: str, key: str, default: Any = None) -> Any: ...

class CoreServiceTransport(Protocol):
    def request(
        self,
        context: UserContext,
        service: str,
        operation: str,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...

class CoreAdapter:
    """Thin facade over Phoenix Core contracts; never accesses Core DB internals."""

    def __init__(
        self,
        *,
        authorization: CoreAuthorization,
        module_registry: CoreModuleRegistry,
        navigation: CoreNavigation,
        audit_service: CoreAudit,
        event_transport: CoreEventTransport,
        configuration: CoreConfiguration,
        service_transport: CoreServiceTransport,
    ) -> None:
        self.authorization = authorization
        self.module_registry = module_registry
        self.navigation = navigation
        self.audit_service = audit_service
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
        self._require_context(context)
        self.authorization.require_permission(context, permission)

    def is_enabled(self, tenant_id: str) -> bool:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        return self.module_registry.is_enabled(tenant_id, MODULE_CODE)

    def record_audit(self, record: AuditRecord) -> str:
        if not record.tenant_id:
            raise ValueError("tenant_id is required")
        return self.audit_service.record(record)

    def publish_event(self, context: UserContext, event_type: str, payload: Mapping[str, Any]) -> str:
        self._require_context(context)
        return self.event_transport.publish(context.tenant_id, event_type, payload)

    def subscribe_events(self, event_types: Sequence[str], handler: Any) -> None:
        self.event_transport.subscribe(event_types, handler)

    def get_config(self, tenant_id: str, key: str, default: Any = None) -> Any:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        return self.configuration.get(tenant_id, key, default)

    def service_request(self, context: UserContext, service: str, operation: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self._require_context(context)
        return self.service_transport.request(context, service, operation, payload)

    @staticmethod
    def _require_context(context: UserContext) -> None:
        if not context.tenant_id:
            raise ValueError("tenant_id is required")
        if not context.user_id:
            raise ValueError("user_id is required")
