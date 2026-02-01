"""
Tests for CVE Scanner module
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCVEMenuStructure:
    """Tests for CVE menu structure."""

    def test_menu_choices_exist(self):
        """Test CVE_MENU_CHOICES is defined."""
        from cve import CVE_MENU_CHOICES

        assert isinstance(CVE_MENU_CHOICES, list)
        assert len(CVE_MENU_CHOICES) > 0

    def test_all_menu_options_present(self):
        """Test all CVE options are in the menu."""
        from cve import CVE_MENU_CHOICES

        values = [c.get("value") for c in CVE_MENU_CHOICES if isinstance(c, dict)]

        assert "full_scan" in values
        assert "scan_system" in values
        assert "scan_apps" in values
        assert "update_db" in values
        assert "setup_cron" in values


class TestCVEDataPaths:
    """Tests for CVE data paths."""

    def test_cve_directories_defined(self):
        """Test CVE data directories are defined."""
        from cve import CVE_DATA_DIR, CVE_SCANS_DIR

        assert CVE_DATA_DIR is not None
        assert CVE_SCANS_DIR is not None
        assert ".forge" in str(CVE_DATA_DIR)
        assert "cve" in str(CVE_DATA_DIR)


class TestDependencyFiles:
    """Tests for dependency file detection."""

    def test_dependency_files_defined(self):
        """Test DEPENDENCY_FILES dictionary is defined."""
        from cve import DEPENDENCY_FILES

        assert isinstance(DEPENDENCY_FILES, dict)
        assert "package.json" in DEPENDENCY_FILES
        assert "composer.json" in DEPENDENCY_FILES
        assert "requirements.txt" in DEPENDENCY_FILES

    def test_dependency_ecosystems(self):
        """Test each dependency file maps to correct ecosystem."""
        from cve import DEPENDENCY_FILES

        assert DEPENDENCY_FILES["package.json"] == "nodejs"
        assert DEPENDENCY_FILES["composer.json"] == "php"
        assert DEPENDENCY_FILES["requirements.txt"] == "python"


class TestUbuntuVersions:
    """Tests for Ubuntu version support."""

    def test_ubuntu_versions_defined(self):
        """Test UBUNTU_VERSIONS dictionary is defined."""
        from cve import UBUNTU_VERSIONS

        assert isinstance(UBUNTU_VERSIONS, dict)
        assert "24.04" in UBUNTU_VERSIONS
        assert "22.04" in UBUNTU_VERSIONS
        assert "20.04" in UBUNTU_VERSIONS

    def test_ubuntu_codenames(self):
        """Test Ubuntu codenames are correct."""
        from cve import UBUNTU_VERSIONS

        assert UBUNTU_VERSIONS["24.04"] == "noble"
        assert UBUNTU_VERSIONS["22.04"] == "jammy"
        assert UBUNTU_VERSIONS["20.04"] == "focal"


class TestDefaultScanDirs:
    """Tests for default scan directories."""

    def test_default_scan_dirs_defined(self):
        """Test DEFAULT_SCAN_DIRS is defined."""
        from cve import DEFAULT_SCAN_DIRS

        assert isinstance(DEFAULT_SCAN_DIRS, list)
        assert "/var/www" in DEFAULT_SCAN_DIRS
        assert "/home" in DEFAULT_SCAN_DIRS


class TestScanResultsSaving:
    """Tests for scan results functions."""

    def test_save_scan_results_function_exists(self):
        """Test save_scan_results function exists."""
        from cve import save_scan_results

        assert callable(save_scan_results)

    def test_get_ubuntu_version_function_exists(self):
        """Test get_ubuntu_version function exists."""
        from cve import get_ubuntu_version

        assert callable(get_ubuntu_version)


class TestNpmScanFunction:
    """Tests for npm scanning."""

    def test_scan_npm_dependencies_function_exists(self):
        """Test scan_npm_dependencies function exists."""
        from cve import scan_npm_dependencies

        assert callable(scan_npm_dependencies)


class TestComposerScanFunction:
    """Tests for composer scanning."""

    def test_scan_composer_dependencies_function_exists(self):
        """Test scan_composer_dependencies function exists."""
        from cve import scan_composer_dependencies

        assert callable(scan_composer_dependencies)


class TestPythonScanFunction:
    """Tests for Python scanning."""

    def test_scan_python_dependencies_function_exists(self):
        """Test scan_python_dependencies function exists."""
        from cve import scan_python_dependencies

        assert callable(scan_python_dependencies)
