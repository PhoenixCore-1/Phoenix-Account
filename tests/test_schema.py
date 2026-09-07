from pathlib import Path
import sqlite3

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema.sql"

EXPECTED_TABLES = {
    "account_360_accounts",
    "account_360_source_references",
    "account_360_relationship_references",
    "account_360_contact_references",
    "account_360_projection_states",
    "account_360_integration_states",
    "account_360_timeline_events",
}


def connection_with_schema() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    return connection


def insert_account(connection, tenant_id="tenant-1", account_id="account-1", row_id="a1"):
    connection.execute(
        """
        INSERT INTO account_360_accounts
            (id, tenant_id, account_id, display_name, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (row_id, tenant_id, account_id, "Test Account", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
    )


def test_schema_loads_and_integrity_check_passes():
    connection = connection_with_schema()
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }

    assert EXPECTED_TABLES <= tables
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_canonical_account_is_unique_per_tenant():
    connection = connection_with_schema()
    insert_account(connection)

    with pytest.raises(sqlite3.IntegrityError):
        insert_account(connection, row_id="a2")

    insert_account(connection, tenant_id="tenant-2", row_id="a3")


def test_source_reference_cannot_cross_tenant_account_boundary():
    connection = connection_with_schema()
    insert_account(connection, tenant_id="tenant-1", account_id="account-1", row_id="a1")
    insert_account(connection, tenant_id="tenant-2", account_id="account-2", row_id="a2")

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO account_360_source_references
                (id, tenant_id, account_id, source_module, source_entity_type,
                 source_record_id, first_seen_at, last_seen_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "sr1", "tenant-1", "account-2", "crm", "customer", "crm-2",
                "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z",
            ),
        )


def test_timeline_event_id_is_idempotent_per_tenant_and_source():
    connection = connection_with_schema()
    insert_account(connection)

    values = (
        "event-row-1", "tenant-1", "account-1", "crm", "activity", "crm-1",
        "event-1", "CALL", "2026-01-02T10:00:00Z", "2026-01-02T10:01:00Z",
        "crm-1.0", "Call", "RELATIONSHIP", "2026-01-02T10:00:00Z",
    )

    connection.execute(
        """
        INSERT INTO account_360_timeline_events
            (id, tenant_id, account_id, source_module, source_entity_type,
             source_record_id, event_id, event_type, occurred_at, received_at,
             producer_version, title, category, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO account_360_timeline_events
                (id, tenant_id, account_id, source_module, source_entity_type,
                 source_record_id, event_id, event_type, occurred_at, received_at,
                 producer_version, title, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*values[:6], "event-1", *values[7:]),
        )


def test_relationship_cannot_point_to_itself():
    connection = connection_with_schema()
    insert_account(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO account_360_relationship_references
                (id, tenant_id, account_id, related_account_id, relationship_type,
                 source_module, source_entity_type, source_record_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "rel1", "tenant-1", "account-1", "account-1", "SELF",
                "crm", "relationship", "crm-rel-1",
                "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z",
            ),
        )


def test_account_360_does_not_create_financial_system_of_record_tables():
    connection = connection_with_schema()
    table_names = {
        row[0].lower()
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }

    prohibited = {
        "invoices",
        "payments",
        "allocations",
        "ledger_entries",
        "vat_transactions",
        "credit_notes",
        "sales_orders",
        "quotes",
        "stock_balances",
        "warehouse_bins",
    }

    assert table_names.isdisjoint(prohibited)
