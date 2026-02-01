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
from utils.network import (
    get_local_ips,
    get_public_ip,
    check_dns_resolution,
    verify_domain_points_to_server,
    check_port_open,
    get_listening_ports,
    http_check,
    check_ssl_certificate,
)

__all__ = [
    # UI
    "clear_screen",
    "print_header",
    "print_breadcrumb",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "confirm_action",
    # Shell
    "run_command",
    "command_exists",
    "get_command_output",
    "run_with_spinner",
    # Network
    "get_local_ips",
    "get_public_ip",
    "check_dns_resolution",
    "verify_domain_points_to_server",
    "check_port_open",
    "get_listening_ports",
    "http_check",
    "check_ssl_certificate",
]
