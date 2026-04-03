"""Tests for database management helpers and actions."""

from unittest.mock import patch

from databases import (
    build_admin_command,
    build_create_user_sql,
    delete_database,
    filter_system_databases,
    list_databases,
)


def test_build_admin_command_for_postgresql():
    """PostgreSQL commands should run through the postgres user."""
    assert build_admin_command("postgresql", "SELECT 1") == 'sudo -u postgres psql -tAc "SELECT 1"'


def test_build_admin_command_for_mysql_family():
    """MySQL and MariaDB should share the mysql admin runner."""
    assert build_admin_command("mysql", "SELECT 1") == 'sudo mysql -Nse "SELECT 1"'
    assert build_admin_command("mariadb", "SELECT 1") == 'sudo mysql -Nse "SELECT 1"'


def test_filter_system_databases_for_postgresql():
    """PostgreSQL system databases should be hidden from list views."""
    names = ["postgres", "template0", "template1", "app_db"]
    assert filter_system_databases("postgresql", names) == ["app_db"]


def test_filter_system_databases_for_mysql_family():
    """MySQL-family system databases should be hidden from list views."""
    names = ["mysql", "information_schema", "performance_schema", "sys", "app_db"]
    assert filter_system_databases("mysql", names) == ["app_db"]
    assert filter_system_databases("mariadb", names) == ["app_db"]


def test_build_create_user_sql_for_postgresql():
    """PostgreSQL user creation should generate the correct SQL."""
    sql = build_create_user_sql("postgresql", "forge_app", "secret")
    assert sql == 'CREATE USER "forge_app" WITH PASSWORD \'secret\';'


def test_build_create_user_sql_for_mysql():
    """MySQL user creation should include host scope and password."""
    sql = build_create_user_sql("mysql", "forge_app", "secret", host="%")
    assert sql == "CREATE USER 'forge_app'@'%' IDENTIFIED BY 'secret';"


@patch("databases.run_command")
def test_list_databases_filters_postgresql_system_databases(mock_run):
    """List views should return only non-system PostgreSQL databases."""
    mock_run.return_value = (0, "postgres\ntemplate0\ntemplate1\napp_db", "")

    assert list_databases("postgresql") == ["app_db"]


@patch("databases.confirm_action", return_value=False)
@patch("databases.run_command")
def test_delete_database_requires_confirmation(mock_run, mock_confirm):
    """Delete database should not execute without confirmation."""
    assert delete_database("postgresql", "app_db") is False
    mock_run.assert_not_called()
