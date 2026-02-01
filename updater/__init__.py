"""
Forge CLI Updater - Self-update functionality
"""

import re
import questionary
from rich.console import Console
from rich.panel import Panel
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, print_warning, print_info, confirm_action
)
from utils.shell import run_command

console = Console()

# Current version - should match pyproject.toml
CURRENT_VERSION = "0.10.1"

# GitHub repository
GITHUB_REPO = "boparaiamrit/forge-cli"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"


def get_current_version() -> str:
    """Get the current installed version."""
    return CURRENT_VERSION


def get_latest_version() -> tuple:
    """
    Fetch the latest version from GitHub.
    Returns (version, changelog_url, error)
    """
    # Try to fetch pyproject.toml from GitHub
    code, stdout, _ = run_command(
        f"curl -s {GITHUB_RAW_URL}/pyproject.toml 2>/dev/null | grep '^version' | head -1",
        check=False
    )

    if code == 0 and stdout:
        # Parse version = "x.x.x"
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', stdout)
        if match:
            return (match.group(1), f"https://github.com/{GITHUB_REPO}/blob/main/CHANGELOG.md", None)

    # Fallback: try GitHub API for latest release
    code, stdout, _ = run_command(
        f"curl -s https://api.github.com/repos/{GITHUB_REPO}/releases/latest 2>/dev/null | grep '\"tag_name\"' | head -1",
        check=False
    )

    if code == 0 and stdout:
        match = re.search(r'"tag_name":\s*"v?([^"]+)"', stdout)
        if match:
            return (match.group(1), f"https://github.com/{GITHUB_REPO}/releases", None)

    return (None, None, "Could not fetch latest version from GitHub")


def compare_versions(current: str, latest: str) -> int:
    """
    Compare two version strings.
    Returns: -1 if current < latest, 0 if equal, 1 if current > latest
    """
    def parse_version(v):
        # Remove 'v' prefix if present
        v = v.lstrip('v')
        # Split by dots and convert to integers
        parts = []
        for part in v.split('.'):
            # Handle versions like "1.0.0-beta"
            num = re.match(r'(\d+)', part)
            if num:
                parts.append(int(num.group(1)))
            else:
                parts.append(0)
        return parts

    current_parts = parse_version(current)
    latest_parts = parse_version(latest)

    # Pad with zeros to make same length
    max_len = max(len(current_parts), len(latest_parts))
    current_parts.extend([0] * (max_len - len(current_parts)))
    latest_parts.extend([0] * (max_len - len(latest_parts)))

    for c, l in zip(current_parts, latest_parts):
        if c < l:
            return -1
        elif c > l:
            return 1
    return 0


def check_for_updates(silent: bool = False) -> tuple:
    """
    Check if updates are available.
    Returns (has_update, current_version, latest_version, error)
    """
    current = get_current_version()
    latest, changelog_url, error = get_latest_version()

    if error:
        if not silent:
            print_warning(f"Could not check for updates: {error}")
        return (False, current, None, error)

    if not latest:
        return (False, current, None, "Could not determine latest version")

    has_update = compare_versions(current, latest) < 0

    return (has_update, current, latest, None)


def show_update_status():
    """Show current version and check for updates."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Update"])

    console.print("\n[bold]🔄 Forge CLI Update[/bold]\n")

    current = get_current_version()
    console.print(f"[cyan]Current version:[/cyan] v{current}\n")

    console.print("[dim]Checking for updates...[/dim]")

    has_update, current, latest, error = check_for_updates()

    if error:
        print_warning(f"Could not check for updates: {error}")
        console.print("\n[dim]You can manually update with:[/dim]")
        console.print("[cyan]  pip install --upgrade forge-cli[/cyan]")
        console.print("[dim]or[/dim]")
        console.print(f"[cyan]  git pull (if installed from source)[/cyan]")
    elif has_update:
        console.print(Panel(
            f"[green]✨ New version available![/green]\n\n"
            f"Current: v{current}\n"
            f"Latest:  v{latest}\n\n"
            f"Run the update to get the latest features and bug fixes.",
            title="🆕 Update Available",
            border_style="green",
        ))

        if confirm_action("Would you like to update now?"):
            perform_update()
    else:
        console.print(Panel(
            f"[green]✓ You're running the latest version![/green]\n\n"
            f"Version: v{current}",
            title="✅ Up to Date",
            border_style="green",
        ))

    questionary.press_any_key_to_continue().ask()


def perform_update():
    """Perform the actual update."""
    console.print("\n[cyan]Starting update...[/cyan]\n")

    # Detect installation method
    # Check if we're in a git repository
    code, stdout, _ = run_command("git rev-parse --is-inside-work-tree 2>/dev/null", check=False)
    is_git_repo = code == 0 and stdout.strip() == "true"

    if is_git_repo:
        # Update via git
        console.print("[dim]Detected git installation, pulling latest changes...[/dim]\n")

        # Stash any local changes
        run_command("git stash", check=False)

        # Pull latest
        code, stdout, stderr = run_command("git pull origin main", check=False)

        if code == 0:
            print_success("Git pull successful!")

            # Reinstall package
            console.print("\n[dim]Reinstalling package...[/dim]")
            code, _, _ = run_command("pip install -e . --quiet", check=False)

            if code == 0:
                print_success("Package reinstalled successfully!")
            else:
                print_warning("Could not reinstall package. Run: pip install -e .")
        else:
            print_error(f"Git pull failed: {stderr}")
            console.print("\n[dim]Try manually running:[/dim]")
            console.print("[cyan]  git pull origin main[/cyan]")
    else:
        # Update via pip
        console.print("[dim]Attempting pip upgrade...[/dim]\n")

        code, stdout, stderr = run_command(
            "pip install --upgrade forge-cli",
            check=False
        )

        if code == 0:
            print_success("Update successful!")
        else:
            # Try with --user flag
            code, _, _ = run_command(
                "pip install --upgrade --user forge-cli",
                check=False
            )

            if code == 0:
                print_success("Update successful!")
            else:
                print_error("Update failed. Try manually:")
                console.print("[cyan]  pip install --upgrade forge-cli[/cyan]")

    # Show what's new
    console.print("\n[bold]What's New:[/bold]")
    console.print(f"[dim]See changelog: https://github.com/{GITHUB_REPO}/blob/main/CHANGELOG.md[/dim]")


def show_version():
    """Display version information."""
    current = get_current_version()
    console.print(f"[bold cyan]Forge CLI[/bold cyan] v{current}")


def run_updater_menu():
    """Run the updater menu."""
    show_update_status()


# Quick update check for startup (non-blocking)
def startup_update_check():
    """
    Quick update check to show in header.
    Returns update message or None.
    """
    try:
        has_update, current, latest, _ = check_for_updates(silent=True)
        if has_update:
            return f"[yellow]Update available: v{latest}[/yellow]"
    except:
        pass
    return None
