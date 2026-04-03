"""Tests for main CLI routing."""

from unittest.mock import patch

import cli


def test_main_menu_includes_database_management():
    """Main menu should expose database management."""
    menu_values = [choice["value"] for choice in cli.MAIN_MENU_CHOICES if isinstance(choice, dict)]
    assert "databases" in menu_values


def test_handle_main_menu_choice_routes_to_database_menu():
    """Database menu selection should route to the database module."""
    with patch("cli.run_databases_menu") as mock_run:
        cli.handle_main_menu_choice("databases")

    mock_run.assert_called_once_with()
