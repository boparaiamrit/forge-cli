"""
Service Management - Comprehensive systemd service dashboard
"""

import re
import questionary
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, print_warning, print_info, confirm_action
)
from utils.shell import run_command, get_command_output

console = Console()


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE DEFINITIONS - Comprehensive list of server services
# ═══════════════════════════════════════════════════════════════════════════════

SERVICE_CATEGORIES = {
    "web": {
        "name": "🌐 Web Servers",
        "services": [
            {"name": "Nginx", "service": "nginx", "critical": True},
            {"name": "Apache2", "service": "apache2", "critical": True},
            {"name": "Caddy", "service": "caddy", "critical": True},
        ]
    },
    "php": {
        "name": "🐘 PHP-FPM",
        "services": [
            {"name": "PHP 8.5-FPM", "service": "php8.5-fpm", "critical": True},
            {"name": "PHP 8.4-FPM", "service": "php8.4-fpm", "critical": True},
            {"name": "PHP 8.3-FPM", "service": "php8.3-fpm", "critical": True},
            {"name": "PHP 8.2-FPM", "service": "php8.2-fpm", "critical": True},
            {"name": "PHP 8.1-FPM", "service": "php8.1-fpm", "critical": True},
            {"name": "PHP 8.0-FPM", "service": "php8.0-fpm", "critical": False},
            {"name": "PHP 7.4-FPM", "service": "php7.4-fpm", "critical": False},
        ]
    },
    "database": {
        "name": "🗄️ Databases",
        "services": [
            {"name": "MySQL", "service": "mysql", "critical": True},
            {"name": "MariaDB", "service": "mariadb", "critical": True},
            {"name": "PostgreSQL", "service": "postgresql", "critical": True},
            {"name": "MongoDB", "service": "mongod", "critical": False},
        ]
    },
    "cache": {
        "name": "⚡ Caching",
        "services": [
            {"name": "Redis", "service": "redis-server", "critical": True},
            {"name": "Memcached", "service": "memcached", "critical": False},
        ]
    },
    "queue": {
        "name": "📨 Queue & Workers",
        "services": [
            {"name": "Supervisor", "service": "supervisor", "critical": False},
            {"name": "RabbitMQ", "service": "rabbitmq-server", "critical": False},
            {"name": "Beanstalkd", "service": "beanstalkd", "critical": False},
        ]
    },
    "mail": {
        "name": "📧 Mail",
        "services": [
            {"name": "Postfix", "service": "postfix", "critical": False},
            {"name": "Dovecot", "service": "dovecot", "critical": False},
        ]
    },
    "monitoring": {
        "name": "📊 Monitoring",
        "services": [
            {"name": "Prometheus", "service": "prometheus", "critical": False},
            {"name": "Grafana", "service": "grafana-server", "critical": False},
            {"name": "Node Exporter", "service": "node_exporter", "critical": False},
        ]
    },
    "security": {
        "name": "🔒 Security",
        "services": [
            {"name": "UFW (Firewall)", "service": "ufw", "critical": True},
            {"name": "Fail2ban", "service": "fail2ban", "critical": True},
            {"name": "ClamAV", "service": "clamav-daemon", "critical": False},
            {"name": "Freshclam", "service": "clamav-freshclam", "critical": False},
        ]
    },
    "ssl": {
        "name": "🔐 SSL/TLS",
        "services": [
            {"name": "Certbot Timer", "service": "certbot.timer", "critical": False},
        ]
    },
    "system": {
        "name": "💻 System",
        "services": [
            {"name": "Cron", "service": "cron", "critical": True},
            {"name": "SSH", "service": "ssh", "critical": True},
            {"name": "Rsyslog", "service": "rsyslog", "critical": False},
            {"name": "NTP", "service": "ntp", "critical": False},
            {"name": "Systemd Timesyncd", "service": "systemd-timesyncd", "critical": False},
        ]
    },
    "docker": {
        "name": "🐳 Containers",
        "services": [
            {"name": "Docker", "service": "docker", "critical": False},
            {"name": "Containerd", "service": "containerd", "critical": False},
        ]
    },
}


SERVICE_MENU_CHOICES = [
    {"name": "📊 Service Dashboard", "value": "dashboard"},
    {"name": "📋 All Services Status", "value": "status"},
    questionary.Separator("─" * 30),
    {"name": "▶️ Start Service", "value": "start"},
    {"name": "⏹️ Stop Service", "value": "stop"},
    {"name": "🔄 Restart Service", "value": "restart"},
    {"name": "↻ Reload Service", "value": "reload"},
    questionary.Separator("─" * 30),
    {"name": "🔧 Enable on Boot", "value": "enable"},
    {"name": "❌ Disable on Boot", "value": "disable"},
    questionary.Separator("─" * 30),
    {"name": "📜 View Service Logs", "value": "logs"},
    {"name": "ℹ️ Service Details", "value": "details"},
    {"name": "🔍 Find Services", "value": "find"},
    questionary.Separator("─" * 30),
    {"name": "⬅️ Back", "value": "back"},
]


