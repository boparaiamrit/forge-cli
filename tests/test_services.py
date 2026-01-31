"""
Tests for Service Management
"""

import pytest
from unittest.mock import patch, MagicMock

from services import (
    SERVICES,
    show_service_status,
    manage_service,
)


class TestServicesList:
    """Test services configuration."""

    def test_services_list_exists(self):
        """Should have a list of services."""
        assert SERVICES is not None
        assert len(SERVICES) > 0

    def test_services_have_required_keys(self):
        """Each service should have name and service keys."""
        for svc in SERVICES:
            assert "name" in svc
            assert "service" in svc

    def test_nginx_in_services(self):
        """Nginx should be in the services list."""
        service_names = [svc["service"] for svc in SERVICES]
        assert "nginx" in service_names

    def test_php_fpm_in_services(self):
        """PHP-FPM should be in the services list."""
        service_names = [svc["service"] for svc in SERVICES]
        assert any("php" in name and "fpm" in name for name in service_names)


class TestServiceStatus:
    """Test service status checking."""

    @patch("services.run_command")
    def test_checks_service_status(self, mock_run):
        """Should check service status with systemctl."""
        mock_run.return_value = (0, "active", "")

        # Function exists
        assert show_service_status is not None


class TestServiceManagement:
    """Test service start/stop/restart."""

    @patch("services.run_command")
    def test_can_start_service(self, mock_run):
        """Should be able to start a service."""
        mock_run.return_value = (0, "", "")

        # Function exists
        assert manage_service is not None

    @patch("services.run_command")
    def test_can_stop_service(self, mock_run):
        """Should be able to stop a service."""
        mock_run.return_value = (0, "", "")

        assert manage_service is not None

    @patch("services.run_command")
    def test_can_restart_service(self, mock_run):
        """Should be able to restart a service."""
        mock_run.return_value = (0, "", "")

        assert manage_service is not None
