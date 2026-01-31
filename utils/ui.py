"""
UI Utilities - Shared display functions
"""

import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

LOGO = """
███████╗ ██████╗ ██████╗  ██████╗ ███████╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
█████╗  ██║   ██║██████╔╝██║  ███╗█████╗
██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
"""


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    """Print the Forge header/logo."""
    console.print(Text(LOGO, style="bold cyan"))
    console.print(
        "[dim]Server Management CLI • v1.0.0[/dim]",
        justify="center",
    )
    console.print()


def print_breadcrumb(path: list[str]):
    """Print navigation breadcrumb."""
    crumbs = " › ".join(f"[cyan]{p}[/cyan]" for p in path)
    console.print(f"📍 {crumbs}")
    console.print()


def print_success(message: str):
    """Print a success message."""
    console.print(f"[green]✓ {message}[/green]")


def print_error(message: str):
    """Print an error message."""
    console.print(f"[red]✗ {message}[/red]")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[yellow]⚠ {message}[/yellow]")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[blue]ℹ {message}[/blue]")


def confirm_action(message: str, default: bool = False) -> bool:
    """Confirm a potentially destructive action."""
    import questionary
    return questionary.confirm(message, default=default).ask() or False
