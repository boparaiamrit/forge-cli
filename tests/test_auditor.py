"""
Tests for Configuration Auditor module
"""

import pytest
from unittest.mock import patch, MagicMock


class TestAuditDefinitions:
    """Tests for audit definition data structures."""

    def test_nginx_security_headers_defined(self):
        """Test NGINX_SECURITY_HEADERS has expected headers."""
        from auditor import NGINX_SECURITY_HEADERS

        expected_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
        ]

        for header in expected_headers:
            assert header in NGINX_SECURITY_HEADERS
            assert "value" in NGINX_SECURITY_HEADERS[header]
            assert "directive" in NGINX_SECURITY_HEADERS[header]
            assert "severity" in NGINX_SECURITY_HEADERS[header]

    def test_nginx_optimizations_defined(self):
        """Test NGINX_OPTIMIZATIONS has expected settings."""
        from auditor import NGINX_OPTIMIZATIONS

        expected_opts = ["gzip", "client_max_body_size", "timeouts"]

        for opt in expected_opts:
            assert opt in NGINX_OPTIMIZATIONS
            assert "check" in NGINX_OPTIMIZATIONS[opt]
            assert "directive" in NGINX_OPTIMIZATIONS[opt]

    def test_php_recommended_settings_defined(self):
        """Test PHP_RECOMMENDED_SETTINGS has expected settings."""
        from auditor import PHP_RECOMMENDED_SETTINGS

        expected_settings = [
            "memory_limit",
            "upload_max_filesize",
            "max_execution_time",
            "opcache.enable",
        ]

        for setting in expected_settings:
            assert setting in PHP_RECOMMENDED_SETTINGS
            assert "recommended" in PHP_RECOMMENDED_SETTINGS[setting]
            assert "severity" in PHP_RECOMMENDED_SETTINGS[setting]


class TestPHPValueParser:
    """Tests for PHP value parsing."""

    def test_parse_memory_value_megabytes(self):
        """Test parsing memory values with M suffix."""
        from auditor import parse_php_value

        assert parse_php_value("128M") == 128 * 1024 * 1024
        assert parse_php_value("512M") == 512 * 1024 * 1024

    def test_parse_memory_value_gigabytes(self):
        """Test parsing memory values with G suffix."""
        from auditor import parse_php_value

        assert parse_php_value("1G") == 1024 * 1024 * 1024
        assert parse_php_value("2G") == 2 * 1024 * 1024 * 1024

    def test_parse_memory_value_kilobytes(self):
        """Test parsing memory values with K suffix."""
        from auditor import parse_php_value

        assert parse_php_value("1024K") == 1024 * 1024

    def test_parse_boolean_values(self):
        """Test parsing boolean-like PHP values."""
        from auditor import parse_php_value

        assert parse_php_value("On") == 1
        assert parse_php_value("OFF") == 0
        assert parse_php_value("1") == 1
        assert parse_php_value("0") == 0

    def test_parse_numeric_values(self):
        """Test parsing plain numeric values."""
        from auditor import parse_php_value

        assert parse_php_value("300") == 300
        assert parse_php_value("3000") == 3000


class TestAuditorMenu:
    """Tests for auditor menu structure."""

    def test_menu_choices_exist(self):
        """Test AUDITOR_MENU_CHOICES is defined."""
        from auditor import AUDITOR_MENU_CHOICES

        assert isinstance(AUDITOR_MENU_CHOICES, list)
        assert len(AUDITOR_MENU_CHOICES) > 0

    def test_all_audit_options_present(self):
        """Test all audit options are in the menu."""
        from auditor import AUDITOR_MENU_CHOICES

        values = [c.get("value") for c in AUDITOR_MENU_CHOICES if isinstance(c, dict)]

        assert "audit_all" in values
        assert "audit_nginx" in values
        assert "audit_php" in values
        assert "audit_services" in values
        assert "audit_security" in values


class TestPHPVersions:
    """Tests for PHP version support."""

    def test_php_versions_include_84_85(self):
        """Test PHP 8.4 and 8.5 are in version list."""
        from php import PHP_VERSIONS

        assert "8.5" in PHP_VERSIONS
        assert "8.4" in PHP_VERSIONS
        assert "8.3" in PHP_VERSIONS

    def test_php_services_include_84_85(self):
        """Test PHP 8.4 and 8.5 FPM are in services."""
        from services import SERVICE_CATEGORIES

        php_services = [s["service"] for s in SERVICE_CATEGORIES["php"]["services"]]

        assert "php8.5-fpm" in php_services
        assert "php8.4-fpm" in php_services
        assert "php8.3-fpm" in php_services
