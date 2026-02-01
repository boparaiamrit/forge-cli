"""
Diagnostics - Error troubleshooting and system checks
"""

import os
import questionary
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, print_warning, print_info
)
from utils.shell import run_command, get_command_output, command_exists

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# DIAGNOSTICS MENU
# ═══════════════════════════════════════════════════════════════════════════════

DIAGNOSTICS_MENU_CHOICES = [
    {"name": "🔍  Nginx Config Test", "value": "nginx_test"},
    {"name": "🐘  PHP-FPM Check", "value": "php_check"},
    {"name": "📁  Permission Check", "value": "permissions"},
    {"name": "🔌  Port Conflicts", "value": "ports"},
    {"name": "🚨  Common Errors", "value": "errors"},
    {"name": "🔧  Auto-Fix Issues", "value": "autofix"},
    questionary.Separator("─" * 30),
    {"name": "⬅️   Back", "value": "back"},
]


def run_diagnostics_menu():
    """Display the diagnostics menu."""
    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "Diagnostics"])

        choice = questionary.select(
            "Diagnostics & Troubleshooting:",
            choices=DIAGNOSTICS_MENU_CHOICES,
            qmark="🔧",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "nginx_test":
            test_nginx_config()
        elif choice == "php_check":
            check_php_fpm()
        elif choice == "permissions":
            check_permissions()
        elif choice == "ports":
            check_port_conflicts()
        elif choice == "errors":
            diagnose_common_errors()
        elif choice == "autofix":
            auto_fix_issues()


# ═══════════════════════════════════════════════════════════════════════════════
# NGINX DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════════

def test_nginx_config():
    """Test Nginx configuration and show detailed errors."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Diagnostics", "Nginx Test"])

    console.print("\n[bold]🔍 Testing Nginx Configuration[/bold]\n")

    code, stdout, stderr = run_command("sudo nginx -t", check=False)

    if code == 0:
        print_success("Nginx configuration is valid!")
        console.print(f"\n[dim]{stdout}[/dim]")
    else:
        print_error("Nginx configuration has errors:")
        console.print()

        # Parse and format the error
        error_text = stderr or stdout
        for line in error_text.split("\n"):
            if "error" in line.lower():
                console.print(f"[red]{line}[/red]")
            elif "warn" in line.lower():
                console.print(f"[yellow]{line}[/yellow]")
            else:
                console.print(f"[dim]{line}[/dim]")

        # Try to identify the problem
        console.print("\n[bold]💡 Suggested Fixes:[/bold]\n")

        if "unknown directive" in error_text:
            print_info("Check for typos in your Nginx configuration.")
        if "duplicate" in error_text.lower():
            print_info("Remove duplicate server_name or listen directives.")
        if "no such file" in error_text.lower():
            print_info("Check that all included files and SSL certificates exist.")
        if "permission denied" in error_text.lower():
            print_info("Check file permissions on configuration and SSL files.")

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# PHP-FPM DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════════

def check_php_fpm():
    """Check PHP-FPM status and configuration."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Diagnostics", "PHP-FPM"])

    console.print("\n[bold]🐘 PHP-FPM Diagnostics[/bold]\n")

    php_versions = ["8.3", "8.2", "8.1", "8.0", "7.4"]
    found_versions = []

    for version in php_versions:
        service = f"php{version}-fpm"
        socket = f"/var/run/php/php{version}-fpm.sock"

        code, stdout, _ = run_command(f"systemctl is-active {service}", check=False)
        status = stdout.strip()

        if status == "active":
            # Check socket
            socket_exists = os.path.exists(socket)
            socket_status = "🟢" if socket_exists else "🔴"

            console.print(f"[green]✓ PHP {version}[/green] - Running")
            console.print(f"  Socket: {socket_status} {socket}")

            if not socket_exists:
                print_warning(f"  Socket not found! PHP-FPM may not be configured correctly.")

            found_versions.append(version)
        elif status == "inactive":
            console.print(f"[dim]○ PHP {version}[/dim] - Stopped")
            found_versions.append(version)

    if not found_versions:
        print_warning("No PHP-FPM versions found installed.")

    # Check for common issues
    console.print("\n[bold]Common PHP-FPM Issues:[/bold]\n")

    # Check www-data permissions
    code, stdout, _ = run_command("id www-data", check=False)
    if code == 0:
        console.print(f"[green]✓[/green] www-data user exists: [dim]{stdout}[/dim]")
    else:
        print_error("www-data user not found!")

    # Check for running processes
    code, stdout, _ = run_command("pgrep -c php-fpm", check=False)
    if code == 0 and stdout.strip():
        console.print(f"[green]✓[/green] PHP-FPM processes running: {stdout.strip()}")
    else:
        print_warning("No PHP-FPM processes found running.")

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# PERMISSION DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════════

