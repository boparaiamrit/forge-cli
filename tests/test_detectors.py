"""
Tests for System Detectors
"""

import pytest
from unittest.mock import patch, MagicMock

from detectors import (
    detect_nginx,
    detect_php,
    detect_node,
    detect_redis,
    detect_certbot,
    detect_mysql,
    detect_postgresql,
    detect_composer,
    detect_pm2,
    get_system_status,
)


class TestNginxDetector:
    """Test Nginx detection."""

    @patch("detectors.command_exists")
    def test_nginx_not_installed(self, mock_exists):
        """Should return not installed when nginx command not found."""
        mock_exists.return_value = False

        result = detect_nginx()

        assert result["name"] == "🌐 Nginx"
        assert result["installed"] is False
        assert result["version"] is None

    @patch("detectors.run_command")
    @patch("detectors.command_exists")
    def test_nginx_installed(self, mock_exists, mock_run):
        """Should detect Nginx version when installed."""
        mock_exists.return_value = True
        mock_run.side_effect = [
            (0, "", "nginx version: nginx/1.24.0 (Ubuntu)"),  # nginx -v
            (0, "active", ""),  # systemctl is-active
        ]

        result = detect_nginx()

        assert result["installed"] is True
        assert result["version"] == "1.24.0"
        assert result["details"] == "Running"

    @patch("detectors.run_command")
    @patch("detectors.command_exists")
    def test_nginx_stopped(self, mock_exists, mock_run):
        """Should detect when Nginx is stopped."""
        mock_exists.return_value = True
        mock_run.side_effect = [
            (0, "", "nginx version: nginx/1.24.0"),
            (0, "inactive", ""),  # systemctl is-active
        ]

        result = detect_nginx()

        assert result["details"] == "Stopped"


class TestPHPDetector:
    """Test PHP detection."""

    @patch("detectors.command_exists")
    def test_php_not_installed(self, mock_exists):
        """Should return not installed when php not found."""
        mock_exists.return_value = False

        result = detect_php()

        assert result["name"] == "🐘 PHP"
        assert result["installed"] is False

    @patch("detectors.get_command_output")
    @patch("detectors.command_exists")
    def test_php_installed(self, mock_exists, mock_output):
        """Should detect PHP version and extensions."""
        mock_exists.return_value = True
        mock_output.side_effect = [
            "PHP 8.3.1 (cli) (built: Jan 16 2024)",  # php -v
            "Core\ndate\njson\nmysqli\npdo",  # php -m
        ]

        result = detect_php()

        assert result["installed"] is True
        assert result["version"] == "8.3.1"
        assert "extensions" in result["details"]


class TestNodeDetector:
    """Test Node.js detection."""

    @patch("detectors.command_exists")
    def test_node_not_installed(self, mock_exists):
        """Should return not installed when node not found."""
        mock_exists.return_value = False

        result = detect_node()

        assert result["name"] == "🟢 Node.js"
        assert result["installed"] is False

    @patch("detectors.get_command_output")
    @patch("detectors.command_exists")
    def test_node_installed_via_nvm(self, mock_exists, mock_output):
        """Should detect Node.js installed via NVM."""
        mock_exists.return_value = True
        mock_output.side_effect = [
            "v20.11.0",  # node -v
            "/home/user/.nvm",  # echo $NVM_DIR
        ]

        result = detect_node()

        assert result["installed"] is True
        assert result["version"] == "20.11.0"
        assert result["details"] == "via NVM"


class TestRedisDetector:
    """Test Redis detection."""

    @patch("detectors.command_exists")
    def test_redis_not_installed(self, mock_exists):
        """Should return not installed when redis-cli not found."""
        mock_exists.return_value = False

        result = detect_redis()

        assert result["name"] == "🔴 Redis"
        assert result["installed"] is False


class TestCertbotDetector:
    """Test Certbot detection."""

    @patch("detectors.command_exists")
    def test_certbot_not_installed(self, mock_exists):
        """Should return not installed when certbot not found."""
        mock_exists.return_value = False

        result = detect_certbot()

        assert result["name"] == "🔒 Certbot"
        assert result["installed"] is False


class TestMySQLDetector:
    """Test MySQL/MariaDB detection."""

    @patch("detectors.command_exists")
    def test_mysql_not_installed(self, mock_exists):
        """Should return not installed when mysql not found."""
        mock_exists.return_value = False

        result = detect_mysql()

        assert result["installed"] is False


class TestSystemStatus:
    """Test full system status."""

    @patch("detectors.detect_composer")
    @patch("detectors.detect_postgresql")
    @patch("detectors.detect_mysql")
    @patch("detectors.detect_certbot")
    @patch("detectors.detect_redis")
    @patch("detectors.detect_pm2")
    @patch("detectors.detect_node")
    @patch("detectors.detect_php")
    @patch("detectors.detect_nginx")
    def test_get_system_status_returns_all(self, *mocks):
        """Should return status for all detectors."""
        for mock in mocks:
            mock.return_value = {"name": "Test", "installed": False, "version": None, "details": None}

        result = get_system_status()

        assert len(result) == 9  # All detectors
        assert all("name" in item for item in result)
