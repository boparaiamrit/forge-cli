"""
Utility functions for Forge CLI
"""

from utils.ui import (
    clear_screen,
    print_header,
    print_breadcrumb,
    print_success,
    print_error,
    print_warning,
    print_info,
    confirm_action,
)
from utils.shell import (
    run_command,
    command_exists,
    get_command_output,
    run_with_spinner,
)

__all__ = [
    "clear_screen",
    "print_header",
    "print_breadcrumb",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "confirm_action",
    "run_command",
    "command_exists",
    "get_command_output",
    "run_with_spinner",
]
