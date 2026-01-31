"""
Tests for Shell Utilities
"""

import pytest
from unittest.mock import patch, MagicMock
import subprocess

from utils.shell import (
    run_command,
    command_exists,
    get_command_output,
    run_with_spinner,
)


class TestRunCommand:
    """Test run_command function."""

    @patch("subprocess.run")
    def test_run_command_success(self, mock_run):
        """Should return stdout on success."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr="",
        )

        code, stdout, stderr = run_command("echo test")

        assert code == 0
        assert stdout == "output"
        assert stderr == ""

    @patch("subprocess.run")
    def test_run_command_failure(self, mock_run):
        """Should return stderr on failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "cmd", output="", stderr="error message"
        )

        code, stdout, stderr = run_command("invalid command", check=False)

        assert code == 1

    @patch("subprocess.run")
    def test_run_command_with_sudo(self, mock_run):
        """Should prepend sudo when requested."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        run_command("apt update", sudo=True)

        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "sudo"

    def test_run_command_not_found(self):
        """Should handle command not found."""
        code, stdout, stderr = run_command("nonexistent_command_xyz", check=False)

        assert code == 127
        assert "not found" in stderr.lower() or code == 127


class TestCommandExists:
    """Test command_exists function."""

    def test_command_exists_python(self):
        """Python should exist."""
        assert command_exists("python3") is True or command_exists("python") is True

    def test_command_not_exists(self):
        """Nonexistent command should return False."""
        assert command_exists("nonexistent_command_xyz123") is False


class TestGetCommandOutput:
    """Test get_command_output function."""

    def test_get_output_failure(self):
        """Should return None for failed command."""
        result = get_command_output("nonexistent_command_xyz")
        assert result is None
