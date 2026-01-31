"""
Tests for Server Hardening
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open

from provisioning.hardening import (
    harden_ssh,
    setup_firewall,
    setup_fail2ban,
    disable_unused_services,
    setup_automatic_updates,
    secure_shared_memory,
    setup_sysctl_hardening,
    create_deploy_user,
)


class TestSSHHardening:
    """Test SSH hardening functions."""

    @patch("provisioning.hardening.run_command")
    def test_harden_ssh_disables_root_login(self, mock_run):
        """SSH hardening should disable root login."""
        mock_run.return_value = (0, "", "")

        result = harden_ssh()

        # Check that sed commands were called for root login
        calls = [str(call) for call in mock_run.call_args_list]
        assert any("PermitRootLogin no" in call for call in calls)

    @patch("provisioning.hardening.run_command")
    def test_harden_ssh_disables_password_auth(self, mock_run):
        """SSH hardening should disable password authentication."""
        mock_run.return_value = (0, "", "")

        harden_ssh()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("PasswordAuthentication no" in call for call in calls)


class TestFirewallSetup:
    """Test UFW firewall configuration."""

    @patch("provisioning.hardening.run_command")
    def test_firewall_allows_ssh(self, mock_run):
        """Firewall should allow SSH connections."""
        mock_run.return_value = (0, "", "")

        setup_firewall()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("allow" in call and ("22" in call or "OpenSSH" in call) for call in calls)

    @patch("provisioning.hardening.run_command")
    def test_firewall_allows_http_https(self, mock_run):
        """Firewall should allow HTTP and HTTPS."""
        mock_run.return_value = (0, "", "")

        setup_firewall()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("80" in call for call in calls)
        assert any("443" in call for call in calls)

    @patch("provisioning.hardening.run_command")
    def test_firewall_denies_incoming_by_default(self, mock_run):
        """Firewall should deny incoming by default."""
        mock_run.return_value = (0, "", "")

        setup_firewall()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("default deny incoming" in call for call in calls)


class TestFail2BanSetup:
    """Test Fail2Ban configuration."""

    @patch("builtins.open", mock_open())
    @patch("provisioning.hardening.run_command")
    def test_fail2ban_installs_package(self, mock_run):
        """Should install fail2ban package."""
        mock_run.return_value = (0, "", "")

        setup_fail2ban()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("apt-get install" in call and "fail2ban" in call for call in calls)


class TestDeployUser:
    """Test deploy user creation."""

    @patch("provisioning.hardening.run_command")
    def test_creates_user(self, mock_run):
        """Should create the deploy user."""
        mock_run.return_value = (0, "", "")

        create_deploy_user("forge")

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("useradd" in call and "forge" in call for call in calls)

    @patch("provisioning.hardening.run_command")
    def test_adds_to_sudo_group(self, mock_run):
        """Should add user to sudo group."""
        mock_run.return_value = (0, "", "")

        create_deploy_user("forge")

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("sudo" in call for call in calls)

    @patch("provisioning.hardening.run_command")
    def test_creates_ssh_directory(self, mock_run):
        """Should create .ssh directory with correct permissions."""
        mock_run.return_value = (0, "", "")

        create_deploy_user("forge")

        calls = [str(call) for call in mock_run.call_args_list]
        assert any(".ssh" in call for call in calls)
        assert any("700" in call for call in calls)


class TestSysctlHardening:
    """Test kernel hardening."""

    @patch("builtins.open", mock_open())
    @patch("provisioning.hardening.run_command")
    def test_applies_sysctl_settings(self, mock_run):
        """Should apply sysctl settings."""
        mock_run.return_value = (0, "", "")

        setup_sysctl_hardening()

        calls = [str(call) for call in mock_run.call_args_list]
        assert any("sysctl" in call for call in calls)
