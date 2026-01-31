"""
Service Management - Control systemd services
"""

import questionary
from rich.console import Console
from rich.table import Table
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, confirm_action
)
from utils.shell import run_command

console = Console()

# Services to manage
SERVICES = [
    {"name": "🌐 Nginx", "service": "nginx"},
    {"name": "🐘 PHP-FPM 8.3", "service": "php8.3-fpm"},
    {"name": "🐘 PHP-FPM 8.2", "service": "php8.2-fpm"},
    {"name": "🔴 Redis", "service": "redis-server"},
    {"name": "🗄️  MySQL", "service": "mysql"},
    {"name": "🐘 PostgreSQL", "service": "postgresql"},
]

SERVICE_MENU_CHOICES = [
    {"name": "📋  Service Status", "value": "status"},
    {"name": "▶️   Start Service", "value": "start"},
    {"name": "⏹️   Stop Service", "value": "stop"},
    {"name": "🔄  Restart Service", "value": "restart"},
    {"name": "📜  View Logs", "value": "logs"},
    questionary.Separator("─" * 30),
    {"name": "⬅️   Back", "value": "back"},
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

        if choice == "status":
            show_service_status()
        elif choice in ["start", "stop", "restart"]:
            manage_service(choice)
        elif choice == "logs":
            view_logs()


def show_service_status():
    """Show status of all services."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Services", "Status"])

    table = Table(
        title="⚙️ Service Status",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Service", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Active", justify="center")

    for svc in SERVICES:
        code, stdout, _ = run_command(f"systemctl is-active {svc['service']}", check=False)

        if stdout == "active":
            status = "🟢 Running"
            active = "Yes"
        elif stdout == "inactive":
            status = "⚪ Stopped"
            active = "No"
        else:
            status = "❓ Unknown"
            active = "-"

        table.add_row(svc["name"], status, active)

    console.print(table)
    console.print()
    questionary.press_any_key_to_continue().ask()


def manage_service(action: str):
    """Start, stop, or restart a service."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Services", action.capitalize()])

    # Build choices with current status
    choices = []
    for svc in SERVICES:
        code, stdout, _ = run_command(f"systemctl is-active {svc['service']}", check=False)
        status = "🟢" if stdout == "active" else "⚪"
        choices.append({"name": f"{status} {svc['name']}", "value": svc["service"]})

    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    service = questionary.select(
        f"Select service to {action}:",
        choices=choices,
    ).ask()

    if not service:
        return

    if action == "stop" and not confirm_action(f"Are you sure you want to stop {service}?"):
        return

    console.print(f"\n[cyan]{action.capitalize()}ing {service}...[/cyan]")

    code, stdout, stderr = run_command(f"sudo systemctl {action} {service}", check=False)

    if code == 0:
        print_success(f"{service} {action}ed successfully!")
    else:
        print_error(f"Failed to {action} {service}: {stderr}")

    questionary.press_any_key_to_continue().ask()


def view_logs():
    """View recent logs for a service."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Services", "Logs"])

    choices = [{"name": svc["name"], "value": svc["service"]} for svc in SERVICES]
    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    service = questionary.select(
        "Select service to view logs:",
        choices=choices,
    ).ask()

    if not service:
        return

    lines = questionary.text(
        "Number of lines to show:",
        default="50",
        validate=lambda x: x.isdigit(),
    ).ask()

    console.print(f"\n[cyan]Last {lines} log entries for {service}:[/cyan]\n")

    code, stdout, stderr = run_command(
        f"sudo journalctl -u {service} -n {lines} --no-pager",
        check=False
    )

    if code == 0:
        console.print(stdout)
    else:
        print_error(f"Failed to get logs: {stderr}")

    console.print()
    questionary.press_any_key_to_continue().ask()
