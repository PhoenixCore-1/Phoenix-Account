from dataclasses import dataclass

import pytest

from account_360.core_adapter import UserContext
from account_360.ui import (
    Account360UI,
    AccountHeader,
    QuickAction,
    SectionState,
    TimelineItemModel,
    UI_PERMISSION,
    FINANCIAL_PERMISSION,
)


@dataclass
class FakeAuthorization:
    allowed: set[str]

    def has_permission(self, context, permission):
        return permission in self.allowed


def context():
    return UserContext(user_id="u1", tenant_id="t1")


def test_navigation_is_core_registered_contract():
    navigation = Account360UI.navigation()
    assert navigation.module_code == "account_360"
    assert navigation.label == "Account 360"
    assert navigation.route == "/account-360"


def test_view_requires_authenticated_context():
    ui = Account360UI(authorization=FakeAuthorization({UI_PERMISSION}))
    with pytest.raises(ValueError):
        ui.can_view(UserContext(user_id="", tenant_id="t1"))


def test_view_permission_is_enforced_server_side_boundary():
    ui = Account360UI(authorization=FakeAuthorization(set()))
    assert ui.can_view(context()) is False
    with pytest.raises(PermissionError):
        ui.build(context(), AccountHeader("a1", "Acme", "ACTIVE"))


def test_build_exposes_complete_v1_sections():
    ui = Account360UI(authorization=FakeAuthorization({UI_PERMISSION, FINANCIAL_PERMISSION}))
    model = ui.build(context(), AccountHeader("a1", "Acme", "ACTIVE"))
    keys = [section.key for section in model.sections]
    assert keys == [key for key, _ in Account360UI.SECTION_DEFINITIONS]
    assert len(keys) == 15


def test_financial_sections_are_forbidden_without_financial_permission():
    ui = Account360UI(authorization=FakeAuthorization({UI_PERMISSION}))
    model = ui.build(context(), AccountHeader("a1", "Acme", "ACTIVE"))
    financial_keys = {"financial", "credit", "invoices", "payments_allocations", "ledger", "aging_collections", "statements", "tax_vat", "credits_adjustments_disputes"}
    states = {s.key: s.state for s in model.sections}
    assert all(states[key] == SectionState.FORBIDDEN for key in financial_keys)


def test_financial_sections_are_available_with_permission():
    ui = Account360UI(authorization=FakeAuthorization({UI_PERMISSION, FINANCIAL_PERMISSION}))
    model = ui.build(context(), AccountHeader("a1", "Acme", "ACTIVE"), section_data={"financial": {"balance": 100}})
    states = {s.key: s.state for s in model.sections}
    assert states["financial"] == SectionState.READY
    assert states["credit"] == SectionState.EMPTY


def test_section_states_are_preserved():
    ui = Account360UI(authorization=FakeAuthorization({UI_PERMISSION, FINANCIAL_PERMISSION}))
    model = ui.build(
        context(),
        AccountHeader("a1", "Acme", "ACTIVE"),
        section_states={"orders_quotes": SectionState.STALE, "documents": SectionState.UNAVAILABLE},
    )
    states = {s.key: s.state for s in model.sections}
    assert states["orders_quotes"] == SectionState.STALE
    assert states["documents"] == SectionState.UNAVAILABLE


def test_timeline_and_actions_are_presentation_data_only():
    ui = Account360UI(authorization=FakeAuthorization({UI_PERMISSION, FINANCIAL_PERMISSION}))
    timeline = [TimelineItemModel("e1", "2026-09-07T08:00:00Z", "Order", "ORDER", "sales", "o1")]
    actions = [QuickAction("quote", "Create Quote", "sales", "create_quote")]
    model = ui.build(context(), AccountHeader("a1", "Acme", "ACTIVE"), timeline=timeline, actions=actions)
    assert model.timeline == tuple(timeline)
    assert model.actions == tuple(actions)
    assert model.actions[0].target_module == "sales"


def test_account_identity_is_required():
    ui = Account360UI(authorization=FakeAuthorization({UI_PERMISSION}))
    with pytest.raises(ValueError):
        ui.build(context(), AccountHeader("", "Acme", "ACTIVE"))


def test_default_states_are_explicit():
    ui = Account360UI(authorization=FakeAuthorization({UI_PERMISSION, FINANCIAL_PERMISSION}))
    model = ui.build(context(), AccountHeader("a1", "Acme", "ACTIVE"))
    assert all(section.state == SectionState.EMPTY for section in model.sections)