def check_permissions():
    """Check file and directory permissions."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Diagnostics", "Permissions"])

    console.print("\n[bold]📁 Permission Check[/bold]\n")

    path = questionary.text(
        "Enter path to check (e.g., /var/www/mysite):",
        default="/var/www",
    ).ask()

    if not path or not os.path.exists(path):
        print_error(f"Path does not exist: {path}")
        questionary.press_any_key_to_continue().ask()
        return

    console.print(f"\n[cyan]Checking: {path}[/cyan]\n")

    # Get ownership
    code, stdout, _ = run_command(f"stat -c '%U:%G' {path}", check=False)
    if code == 0:
        console.print(f"Owner: [green]{stdout.strip()}[/green]")

    # Get permissions
    code, stdout, _ = run_command(f"stat -c '%a' {path}", check=False)
    if code == 0:
        perms = stdout.strip()
        console.print(f"Permissions: [green]{perms}[/green]")

        # Check for issues
        if os.path.isdir(path):
            if perms not in ["755", "775", "750"]:
                print_warning(f"Unusual directory permissions. Recommended: 755 or 775")
        else:
            if perms not in ["644", "664", "640"]:
                print_warning(f"Unusual file permissions. Recommended: 644 or 664")

    # Check for common Laravel/PHP directories
    for subdir in ["storage", "bootstrap/cache"]:
        full_path = os.path.join(path, subdir)
        if os.path.exists(full_path):
            code, stdout, _ = run_command(f"stat -c '%a %U:%G' {full_path}", check=False)
            if code == 0:
                parts = stdout.strip().split()
                perms, owner = parts[0], parts[1]

                if perms not in ["775", "777"]:
                    print_warning(f"{subdir}: May need to be writable (775). Current: {perms}")
                else:
                    console.print(f"[green]✓[/green] {subdir}: {perms} {owner}")

    # Suggest fix command
    console.print("\n[bold]Fix Commands:[/bold]")
    console.print(f"[dim]sudo chown -R www-data:www-data {path}[/dim]")
    console.print(f"[dim]sudo find {path} -type d -exec chmod 755 {{}} \\;[/dim]")
    console.print(f"[dim]sudo find {path} -type f -exec chmod 644 {{}} \\;[/dim]")

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# PORT CONFLICTS
# ═══════════════════════════════════════════════════════════════════════════════

def check_port_conflicts():
    """Check for port conflicts."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Diagnostics", "Ports"])

    console.print("\n[bold]🔌 Port Conflict Check[/bold]\n")

    # Check common ports
    ports_to_check = [80, 443, 3000, 3306, 5432, 6379, 8080, 9000]

    table = Table(box=box.ROUNDED)
    table.add_column("Port", style="cyan", justify="right")
    table.add_column("Status")
    table.add_column("Process")

    for port in ports_to_check:
        # Check what's using the port
        code, stdout, _ = run_command(f"sudo lsof -i :{port} -sTCP:LISTEN -t", check=False)

        if stdout.strip():
            pids = stdout.strip().split()
            processes = []
            for pid in pids[:2]:  # Limit to first 2
                code, pname, _ = run_command(f"ps -p {pid} -o comm=", check=False)
                if code == 0 and pname.strip():
                    processes.append(pname.strip())

            process_str = ", ".join(processes) if processes else f"PIDs: {', '.join(pids)}"
            table.add_row(str(port), "🟢 In Use", process_str)
        else:
            table.add_row(str(port), "⚪ Free", "-")

    console.print(table)

    # Check for port conflicts
    console.print("\n[bold]Checking for conflicts...[/bold]\n")

    # Multiple things on port 80
    code, stdout, _ = run_command("sudo lsof -i :80 -sTCP:LISTEN | grep -v COMMAND | wc -l", check=False)
    if stdout.strip() and int(stdout.strip()) > 1:
        print_warning("Multiple processes listening on port 80!")

    # Apache vs Nginx
    code, _, _ = run_command("systemctl is-active apache2", check=False)
    if code == 0:
        code2, _, _ = run_command("systemctl is-active nginx", check=False)
        if code2 == 0:
            print_error("Both Apache and Nginx are running! This may cause port 80 conflicts.")
            print_info("Run: sudo systemctl stop apache2 && sudo systemctl disable apache2")

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# COMMON ERRORS
# ═══════════════════════════════════════════════════════════════════════════════