def run_services_menu():
    """Display the services management menu."""
    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "Services"])

        choice = questionary.select(
            "Service Management:",
            choices=SERVICE_MENU_CHOICES,
            qmark="⚙️",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "dashboard":
            show_service_dashboard()
        elif choice == "status":
            show_all_services_status()
        elif choice in ["start", "stop", "restart", "reload"]:
            manage_service(choice)
        elif choice == "enable":
            enable_disable_service(enable=True)
        elif choice == "disable":
            enable_disable_service(enable=False)
        elif choice == "logs":
            view_service_logs()
        elif choice == "details":
            show_service_details()
        elif choice == "find":
            find_services()


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def show_service_dashboard():
    """Show a comprehensive service dashboard."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Services", "Dashboard"])

    console.print("\n[bold]📊 Service Dashboard[/bold]\n")

    # Get all installed services with status
    installed = get_installed_services()

    # Calculate stats
    total = len(installed)
    running = sum(1 for s in installed if s["status"] == "active")
    stopped = sum(1 for s in installed if s["status"] == "inactive")
    failed = sum(1 for s in installed if s["status"] == "failed")
    critical_down = sum(1 for s in installed if s["status"] != "active" and s.get("critical"))

    # Summary panel
    summary = f"""[bold]Services Overview[/bold]

[green]● Running:[/green] {running}
[dim]○ Stopped:[/dim] {stopped}
[red]✗ Failed:[/red] {failed}
[bold]Total:[/bold] {total}
"""

    if critical_down > 0:
        summary += f"\n[red bold]⚠️ {critical_down} critical service(s) not running![/red bold]"

    console.print(Panel(summary, border_style="cyan"))

    # Services by category
    for cat_key, category in SERVICE_CATEGORIES.items():
        cat_services = [s for s in installed if s["category"] == cat_key]

        if not cat_services:
            continue

        console.print(f"\n[bold cyan]{category['name']}[/bold cyan]")

        for svc in cat_services:
            status = svc["status"]
            if status == "active":
                icon = "[green]●[/green]"
            elif status == "inactive":
                icon = "[dim]○[/dim]"
            elif status == "failed":
                icon = "[red]✗[/red]"
            else:
                icon = "[yellow]?[/yellow]"

            enabled = "[dim](enabled)[/dim]" if svc.get("enabled") else "[dim](disabled)[/dim]"
            critical = "[red]*[/red]" if svc.get("critical") else ""

            console.print(f"  {icon} {svc['name']}{critical} {enabled}")

    console.print()
    console.print("[dim]* = critical service[/dim]")
    console.print()

    # Quick actions
    action = questionary.select(
        "Quick Actions:",
        choices=[
            {"name": "🔄 Restart All PHP-FPM", "value": "restart_php"},
            {"name": "🌐 Restart Web Server", "value": "restart_web"},
            {"name": "🗄️ Restart Databases", "value": "restart_db"},
            {"name": "↻ Reload All Services", "value": "reload_all"},
            {"name": "⬅️ Back", "value": "back"},
        ],
    ).ask()

    if action == "restart_php":
        restart_services_by_category("php")
    elif action == "restart_web":
        restart_services_by_category("web")
    elif action == "restart_db":
        restart_services_by_category("database")
    elif action == "reload_all":
        reload_all_services()


def get_installed_services() -> List[Dict]:
    """Get list of installed services with their status."""
    installed = []

    for cat_key, category in SERVICE_CATEGORIES.items():
        for svc in category["services"]:
            # Check if service exists
            code, _, _ = run_command(
                f"systemctl list-unit-files {svc['service']}.service 2>/dev/null | grep -q {svc['service']}",
                check=False
            )

            # Also check timer units
            is_timer = svc["service"].endswith(".timer")
            if is_timer:
                code, _, _ = run_command(
                    f"systemctl list-unit-files {svc['service']} 2>/dev/null | grep -q {svc['service']}",
                    check=False
                )

            if code == 0:
                # Get status
                status = get_service_status(svc["service"])
                enabled = is_service_enabled(svc["service"])

                installed.append({
                    "name": svc["name"],
                    "service": svc["service"],
                    "category": cat_key,
                    "status": status,
                    "enabled": enabled,
                    "critical": svc.get("critical", False),
                })

    return installed


def get_service_status(service: str) -> str:
    """Get service status."""
    code, stdout, _ = run_command(f"systemctl is-active {service}", check=False)
    return stdout.strip() if code == 0 else "unknown"


def is_service_enabled(service: str) -> bool:
    """Check if service is enabled on boot."""
    code, stdout, _ = run_command(f"systemctl is-enabled {service}", check=False)
    return stdout.strip() == "enabled"


# ═══════════════════════════════════════════════════════════════════════════════
# ALL SERVICES STATUS
# ═══════════════════════════════════════════════════════════════════════════════

def show_all_services_status():
    """Show status of all services in a detailed table."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Services", "All Status"])

    console.print("\n[bold]📋 All Services Status[/bold]\n")

    installed = get_installed_services()

    if not installed:
        print_warning("No known services detected.")
        questionary.press_any_key_to_continue().ask()
        return

    table = Table(
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Service", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("State")
    table.add_column("Boot", justify="center")
    table.add_column("Memory", justify="right")
    table.add_column("Uptime", style="dim")

    for svc in installed:
        # Status icon
        status = svc["status"]
        if status == "active":
            status_icon = "[green]● Running[/green]"
        elif status == "inactive":
            status_icon = "[dim]○ Stopped[/dim]"
        elif status == "failed":
            status_icon = "[red]✗ Failed[/red]"
        else:
            status_icon = "[yellow]? Unknown[/yellow]"

        # Enabled on boot
        enabled = "[green]✓[/green]" if svc["enabled"] else "[dim]✗[/dim]"

        # Get memory usage and uptime
        memory = get_service_memory(svc["service"])
        uptime = get_service_uptime(svc["service"]) if status == "active" else "-"

        # State details
        code, state, _ = run_command(f"systemctl show {svc['service']} --property=SubState --value", check=False)
        state = state.strip() if code == 0 else "-"

        table.add_row(
            svc["name"],
            status_icon,
            state,
            enabled,
            memory,
            uptime,
        )

    console.print(table)
    console.print()
    questionary.press_any_key_to_continue().ask()


def get_service_memory(service: str) -> str:
    """Get memory usage of a service."""
    code, stdout, _ = run_command(
        f"systemctl show {service} --property=MemoryCurrent --value",
        check=False
    )

    if code != 0 or not stdout.strip() or stdout.strip() == "[not set]":
        return "-"

    try:
        bytes_val = int(stdout.strip())
        if bytes_val > 1024 * 1024 * 1024:
            return f"{bytes_val / (1024*1024*1024):.1f} GB"
        elif bytes_val > 1024 * 1024:
            return f"{bytes_val / (1024*1024):.1f} MB"
        elif bytes_val > 1024:
            return f"{bytes_val / 1024:.1f} KB"
        else:
            return f"{bytes_val} B"
    except ValueError:
        return "-"


def get_service_uptime(service: str) -> str:
    """Get uptime of a service."""
    code, stdout, _ = run_command(
        f"systemctl show {service} --property=ActiveEnterTimestamp --value",
        check=False
    )

    if code != 0 or not stdout.strip():
        return "-"

    try:
        # Parse timestamp
        from datetime import datetime
        timestamp_str = stdout.strip()
        # Format: "Wed 2024-01-31 10:30:45 UTC"
        parts = timestamp_str.split()
        if len(parts) >= 3:
            date_str = f"{parts[1]} {parts[2]}"
            start_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            delta = now - start_time

            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60

            if days > 0:
                return f"{days}d {hours}h"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
    except Exception:
        pass

    return "-"


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def manage_service(action: str):
    """Start, stop, restart, or reload a service."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Services", action.capitalize()])

    console.print(f"\n[bold]🔄 {action.capitalize()} Service[/bold]\n")

    installed = get_installed_services()

    if not installed:
        print_warning("No known services detected.")
        questionary.press_any_key_to_continue().ask()
        return

    # Build choices with current status
    choices = []
    for svc in installed:
        status = svc["status"]
        if status == "active":
            icon = "[green]●[/green]"
        elif status == "inactive":
            icon = "[dim]○[/dim]"
        else:
            icon = "[red]✗[/red]"

        choices.append({
            "name": f"{icon} {svc['name']} ({svc['service']})",
            "value": svc,
        })

    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    selected = questionary.select(
        f"Select service to {action}:",
        choices=choices,
    ).ask()

    if not selected:
        return

    service = selected["service"]
    name = selected["name"]

    # Confirmation for stop
    if action == "stop":
        if selected.get("critical"):
            print_warning(f"{name} is a critical service!")
        if not confirm_action(f"Are you sure you want to stop {name}?"):
            return

    console.print(f"\n[cyan]{action.capitalize()}ing {name}...[/cyan]")

    code, stdout, stderr = run_command(f"sudo systemctl {action} {service}", check=False)

    if code == 0:
        print_success(f"{name} {action}ed successfully!")

        # Show new status
        new_status = get_service_status(service)
        console.print(f"[dim]New status: {new_status}[/dim]")
    else:
        print_error(f"Failed to {action} {name}: {stderr}")

    questionary.press_any_key_to_continue().ask()


def enable_disable_service(enable: bool):
    """Enable or disable a service on boot."""
    action = "enable" if enable else "disable"

    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Services", action.capitalize()])

    console.print(f"\n[bold]🔧 {action.capitalize()} Service on Boot[/bold]\n")

    installed = get_installed_services()

    if not installed:
        print_warning("No known services detected.")
        questionary.press_any_key_to_continue().ask()
        return

    # Filter based on current state
    if enable:
        services = [s for s in installed if not s["enabled"]]
        if not services:
            print_info("All services are already enabled.")
            questionary.press_any_key_to_continue().ask()
            return
    else:
        services = [s for s in installed if s["enabled"]]
        if not services:
            print_info("All services are already disabled.")
            questionary.press_any_key_to_continue().ask()
            return

    choices = []
    for svc in services:
        status = "[green]●[/green]" if svc["status"] == "active" else "[dim]○[/dim]"
        choices.append({
            "name": f"{status} {svc['name']} ({svc['service']})",
            "value": svc,
        })

    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    selected = questionary.select(
        f"Select service to {action} on boot:",
        choices=choices,
    ).ask()

    if not selected:
        return

    service = selected["service"]
    name = selected["name"]

    console.print(f"\n[cyan]{action.capitalize()}ing {name} on boot...[/cyan]")

    code, _, stderr = run_command(f"sudo systemctl {action} {service}", check=False)

    if code == 0:
        print_success(f"{name} {action}d on boot!")
    else:
        print_error(f"Failed to {action} {name}: {stderr}")

    questionary.press_any_key_to_continue().ask()


def restart_services_by_category(category: str):
    """Restart all services in a category."""
    installed = get_installed_services()
    cat_services = [s for s in installed if s["category"] == category and s["status"] == "active"]

    if not cat_services:
        print_warning(f"No running services in {category} category.")
        questionary.press_any_key_to_continue().ask()
        return

    console.print(f"\n[cyan]Restarting {len(cat_services)} services...[/cyan]\n")

    for svc in cat_services:
        console.print(f"  Restarting {svc['name']}...", end=" ")
        code, _, _ = run_command(f"sudo systemctl restart {svc['service']}", check=False)
        if code == 0:
            console.print("[green]✓[/green]")
        else:
            console.print("[red]✗[/red]")

    print_success("Done!")
    questionary.press_any_key_to_continue().ask()


def reload_all_services():
    """Reload all running services that support reload."""
    installed = get_installed_services()
    running = [s for s in installed if s["status"] == "active"]

    if not running:
        print_warning("No running services to reload.")
        questionary.press_any_key_to_continue().ask()
        return

    console.print(f"\n[cyan]Reloading {len(running)} services...[/cyan]\n")

    for svc in running:
        console.print(f"  Reloading {svc['name']}...", end=" ")
        # Try reload first, fall back to restart
        code, _, _ = run_command(f"sudo systemctl reload {svc['service']}", check=False)
        if code == 0:
            console.print("[green]✓ (reload)[/green]")
        else:
            # Fallback to restart
            code, _, _ = run_command(f"sudo systemctl restart {svc['service']}", check=False)
            if code == 0:
                console.print("[yellow]✓ (restart)[/yellow]")
            else:
                console.print("[red]✗[/red]")

    print_success("Done!")
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# LOGS AND DETAILS
# ═══════════════════════════════════════════════════════════════════════════════

def view_service_logs():
    """View recent logs for a service."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Services", "Logs"])

    console.print("\n[bold]📜 Service Logs[/bold]\n")

    installed = get_installed_services()

    choices = []
    for svc in installed:
        status = "[green]●[/green]" if svc["status"] == "active" else "[dim]○[/dim]"
        choices.append({
            "name": f"{status} {svc['name']}",
            "value": svc["service"],
        })

    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    service = questionary.select(
        "Select service to view logs:",
        choices=choices,
    ).ask()

    if not service:
        return

    # Options
    log_type = questionary.select(
        "Log view type:",
        choices=[
            {"name": "📋 Last 50 lines", "value": "50"},
            {"name": "📋 Last 100 lines", "value": "100"},
            {"name": "📋 Last 500 lines", "value": "500"},
            {"name": "🔴 Live tail (follow)", "value": "follow"},
            {"name": "📅 Since last hour", "value": "hour"},
            {"name": "📅 Since today", "value": "today"},
        ],
    ).ask()

    if not log_type:
        return

    if log_type == "follow":
        console.print(f"\n[cyan]Following logs for {service}... (Ctrl+C to stop)[/cyan]\n")
        try:
            import subprocess
            subprocess.run(["sudo", "journalctl", "-u", service, "-f", "--no-pager"])
        except KeyboardInterrupt:
            pass
    elif log_type == "hour":
        console.print(f"\n[cyan]Logs for {service} since 1 hour ago:[/cyan]\n")
        code, stdout, _ = run_command(
            f"sudo journalctl -u {service} --since '1 hour ago' --no-pager",
            check=False
        )
        console.print(stdout if code == 0 else "Failed to get logs")
        questionary.press_any_key_to_continue().ask()
    elif log_type == "today":
        console.print(f"\n[cyan]Logs for {service} since today:[/cyan]\n")
        code, stdout, _ = run_command(
            f"sudo journalctl -u {service} --since today --no-pager",
            check=False
        )
        console.print(stdout if code == 0 else "Failed to get logs")
        questionary.press_any_key_to_continue().ask()
    else:
        console.print(f"\n[cyan]Last {log_type} log entries for {service}:[/cyan]\n")
        code, stdout, _ = run_command(
            f"sudo journalctl -u {service} -n {log_type} --no-pager",
            check=False
        )
        console.print(stdout if code == 0 else "Failed to get logs")
        questionary.press_any_key_to_continue().ask()


