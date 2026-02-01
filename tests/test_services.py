"""
Tests for enhanced Services module
"""

import pytest
from unittest.mock import patch, MagicMock


class TestServiceCategories:
    """Tests for service category definitions."""

    def test_service_categories_exist(self):
        """Test SERVICE_CATEGORIES has all expected categories."""
        from services import SERVICE_CATEGORIES

        expected_categories = [
            "web", "php", "database", "cache", "queue",
            "mail", "monitoring", "security", "ssl", "system", "docker"
        ]

        for cat in expected_categories:
            assert cat in SERVICE_CATEGORIES
            assert "name" in SERVICE_CATEGORIES[cat]
            assert "services" in SERVICE_CATEGORIES[cat]

    def test_web_services(self):
        """Test web server services are defined."""
        from services import SERVICE_CATEGORIES

        web_services = [s["service"] for s in SERVICE_CATEGORIES["web"]["services"]]

        assert "nginx" in web_services
        assert "apache2" in web_services

    def test_php_services(self):
        """Test PHP-FPM services are defined."""
        from services import SERVICE_CATEGORIES

        php_services = [s["service"] for s in SERVICE_CATEGORIES["php"]["services"]]

        assert "php8.3-fpm" in php_services
        assert "php8.2-fpm" in php_services
        assert "php8.1-fpm" in php_services

    def test_database_services(self):
        """Test database services are defined."""
        from services import SERVICE_CATEGORIES

        db_services = [s["service"] for s in SERVICE_CATEGORIES["database"]["services"]]

        assert "mysql" in db_services
        assert "postgresql" in db_services

    def test_security_services(self):
        """Test security services are defined."""
        from services import SERVICE_CATEGORIES

        sec_services = [s["service"] for s in SERVICE_CATEGORIES["security"]["services"]]

        assert "ufw" in sec_services
        assert "fail2ban" in sec_services
        assert "clamav-daemon" in sec_services

    def test_critical_flags(self):
        """Test critical services are flagged correctly."""
        from services import SERVICE_CATEGORIES

        # Nginx should be critical
        nginx = next(
            s for s in SERVICE_CATEGORIES["web"]["services"]
            if s["service"] == "nginx"
        )
        assert nginx["critical"] is True

        # SSH should be critical
        ssh = next(
            s for s in SERVICE_CATEGORIES["system"]["services"]
            if s["service"] == "ssh"
        )
        assert ssh["critical"] is True


class TestServiceHelpers:
    """Tests for service helper functions."""

    @patch("services.run_command")
    def test_get_service_status_active(self, mock_run):
        """Test getting active service status."""
        from services import get_service_status

        mock_run.return_value = (0, "active", "")

        status = get_service_status("nginx")
        assert status == "active"

    @patch("services.run_command")
    def test_get_service_status_inactive(self, mock_run):
        """Test getting inactive service status."""
        from services import get_service_status

        mock_run.return_value = (0, "inactive", "")

        status = get_service_status("nginx")
        assert status == "inactive"

    @patch("services.run_command")
    def test_is_service_enabled_true(self, mock_run):
        """Test checking if service is enabled."""
        from services import is_service_enabled

        mock_run.return_value = (0, "enabled", "")

        assert is_service_enabled("nginx") is True

    @patch("services.run_command")
    def test_is_service_enabled_false(self, mock_run):
        """Test checking if service is disabled."""
        from services import is_service_enabled

        mock_run.return_value = (0, "disabled", "")

        assert is_service_enabled("nginx") is False

    @patch("services.run_command")
    def test_get_service_memory(self, mock_run):
        """Test getting service memory usage."""
        from services import get_service_memory

        # 50 MB
        mock_run.return_value = (0, str(50 * 1024 * 1024), "")

        memory = get_service_memory("nginx")
        assert "50" in memory
        assert "MB" in memory

    @patch("services.run_command")
    def test_get_service_memory_not_set(self, mock_run):
        """Test getting memory when not set."""
        from services import get_service_memory

        mock_run.return_value = (0, "[not set]", "")

        memory = get_service_memory("nginx")
        assert memory == "-"


class TestSSLAutoRenewal:
    """Tests for SSL auto-renewal setup."""

    @patch("sslcerts.run_command")
    def test_setup_auto_renewal_timer_exists(self, mock_run):
        """Test auto-renewal when timer is already enabled."""
        from sslcerts import setup_auto_renewal

        mock_run.return_value = (0, "enabled", "")

        # Should not raise and should check for timer
        setup_auto_renewal()

        # Verify systemctl is-enabled was called
        calls = [str(c) for c in mock_run.call_args_list]
        assert any("is-enabled" in c and "certbot.timer" in c for c in calls)
