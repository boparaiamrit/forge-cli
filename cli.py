"""
Forge CLI - Main Application Entry Point

This module contains the main menu system and navigation logic.
"""

import sys
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from utils.ui import clear_screen, print_header, print_breadcrumb
from detectors import get_system_status
from installers import run_installer_menu
from sites import run_sites_menu
from sslcerts import run_ssl_menu
from services import run_services_menu
from logs import run_logs_menu
from monitor import run_monitor_menu
from diagnostics import run_diagnostics_menu
from php import run_php_menu
from cron import run_cron_menu
from security import run_security_menu
from auditor import run_auditor_menu
from cve import run_cve_menu
from disk import run_disk_menu
from alerts import run_alerts_menu
from state import get_recent_changes, export_lineage_report

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════

MAIN_MENU_CHOICES = [
    {"name": "📊  System Status", "value": "status"},
    {"name": "📦  Install Packages", "value": "install"},
    {"name": "🐘  PHP Management", "value": "php"},
    questionary.Separator("─" * 30),
    {"name": "🌐  Manage Sites", "value": "sites"},
    {"name": "🔒  SSL Certificates", "value": "ssl"},
    {"name": "⚙️   Services", "value": "services"},
    {"name": "⏰  Cron Jobs", "value": "cron"},
    questionary.Separator("─" * 30),
    {"name": "📜  Logs", "value": "logs"},
    {"name": "📈  Monitor", "value": "monitor"},
    {"name": "🔧  Diagnostics", "value": "diagnostics"},
    {"name": "🛡️   Security & Antivirus", "value": "security"},
    {"name": "🔍  Configuration Auditor", "value": "auditor"},
    {"name": "🛡️   CVE Scanner", "value": "cve"},
    questionary.Separator("─" * 30),
    {"name": "💾  Disk Management", "value": "disk"},
    {"name": "📊  Monitoring & Alerts", "value": "alerts"},
    questionary.Separator("─" * 30),
    {"name": "📋  State History", "value": "history"},
    {"name": "❌  Exit", "value": "exit"},
]


def show_main_menu():
    """Display the main menu and handle selection."""
    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main"])

        choice = questionary.select(
            "What would you like to do?",
            choices=MAIN_MENU_CHOICES,
            style=get_questionary_style(),
            qmark="🔧",
            pointer="▶",
        ).ask()

        if choice is None or choice == "exit":
            console.print("\n[dim]👋 Goodbye![/dim]\n")
            sys.exit(0)

        handle_main_menu_choice(choice)


def handle_main_menu_choice(choice: str):
    """Route to the appropriate sub-menu based on selection."""
    if choice == "status":
        show_system_status()
    elif choice == "install":
        run_installer_menu()
    elif choice == "php":
        run_php_menu()
    elif choice == "sites":
        run_sites_menu()
    elif choice == "ssl":
        run_ssl_menu()
    elif choice == "services":
        run_services_menu()
    elif choice == "cron":
        run_cron_menu()
    elif choice == "logs":
        run_logs_menu()
    elif choice == "monitor":
        run_monitor_menu()
    elif choice == "diagnostics":
        run_diagnostics_menu()
    elif choice == "security":
        run_security_menu()
    elif choice == "auditor":
        run_auditor_menu()
    elif choice == "cve":
        run_cve_menu()
    elif choice == "disk":
        run_disk_menu()
    elif choice == "alerts":
        run_alerts_menu()
    elif choice == "history":
        show_state_history()



def show_system_status():
    """Display detailed system status."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "System Status"])

    console.print()

    with console.status("[bold cyan]Scanning system...", spinner="dots"):
        status = get_system_status()

    # Create status table
    table = Table(
        title="🖥️  Server Software Status",
        box=box.ROUNDED,
        header_style="bold magenta",
        border_style="dim",
        title_style="bold white",
        padding=(0, 2),
    )

    table.add_column("Software", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Version", style="dim")
    table.add_column("Details", style="dim italic")

    for item in status:
        icon = "🟢" if item["installed"] else "🔴"
        status_text = f"{icon} Installed" if item["installed"] else f"{icon} Not Found"
        table.add_row(
            item["name"],
            status_text,
            item.get("version", "-"),
            item.get("details", ""),
        )

    console.print(table)
    console.print()

    # Quick stats
    installed_count = sum(1 for i in status if i["installed"])
    console.print(f"[dim]Installed: {installed_count}/{len(status)} packages[/dim]")
    console.print()

    questionary.press_any_key_to_continue(
        message="Press any key to return to main menu..."
    ).ask()


def show_state_history():
    """Display state change history."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "State History"])

    console.print("\n[bold]📋 State Change History[/bold]\n")

    # Get recent changes
    changes = get_recent_changes(30)

    if not changes:
        console.print("[dim]No state changes recorded yet.[/dim]")
    else:
        table = Table(
            box=box.ROUNDED,
            header_style="bold magenta",
        )
        table.add_column("Timestamp", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Entity", style="green")
        table.add_column("Action")

        for change in reversed(changes):
            timestamp = change.get("timestamp", "")[:19]
            entity_type = change.get("entity_type", "?")
            entity_id = change.get("entity_id", "?")
            action = change.get("action", "?")

            # Color code actions
            if action == "create" or action == "install":
                action_str = f"[green]+ {action}[/green]"
            elif action == "delete":
                action_str = f"[red]- {action}[/red]"
            elif action == "update" or action == "ssl_update":
                action_str = f"[yellow]~ {action}[/yellow]"
            else:
                action_str = action

            table.add_row(timestamp, entity_type, entity_id, action_str)

        console.print(table)

    # Options
    console.print()
    action = questionary.select(
        "Options:",
        choices=[
            {"name": "📄 Export Full Report", "value": "export"},
            {"name": "⬅️  Back", "value": "back"},
        ],
    ).ask()

    if action == "export":
        report = export_lineage_report()
        console.print(Panel(report, title="Lineage Report", border_style="cyan"))
        questionary.press_any_key_to_continue().ask()


def get_questionary_style():
    """Return custom questionary style."""
    from questionary import Style
    return Style([
        ("qmark", "fg:cyan bold"),
        ("question", "fg:white bold"),
        ("answer", "fg:green bold"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
        ("separator", "fg:ansigray"),
        ("instruction", "fg:ansigray"),
    ])


def main():
    """Main entry point for Forge CLI."""
    try:
        show_main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[dim]👋 Interrupted. Goodbye![/dim]\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