def show_service_details():
    """Show detailed information about a service."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Services", "Details"])

    console.print("\n[bold]ℹ️ Service Details[/bold]\n")

    installed = get_installed_services()

    choices = []
    for svc in installed:
        status = "[green]●[/green]" if svc["status"] == "active" else "[dim]○[/dim]"
        choices.append({
            "name": f"{status} {svc['name']}",
            "value": svc["service"],
        })

    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    service = questionary.select(
        "Select service:",
        choices=choices,
    ).ask()

    if not service:
        return

    # Get full status
    code, stdout, _ = run_command(f"sudo systemctl status {service}", check=False)

    console.print(Panel(stdout, title=f"Status: {service}", border_style="cyan"))

    # Get properties
    props = [
        "Description", "LoadState", "ActiveState", "SubState",
        "MainPID", "ExecMainStartTimestamp", "MemoryCurrent",
        "TasksCurrent", "Restart", "RestartUSec",
    ]

    console.print("\n[bold cyan]Properties:[/bold cyan]")

    for prop in props:
        code, value, _ = run_command(
            f"systemctl show {service} --property={prop} --value",
            check=False
        )
        if code == 0 and value.strip():
            console.print(f"  {prop}: [dim]{value.strip()}[/dim]")

    console.print()
    questionary.press_any_key_to_continue().ask()


def find_services():
    """Find and discover installed services."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Services", "Find"])

    console.print("\n[bold]🔍 Find Services[/bold]\n")

    search = questionary.text(
        "Search term (or leave empty for all):",
    ).ask()

    if search is None:
        return

    console.print(f"\n[cyan]Searching for services...[/cyan]\n")

    if search:
        cmd = f"systemctl list-units --type=service --all | grep -i {search}"
    else:
        cmd = "systemctl list-units --type=service --state=running"

    code, stdout, _ = run_command(cmd, check=False)

    if code == 0 and stdout:
        # Parse and display
        lines = stdout.strip().split("\n")

        table = Table(box=box.SIMPLE)
        table.add_column("Unit", style="cyan")
        table.add_column("Load")
        table.add_column("Active")
        table.add_column("Sub")
        table.add_column("Description")

        for line in lines[:30]:  # Limit to 30 results
            parts = line.split(None, 4)
            if len(parts) >= 5:
                unit = parts[0]
                load = parts[1]
                active = "[green]active[/green]" if parts[2] == "active" else parts[2]
                sub = parts[3]
                desc = parts[4][:50]
                table.add_row(unit, load, active, sub, desc)

        console.print(table)

        if len(lines) > 30:
            console.print(f"\n[dim]Showing 30 of {len(lines)} results[/dim]")
    else:
        print_info("No services found matching your search.")

    console.print()
    questionary.press_any_key_to_continue().ask()
