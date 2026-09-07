"""Canonical account identity resolution for Phoenix Account 360."""

from dataclasses import dataclass
from typing import Protocol

from .core_adapter import UserContext


@dataclass(frozen=True)
class SourceIdentity:
    """Identity of an account/customer record owned by another module."""

    source_module: str
    source_entity_type: str
    source_record_id: str


@dataclass(frozen=True)
class AccountIdentity:
    """Canonical Phoenix account identity resolved for a tenant."""

    tenant_id: str
    account_id: str


@dataclass(frozen=True)
class IdentityResolution:
    """Result of resolving a source identity."""

    identity: AccountIdentity
    source: SourceIdentity
    created: bool


class AccountIdentityStore(Protocol):
    """Persistence/service boundary for canonical identity mappings."""

    def get_by_source(
        self, tenant_id: str, source: SourceIdentity
    ) -> AccountIdentity | None: ...

    def get_by_account(
        self, tenant_id: str, account_id: str
    ) -> AccountIdentity | None: ...

    def create_account(self, tenant_id: str) -> AccountIdentity: ...

    def bind_source(
        self,
        tenant_id: str,
        account_id: str,
        source: SourceIdentity,
    ) -> None: ...


class IdentityConflictError(ValueError):
    """Raised when a source identity cannot be safely resolved."""


class IdentityNotFoundError(LookupError):
    """Raised when strict resolution finds no mapping."""


class AccountIdentityService:
    """Resolve source customer identities without owning the customer master."""

    def __init__(self, store: AccountIdentityStore) -> None:
        self.store = store

    def resolve(
        self,
        context: UserContext,
        source: SourceIdentity,
        *,
        create_if_missing: bool = False,
    ) -> IdentityResolution:
        self._validate_context(context)
        self._validate_source(source)

        existing = self.store.get_by_source(context.tenant_id, source)
        if existing is not None:
            return IdentityResolution(existing, source, created=False)

        if not create_if_missing:
            raise IdentityNotFoundError("Source identity is not mapped to a canonical account")

        account = self.store.create_account(context.tenant_id)
        if account.tenant_id != context.tenant_id:
            raise IdentityConflictError("Identity store returned a cross-tenant account")

        try:
            self.store.bind_source(context.tenant_id, account.account_id, source)
        except Exception as exc:
            raise IdentityConflictError("Source identity could not be bound safely") from exc

        return IdentityResolution(account, source, created=True)

    def require_account(
        self, context: UserContext, source: SourceIdentity
    ) -> AccountIdentity:
        return self.resolve(context, source, create_if_missing=False).identity

    def verify_account(
        self, context: UserContext, account_id: str
    ) -> AccountIdentity:
        self._validate_context(context)
        if not account_id:
            raise ValueError("account_id is required")
        account = self.store.get_by_account(context.tenant_id, account_id)
        if account is None:
            raise IdentityNotFoundError("Canonical account was not found")
        if account.tenant_id != context.tenant_id:
            raise IdentityConflictError("Canonical account belongs to another tenant")
        return account

    @staticmethod
    def _validate_context(context: UserContext) -> None:
        if not context.user_id:
            raise ValueError("user_id is required")
        if not context.tenant_id:
            raise ValueError("tenant_id is required")

    @staticmethod
    def _validate_source(source: SourceIdentity) -> None:
        if not source.source_module:
            raise ValueError("source_module is required")
        if not source.source_entity_type:
            raise ValueError("source_entity_type is required")
        if not source.source_record_id:
            raise ValueError("source_record_id is required")
