"""
Tests for Updater module
"""

import pytest


class TestUpdaterModule:
    """Tests for updater module."""

    def test_module_imports(self):
        """Test that the updater module imports correctly."""
        from updater import (
            run_updater_menu,
            get_current_version,
            get_latest_version,
            compare_versions,
            check_for_updates,
            startup_update_check,
        )
        assert callable(run_updater_menu)
        assert callable(get_current_version)
        assert callable(get_latest_version)
        assert callable(compare_versions)
        assert callable(check_for_updates)
        assert callable(startup_update_check)

    def test_get_current_version(self):
        """Test getting current version."""
        from updater import get_current_version

        version = get_current_version()
        assert version is not None
        assert isinstance(version, str)
        # Version should be in format x.x.x
        parts = version.split(".")
        assert len(parts) >= 2

    def test_github_repo_constant(self):
        """Test GitHub repo constant is set."""
        from updater import GITHUB_REPO

        assert GITHUB_REPO is not None
        assert "/" in GITHUB_REPO


class TestVersionComparison:
    """Tests for version comparison logic."""

    def test_compare_equal_versions(self):
        """Test comparing equal versions."""
        from updater import compare_versions

        assert compare_versions("1.0.0", "1.0.0") == 0
        assert compare_versions("0.9.0", "0.9.0") == 0
        assert compare_versions("2.1.3", "2.1.3") == 0

    def test_compare_older_version(self):
        """Test comparing when current is older."""
        from updater import compare_versions

        assert compare_versions("0.8.0", "0.9.0") == -1
        assert compare_versions("1.0.0", "1.0.1") == -1
        assert compare_versions("1.0.0", "2.0.0") == -1
        assert compare_versions("0.1.0", "0.2.0") == -1

    def test_compare_newer_version(self):
        """Test comparing when current is newer."""
        from updater import compare_versions

        assert compare_versions("0.9.0", "0.8.0") == 1
        assert compare_versions("1.0.1", "1.0.0") == 1
        assert compare_versions("2.0.0", "1.0.0") == 1
        assert compare_versions("0.10.0", "0.9.0") == 1

    def test_compare_with_v_prefix(self):
        """Test comparing versions with v prefix."""
        from updater import compare_versions

        assert compare_versions("v1.0.0", "1.0.0") == 0
        assert compare_versions("1.0.0", "v1.0.0") == 0
        assert compare_versions("v0.8.0", "v0.9.0") == -1

    def test_compare_different_lengths(self):
        """Test comparing versions with different lengths."""
        from updater import compare_versions

        assert compare_versions("1.0", "1.0.0") == 0
        assert compare_versions("1.0.0", "1.0") == 0
        assert compare_versions("1.0", "1.0.1") == -1


class TestUpdateCheck:
    """Tests for update checking."""

    def test_check_for_updates_returns_tuple(self):
        """Test that check_for_updates returns correct format."""
        from updater import check_for_updates

        result = check_for_updates(silent=True)
        assert isinstance(result, tuple)
        assert len(result) == 4  # (has_update, current, latest, error)

        has_update, current, latest, error = result
        assert isinstance(has_update, bool)
        assert isinstance(current, str)

    def test_startup_update_check(self):
        """Test startup update check."""
        from updater import startup_update_check

        # Should return None or a string
        result = startup_update_check()
        assert result is None or isinstance(result, str)
