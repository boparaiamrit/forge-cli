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

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════

MAIN_MENU_CHOICES = [
    {"name": "📊  System Status", "value": "status"},
    {"name": "📦  Install Packages", "value": "install"},
    {"name": "🌐  Manage Sites", "value": "sites"},
    {"name": "🔒  SSL Certificates", "value": "ssl"},
    {"name": "⚙️   Services", "value": "services"},
    questionary.Separator("─" * 30),
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
    elif choice == "sites":
        run_sites_menu()
    elif choice == "ssl":
        run_ssl_menu()
    elif choice == "services":
        run_services_menu()


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
        border_style="bright_black",
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

    questionary.press_any_key_to_continue(
        message="Press any key to return to main menu..."
    ).ask()


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