ERROR_GUIDES = {
    "419": {
        "name": "419 Page Expired (Laravel CSRF)",
        "causes": [
            "Session expired",
            "CSRF token mismatch",
            "Incorrect session driver configuration",
        ],
        "fixes": [
            "Check SESSION_DRIVER in .env (use 'file' or 'redis')",
            "Ensure storage/framework/sessions is writable",
            "Check APP_URL matches your actual domain",
            "Clear cache: php artisan config:clear",
        ],
    },
    "500": {
        "name": "500 Internal Server Error",
        "causes": [
            "PHP error/exception",
            "Missing dependencies",
            "Configuration error",
        ],
        "fixes": [
            "Check Laravel logs: storage/logs/laravel.log",
            "Check Nginx error log: /var/log/nginx/error.log",
            "Check PHP-FPM log: /var/log/php*-fpm.log",
            "Enable debug: APP_DEBUG=true (temporarily)",
        ],
    },
    "502": {
        "name": "502 Bad Gateway",
        "causes": [
            "PHP-FPM not running",
            "Socket not found",
            "App not started (Node.js)",
        ],
        "fixes": [
            "Restart PHP-FPM: sudo systemctl restart php8.3-fpm",
            "Check socket exists: ls /var/run/php/",
            "For Node.js: Check PM2 status or app port",
            "Check Nginx upstream configuration",
        ],
    },
    "504": {
        "name": "504 Gateway Timeout",
        "causes": [
            "Slow database queries",
            "Long-running PHP script",
            "Unresponsive upstream",
        ],
        "fixes": [
            "Increase proxy_read_timeout in Nginx",
            "Increase request_terminate_timeout in PHP-FPM",
            "Optimize database queries",
            "Check MySQL/PostgreSQL performance",
        ],
    },
    "403": {
        "name": "403 Forbidden",
        "causes": [
            "File permissions",
            "Directory listing disabled",
            "IP blocked",
        ],
        "fixes": [
            "Check document root permissions",
            "Ensure index file exists",
            "Check Nginx access rules",
        ],
    },
    "404": {
        "name": "404 Not Found",
        "causes": [
            "Wrong document root",
            "Missing try_files directive",
            "App not serving",
        ],
        "fixes": [
            "Check Nginx root path",
            "Add: try_files $uri $uri/ /index.php?$query_string",
            "Check application is running",
        ],
    },
}


def diagnose_common_errors():
    """Guide for diagnosing common HTTP errors."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Diagnostics", "Errors"])

    console.print("\n[bold]🚨 Common Error Troubleshooting[/bold]\n")

    choices = [{"name": f"{code} - {info['name']}", "value": code}
               for code, info in ERROR_GUIDES.items()]
    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Back", "value": None})

    error_code = questionary.select(
        "Select error to troubleshoot:",
        choices=choices,
    ).ask()

    if not error_code:
        return

    guide = ERROR_GUIDES[error_code]

    console.print(f"\n[bold red]{error_code} - {guide['name']}[/bold red]\n")

    console.print("[bold]Possible Causes:[/bold]")
    for cause in guide["causes"]:
        console.print(f"  • {cause}")

    console.print(f"\n[bold]How to Fix:[/bold]")
    for i, fix in enumerate(guide["fixes"], 1):
        console.print(f"  {i}. {fix}")

    # Show relevant logs
    console.print("\n[bold]Check Logs:[/bold]")
    console.print("[dim]  sudo tail -50 /var/log/nginx/error.log[/dim]")

    if error_code in ["500", "502"]:
        console.print("[dim]  sudo tail -50 /var/log/php*-fpm.log[/dim]")

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-FIX
# ═══════════════════════════════════════════════════════════════════════════════

def auto_fix_issues():
    """Attempt to automatically fix common issues."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Diagnostics", "Auto-Fix"])

    console.print("\n[bold]🔧 Auto-Fix Common Issues[/bold]\n")
    console.print("[dim]This will attempt to fix common configuration issues.[/dim]\n")

    fixes = [
        {"name": "Restart Nginx", "cmd": "sudo systemctl restart nginx", "check": "nginx"},
        {"name": "Restart PHP-FPM 8.3", "cmd": "sudo systemctl restart php8.3-fpm", "check": "php8.3-fpm"},
        {"name": "Fix /var/www permissions", "cmd": "sudo chown -R www-data:www-data /var/www", "dangerous": True},
        {"name": "Clear Nginx cache", "cmd": "sudo rm -rf /var/cache/nginx/*", "dangerous": True},
        {"name": "Test Nginx config", "cmd": "sudo nginx -t", "always_run": True},
    ]

    choices = [{"name": f["name"], "value": i} for i, f in enumerate(fixes)]
    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    selected = questionary.checkbox(
        "Select fixes to apply:",
        choices=choices,
    ).ask()

    if not selected:
        return

    console.print()
    for idx in selected:
        fix = fixes[idx]

        if fix.get("dangerous") and not questionary.confirm(
            f"Are you sure you want to run '{fix['name']}'?"
        ).ask():
            continue

        console.print(f"[cyan]Running: {fix['name']}...[/cyan]")
        code, stdout, stderr = run_command(fix["cmd"], check=False)

        if code == 0:
            print_success(f"{fix['name']} completed!")
        else:
            print_error(f"{fix['name']} failed: {stderr}")

    console.print()
    questionary.press_any_key_to_continue().ask()
