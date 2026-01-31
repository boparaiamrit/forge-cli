"""
Tests for Package Installers
"""

import pytest
from unittest.mock import patch, MagicMock

from installers import (
    install_nginx,
    install_php,
    install_node,
    install_redis,
    install_certbot,
    install_composer,
    install_mysql,
    install_postgresql,
)


class TestNginxInstaller:
    """Test Nginx installation."""

    @patch("installers.run_command")
    def test_installs_nginx_package(self, mock_run):
        """Should install nginx via apt."""
        mock_run.return_value = (0, "", "")

        install_nginx()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("apt" in call and "nginx" in call for call in calls)

    @patch("installers.run_command")
    def test_enables_nginx_service(self, mock_run):
        """Should enable nginx with systemctl."""
        mock_run.return_value = (0, "", "")

        install_nginx()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("systemctl enable nginx" in call for call in calls)


class TestPHPInstaller:
    """Test PHP installation."""

    @patch("installers.run_command")
    def test_installs_php_with_version(self, mock_run):
        """Should install specific PHP version."""
        mock_run.return_value = (0, "", "")

        install_php("8.3")

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("php8.3" in call for call in calls)

    @patch("installers.run_command")
    def test_installs_common_extensions(self, mock_run):
        """Should install common PHP extensions."""
        mock_run.return_value = (0, "", "")

        install_php("8.3")

        calls = [str(call) for call in mock_run.call_args_list]
        # Check for some common extensions
        call_str = " ".join(calls)
        assert "fpm" in call_str
        assert "mysql" in call_str
        assert "mbstring" in call_str

    @patch("installers.run_command")
    def test_adds_ondrej_ppa(self, mock_run):
        """Should add ondrej/php PPA."""
        mock_run.return_value = (0, "", "")

        install_php("8.3")

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("ondrej/php" in call for call in calls)


class TestNodeInstaller:
    """Test Node.js installation via NVM."""

    @patch("installers.run_command")
    def test_installs_nvm(self, mock_run):
        """Should install NVM."""
        mock_run.return_value = (0, "", "")

        install_node()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("nvm" in call.lower() for call in calls)


class TestRedisInstaller:
    """Test Redis installation."""

    @patch("installers.run_command")
    def test_installs_redis_server(self, mock_run):
        """Should install redis-server."""
        mock_run.return_value = (0, "", "")

        install_redis()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("redis-server" in call for call in calls)

    @patch("installers.run_command")
    def test_enables_redis_service(self, mock_run):
        """Should enable redis service."""
        mock_run.return_value = (0, "", "")

        install_redis()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("enable" in call and "redis" in call for call in calls)


class TestCertbotInstaller:
    """Test Certbot installation."""

    @patch("installers.run_command")
    def test_installs_certbot_with_nginx(self, mock_run):
        """Should install certbot with nginx plugin."""
        mock_run.return_value = (0, "", "")

        install_certbot()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("certbot" in call for call in calls)
        assert any("python3-certbot-nginx" in call for call in calls)


class TestMySQLInstaller:
    """Test MySQL installation."""

    @patch("installers.run_command")
    def test_installs_mysql_server(self, mock_run):
        """Should install mysql-server."""
        mock_run.return_value = (0, "", "")

        install_mysql()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("mysql-server" in call for call in calls)


class TestPostgreSQLInstaller:
    """Test PostgreSQL installation."""

    @patch("installers.run_command")
    def test_installs_postgresql(self, mock_run):
        """Should install postgresql."""
        mock_run.return_value = (0, "", "")

        install_postgresql()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("postgresql" in call for call in calls)
