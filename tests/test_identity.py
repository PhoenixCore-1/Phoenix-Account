import pytest

from account_360.core_adapter import UserContext
from account_360.identity import (
    AccountIdentity,
    AccountIdentityService,
    IdentityConflictError,
    IdentityNotFoundError,
    SourceIdentity,
)


class FakeIdentityStore:
    def __init__(self):
        self.by_source = {}
        self.by_account = {}
        self.created = 0
        self.bound = []
        self.return_cross_tenant = False
        self.fail_bind = False

    def get_by_source(self, tenant_id, source):
        return self.by_source.get((tenant_id, source))

    def get_by_account(self, tenant_id, account_id):
        return self.by_account.get((tenant_id, account_id))

    def create_account(self, tenant_id):
        self.created += 1
        account = AccountIdentity(tenant_id, f"account-{self.created}")
        if self.return_cross_tenant:
            account = AccountIdentity("other-tenant", account.account_id)
        self.by_account[(account.tenant_id, account.account_id)] = account
        return account

    def bind_source(self, tenant_id, account_id, source):
        if self.fail_bind:
            raise RuntimeError("duplicate source")
        self.bound.append((tenant_id, account_id, source))
        self.by_source[(tenant_id, source)] = AccountIdentity(tenant_id, account_id)


def context(tenant="tenant-1"):
    return UserContext("user-1", tenant)


def source():
    return SourceIdentity("crm", "customer", "crm-123")


def test_existing_source_resolves_without_creating_account():
    store = FakeIdentityStore()
    existing = AccountIdentity("tenant-1", "account-42")
    store.by_source[("tenant-1", source())] = existing
    service = AccountIdentityService(store)

    result = service.resolve(context(), source())

    assert result.identity == existing
    assert result.created is False
    assert store.created == 0


def test_missing_source_can_create_and_bind_canonical_account():
    store = FakeIdentityStore()
    service = AccountIdentityService(store)

    result = service.resolve(context(), source(), create_if_missing=True)

    assert result.identity == AccountIdentity("tenant-1", "account-1")
    assert result.created is True
    assert store.bound == [("tenant-1", "account-1", source())]


def test_strict_resolution_does_not_create_missing_identity():
    service = AccountIdentityService(FakeIdentityStore())

    with pytest.raises(IdentityNotFoundError):
        service.require_account(context(), source())


def test_cross_tenant_created_identity_is_rejected():
    store = FakeIdentityStore()
    store.return_cross_tenant = True
    service = AccountIdentityService(store)

    with pytest.raises(IdentityConflictError):
        service.resolve(context(), source(), create_if_missing=True)


def test_bind_failure_is_exposed_as_identity_conflict():
    store = FakeIdentityStore()
    store.fail_bind = True
    service = AccountIdentityService(store)

    with pytest.raises(IdentityConflictError):
        service.resolve(context(), source(), create_if_missing=True)


def test_verify_account_is_tenant_scoped():
    store = FakeIdentityStore()
    account = AccountIdentity("tenant-1", "account-42")
    store.by_account[("tenant-1", "account-42")] = account
    service = AccountIdentityService(store)

    assert service.verify_account(context(), "account-42") == account

    with pytest.raises(IdentityNotFoundError):
        service.verify_account(context("tenant-2"), "account-42")


def test_missing_identity_fields_are_rejected():
    service = AccountIdentityService(FakeIdentityStore())

    with pytest.raises(ValueError):
        service.resolve(context(), SourceIdentity("", "customer", "1"))

    with pytest.raises(ValueError):
        service.resolve(context(), SourceIdentity("crm", "", "1"))

    with pytest.raises(ValueError):
        service.resolve(context(), SourceIdentity("crm", "customer", ""))
