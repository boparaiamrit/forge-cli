"""
Shell Utilities - Command execution helpers
"""

import subprocess
import shutil
from typing import Optional, Tuple
from rich.console import Console

console = Console()


def run_command(
    command: str | list[str],
    capture: bool = True,
    sudo: bool = False,
    check: bool = True,
) -> Tuple[int, str, str]:
    """
    Run a shell command and return (returncode, stdout, stderr).

    Args:
        command: Command string or list of args
        capture: Whether to capture output
        sudo: Whether to prepend sudo
        check: Whether to raise on non-zero exit

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    if isinstance(command, str):
        cmd_list = command.split()
    else:
        cmd_list = command

    if sudo and cmd_list[0] != "sudo":
        cmd_list = ["sudo"] + cmd_list

    try:
        result = subprocess.run(
            cmd_list,
            capture_output=capture,
            text=True,
            check=check,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout or "", e.stderr or ""
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd_list[0]}"


def command_exists(command: str) -> bool:
    """Check if a command is available in PATH."""
    return shutil.which(command) is not None


def get_command_output(command: str) -> Optional[str]:
    """Run a command and return stdout, or None on failure."""
    code, stdout, _ = run_command(command, check=False)
    return stdout if code == 0 else None


def run_with_spinner(command: str, message: str, sudo: bool = False) -> Tuple[bool, str]:
    """
    Run a command with a spinner and return (success, output).
    """
    with console.status(f"[bold cyan]{message}...", spinner="dots"):
        code, stdout, stderr = run_command(command, sudo=sudo, check=False)

    success = code == 0
    output = stdout if success else stderr
    return success, output
