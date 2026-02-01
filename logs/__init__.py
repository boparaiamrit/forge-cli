"""
Log Management - View, monitor, and analyze server logs
"""

import os
import re
import time
import questionary
from datetime import datetime
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, print_warning, print_info
)
from utils.shell import run_command, get_command_output

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# LOG PATHS
# ═══════════════════════════════════════════════════════════════════════════════

LOG_PATHS = {
    "nginx_access": "/var/log/nginx/access.log",
    "nginx_error": "/var/log/nginx/error.log",
    "php_fpm": "/var/log/php{version}-fpm.log",
    "mysql": "/var/log/mysql/error.log",
    "postgresql": "/var/log/postgresql/postgresql-*-main.log",
    "syslog": "/var/log/syslog",
    "auth": "/var/log/auth.log",
}

# HTTP status code colors
STATUS_COLORS = {
    "2": "green",      # 2xx - Success
    "3": "cyan",       # 3xx - Redirect
    "4": "yellow",     # 4xx - Client Error
    "5": "red bold",   # 5xx - Server Error
}

# Log level colors
LEVEL_COLORS = {
    "error": "red bold",
    "warn": "yellow",
    "warning": "yellow",
    "notice": "cyan",
    "info": "blue",
    "debug": "dim",
}


# ═══════════════════════════════════════════════════════════════════════════════
# LOG MENU
# ═══════════════════════════════════════════════════════════════════════════════

LOG_MENU_CHOICES = [
    {"name": "🌐 Nginx Access Logs", "value": "nginx_access"},
    {"name": "❌ Nginx Error Logs", "value": "nginx_error"},
    {"name": "🌍 Site-Specific Logs", "value": "site"},
    {"name": "🔴 Real-Time Monitor", "value": "live"},
    {"name": "🔍 Search Logs", "value": "search"},
    {"name": "📊 Error Summary", "value": "summary"},
    questionary.Separator("─" * 30),
    {"name": "⬅️ Back", "value": "back"},
]


def run_logs_menu():
    """Display the log management menu."""
    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "Logs"])

        choice = questionary.select(
            "Log Management:",
            choices=LOG_MENU_CHOICES,
            qmark="📜",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "nginx_access":
            view_nginx_access_logs()
        elif choice == "nginx_error":
            view_nginx_error_logs()
        elif choice == "site":
            view_site_logs()
        elif choice == "live":
            live_log_monitor()
        elif choice == "search":
            search_logs()
        elif choice == "summary":
            show_error_summary()


# ═══════════════════════════════════════════════════════════════════════════════
# LOG VIEWING
# ═══════════════════════════════════════════════════════════════════════════════

def view_nginx_access_logs():
    """View Nginx access logs with formatting."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Logs", "Nginx Access"])

    lines = questionary.text(
        "Number of lines to show:",
        default="50",
        validate=lambda x: x.isdigit() and 1 <= int(x) <= 1000,
    ).ask()

    if not lines:
        return

    console.print(f"\n[bold cyan]Last {lines} access log entries:[/bold cyan]\n")

    code, stdout, stderr = run_command(
        f"sudo tail -n {lines} /var/log/nginx/access.log",
        check=False
    )

    if code != 0:
        print_error(f"Failed to read logs: {stderr}")
    else:
        format_access_logs(stdout)

    console.print()
    questionary.press_any_key_to_continue().ask()


def view_nginx_error_logs():
    """View Nginx error logs."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Logs", "Nginx Errors"])

    # Filter by level
    level = questionary.select(
        "Filter by level:",
        choices=[
            {"name": "🔴 Errors only", "value": "error"},
            {"name": "🟡 Warnings and above", "value": "warn"},
            {"name": "📋 All levels", "value": "all"},
        ],
    ).ask()

    lines = questionary.text(
        "Number of lines to show:",
        default="50",
        validate=lambda x: x.isdigit() and 1 <= int(x) <= 1000,
    ).ask()

    if not lines:
        return

    console.print(f"\n[bold red]Last {lines} error log entries:[/bold red]\n")

    if level == "all":
        cmd = f"sudo tail -n {lines} /var/log/nginx/error.log"
    else:
        cmd = f"sudo grep -i '{level}' /var/log/nginx/error.log | tail -n {lines}"

    code, stdout, stderr = run_command(cmd, check=False)

    if code != 0 and "No such file" not in stderr:
        print_error(f"Failed to read logs: {stderr}")
    elif not stdout.strip():
        print_info("No matching log entries found.")
    else:
        format_error_logs(stdout)

    console.print()
    questionary.press_any_key_to_continue().ask()


