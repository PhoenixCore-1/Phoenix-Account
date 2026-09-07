from pathlib import Path
import sqlite3
import tomllib

import account_360
from account_360.core_adapter import MODULE_CODE, MODULE_NAME, MODULE_VERSION

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_consistent():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == "1.0.0"
    assert account_360.__version__ == "1.0.0"
    assert MODULE_VERSION == "1.0.0"
    assert MODULE_CODE == "account_360"
    assert MODULE_NAME == "Account 360"


def test_package_metadata_has_no_runtime_dependencies():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"].get("dependencies", []) == []


def test_required_release_files_exist():
    required = (
        "README.md",
        "pyproject.toml",
        "schema.sql",
        "docs/BUILD_PHASES_V1.0.md",
        "docs/ACCOUNT_360_SCOPE_V1.0.md",
        "docs/ACCOUNT_360_CONTRACT_V1.0.md",
        "docs/ACCOUNT_360_RELEASE_CANDIDATE_V1.0.md",
    )
    for relative in required:
        assert (ROOT / relative).is_file(), relative


def test_schema_initializes_clean_database():
    schema = (ROOT / "schema.sql").read_text(encoding="utf-8")
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(schema)
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        connection.close()


def test_schema_contains_required_account_360_tables():
    schema = (ROOT / "schema.sql").read_text(encoding="utf-8")
    required_tables = (
        "account_360_accounts",
        "account_360_source_references",
        "account_360_relationship_references",
        "account_360_contact_references",
        "account_360_projection_states",
        "account_360_integration_states",
        "account_360_timeline_events",
    )
    for table in required_tables:
        assert f"CREATE TABLE {table}" in schema


def test_schema_does_not_introduce_forbidden_system_of_record_tables():
    schema = (ROOT / "schema.sql").read_text(encoding="utf-8").lower()
    forbidden = (
        "invoices",
        "payments",
        "ledger_entries",
        "sales_orders",
        "quotes",
        "warehouse_stock",
        "inventory_transactions",
        "crm_contacts",
    )
    for name in forbidden:
        assert f"create table {name}" not in schema


def test_package_discovery_targets_account_360_only():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    includes = pyproject["tool"]["setuptools"]["packages"]["find"]["include"]
    assert includes == ["account_360*"]


def test_release_candidate_document_preserves_known_boundaries():
    document = (ROOT / "docs/ACCOUNT_360_RELEASE_CANDIDATE_V1.0.md").read_text(encoding="utf-8")
    required_phrases = (
        "not a replacement for source systems of record",
        "Core AI service boundary",
        "No external communication credentials",
        "no unresolved critical security",
    )
    for phrase in required_phrases:
        assert phrase.lower() in document.lower()


def test_build_phase_document_defines_phase_14_and_15_gate():
    document = (ROOT / "docs/BUILD_PHASES_V1.0.md").read_text(encoding="utf-8")
    assert "## Phase 14 — Full Regression & Release Candidate" in document
    assert "## Phase 15 — V1.0 Freeze & Package" in document
    assert "Release candidate accepted" in document


def test_release_candidate_has_no_embedded_provider_credentials():
    package_files = list((ROOT / "account_360").rglob("*.py"))
    forbidden_markers = ("BEGIN PRIVATE KEY", "client_secret=", "access_token=", "api_key=")
    for path in package_files:
        content = path.read_text(encoding="utf-8").lower()
        for marker in forbidden_markers:
            assert marker.lower() not in content, str(path)