def view_site_logs():
    """View logs for a specific site."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Logs", "Site Logs"])

    # Get list of sites from nginx logs
    code, stdout, _ = run_command(
        "ls /var/log/nginx/*.access.log 2>/dev/null | xargs -n1 basename | sed 's/.access.log//'",
        check=False
    )

    if code != 0 or not stdout.strip():
        # Fallback: list sites from sites-available
        code, stdout, _ = run_command("ls /etc/nginx/sites-available", check=False)
        sites = [s for s in stdout.split() if s != "default"]
    else:
        sites = stdout.split()

    if not sites:
        print_warning("No site-specific logs found.")
        questionary.press_any_key_to_continue().ask()
        return

    site = questionary.select(
        "Select site:",
        choices=sites + [questionary.Separator(), {"name": "⬅️ Cancel", "value": None}],
    ).ask()

    if not site:
        return

    log_type = questionary.select(
        "Log type:",
        choices=[
            {"name": "🌐 Access Log", "value": "access"},
            {"name": "❌ Error Log", "value": "error"},
        ],
    ).ask()

    log_path = f"/var/log/nginx/{site}.{log_type}.log"

    lines = questionary.text(
        "Number of lines:",
        default="50",
        validate=lambda x: x.isdigit(),
    ).ask()

    console.print(f"\n[bold]Logs for {site} ({log_type}):[/bold]\n")

    code, stdout, stderr = run_command(f"sudo tail -n {lines} {log_path}", check=False)

    if code != 0:
        print_error(f"Failed to read logs: {stderr}")
        # Try generic log
        code, stdout, _ = run_command(
            f"sudo grep '{site}' /var/log/nginx/{log_type}.log | tail -n {lines}",
            check=False
        )
        if stdout:
            if log_type == "access":
                format_access_logs(stdout)
            else:
                format_error_logs(stdout)
    else:
        if log_type == "access":
            format_access_logs(stdout)
        else:
            format_error_logs(stdout)

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE MONITORING
# ═══════════════════════════════════════════════════════════════════════════════

def live_log_monitor():
    """Real-time log monitoring with color coding."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Logs", "Live Monitor"])

    log_source = questionary.select(
        "Select log to monitor:",
        choices=[
            {"name": "🌐 Nginx Access (all sites)", "value": "nginx_access"},
            {"name": "❌ Nginx Errors (all sites)", "value": "nginx_error"},
            {"name": "📋 Syslog", "value": "syslog"},
        ],
    ).ask()

    if not log_source:
        return

    log_paths = {
        "nginx_access": "/var/log/nginx/access.log",
        "nginx_error": "/var/log/nginx/error.log",
        "syslog": "/var/log/syslog",
    }

    log_path = log_paths.get(log_source)

    console.print(f"\n[bold cyan]📡 Live monitoring: {log_path}[/bold cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    try:
        import subprocess
        process = subprocess.Popen(
            ["sudo", "tail", "-f", log_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        for line in process.stdout:
            line = line.strip()
            if log_source == "nginx_access":
                print_formatted_access_line(line)
            elif log_source == "nginx_error":
                print_formatted_error_line(line)
            else:
                console.print(line)

    except KeyboardInterrupt:
        process.terminate()
        console.print("\n[dim]Monitoring stopped.[/dim]")

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# LOG SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def search_logs():
    """Search through logs with filters."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Logs", "Search"])

    log_type = questionary.select(
        "Search in:",
        choices=[
            {"name": "🌐 Nginx Access Logs", "value": "access"},
            {"name": "❌ Nginx Error Logs", "value": "error"},
            {"name": "📋 All Nginx Logs", "value": "all"},
        ],
    ).ask()

    search_type = questionary.select(
        "Search by:",
        choices=[
            {"name": "🔍 Keyword/Pattern", "value": "keyword"},
            {"name": "🌐 IP Address", "value": "ip"},
            {"name": "📊 HTTP Status Code", "value": "status"},
            {"name": "📁 URL Path", "value": "path"},
        ],
    ).ask()

    pattern = questionary.text(
        "Enter search pattern:",
        validate=lambda x: len(x) > 0,
    ).ask()

    if not pattern:
        return

    console.print(f"\n[cyan]Searching for '{pattern}'...[/cyan]\n")

    # Build grep command
    if log_type == "access":
        log_path = "/var/log/nginx/access.log"
    elif log_type == "error":
        log_path = "/var/log/nginx/error.log"
    else:
        log_path = "/var/log/nginx/*.log"

    cmd = f"sudo grep -i '{pattern}' {log_path} | tail -n 100"
    code, stdout, stderr = run_command(cmd, check=False)

    if not stdout.strip():
        print_info("No matching entries found.")
    else:
        lines = stdout.split("\n")
        console.print(f"[green]Found {len(lines)} matching entries (showing last 100):[/green]\n")

        for line in lines:
            if "access" in log_path or log_type == "access":
                print_formatted_access_line(line)
            else:
                print_formatted_error_line(line)

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def show_error_summary():
    """Show summary of errors from logs."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Logs", "Error Summary"])

    console.print("\n[bold]🔍 Analyzing logs...[/bold]\n")

    # Get 4xx and 5xx errors count
    code, stdout, _ = run_command(
        "sudo awk '{print $9}' /var/log/nginx/access.log | grep -E '^[45]' | sort | uniq -c | sort -rn | head -10",
        check=False
    )

    table = Table(
        title="📊 HTTP Error Summary (Top 10)",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Count", justify="right", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Description")

    status_descriptions = {
        "400": "Bad Request",
        "401": "Unauthorized",
        "403": "Forbidden",
        "404": "Not Found",
        "405": "Method Not Allowed",
        "408": "Request Timeout",
        "419": "Page Expired (CSRF)",
        "429": "Too Many Requests",
        "500": "Internal Server Error",
        "502": "Bad Gateway",
        "503": "Service Unavailable",
        "504": "Gateway Timeout",
    }

    if stdout.strip():
        for line in stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                count, status = parts[0], parts[1]
                color = STATUS_COLORS.get(status[0], "white")
                desc = status_descriptions.get(status, "Unknown")
                table.add_row(count, f"[{color}]{status}[/{color}]", desc)

        console.print(table)
    else:
        print_info("No error data found.")

    # Show top error IPs
    console.print("\n[bold]🌐 Top IPs with Errors:[/bold]\n")

    code, stdout, _ = run_command(
        "sudo awk '$9 ~ /^[45]/ {print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -5",
        check=False
    )

    if stdout.strip():
        ip_table = Table(box=box.SIMPLE)
        ip_table.add_column("Count", justify="right")
        ip_table.add_column("IP Address")

        for line in stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                ip_table.add_row(parts[0], parts[1])

        console.print(ip_table)
    else:
        print_info("No error IP data found.")

    # Recent errors
    console.print("\n[bold]🔴 Most Recent Errors:[/bold]\n")

    code, stdout, _ = run_command(
        "sudo tail -n 5 /var/log/nginx/error.log",
        check=False
    )

    if stdout.strip():
        format_error_logs(stdout)
    else:
        print_info("No recent errors.")

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def format_access_logs(log_text: str):
    """Format and colorize access log entries."""
    for line in log_text.split("\n"):
        if line.strip():
            print_formatted_access_line(line)


def format_error_logs(log_text: str):
    """Format and colorize error log entries."""
    for line in log_text.split("\n"):
        if line.strip():
            print_formatted_error_line(line)


def print_formatted_access_line(line: str):
    """Print a single access log line with colors."""
    # Parse common log format
    # IP - - [date] "METHOD /path HTTP/x.x" status bytes "referer" "user-agent"

    # Try to extract status code
    match = re.search(r'" (\d{3}) ', line)
    if match:
        status = match.group(1)
        color = STATUS_COLORS.get(status[0], "white")

        # Highlight the status code
        highlighted = line.replace(f'" {status} ', f'" [{color}]{status}[/{color}] ')
        console.print(highlighted)
    else:
        console.print(line)


def print_formatted_error_line(line: str):
    """Print a single error log line with colors."""
    # Detect error level
    line_lower = line.lower()

    if "error" in line_lower or "crit" in line_lower or "alert" in line_lower:
        console.print(f"[red]{line}[/red]")
    elif "warn" in line_lower:
        console.print(f"[yellow]{line}[/yellow]")
    elif "notice" in line_lower:
        console.print(f"[cyan]{line}[/cyan]")
    else:
        console.print(line)
