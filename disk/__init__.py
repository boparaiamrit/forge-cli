"""
Disk Management - Disk cleanup, log rotation, space analysis, and file management
"""

import os
import re
import json
import questionary
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, print_warning, print_info, confirm_action
)
from utils.shell import run_command, get_command_output
from state import record_lineage

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# DISK DATA PATHS
# ═══════════════════════════════════════════════════════════════════════════════

DISK_DATA_DIR = Path.home() / ".forge" / "disk"

# Directories that are safe to clean
CLEANABLE_DIRS = {
    "/tmp": {"name": "Temporary Files", "pattern": "*", "min_age_days": 7},
    "/var/tmp": {"name": "Var Temp Files", "pattern": "*", "min_age_days": 7},
    "/var/cache/apt/archives": {"name": "APT Cache", "pattern": "*.deb", "min_age_days": 0},
    "/var/log": {"name": "Old Log Files", "pattern": "*.gz", "min_age_days": 30},
    "/var/log": {"name": "Rotated Logs", "pattern": "*.1", "min_age_days": 7},
}

# Log directories to manage
LOG_DIRS = [
    "/var/log/nginx",
    "/var/log/php*-fpm.log*",
    "/var/log/mysql",
    "/var/log/postgresql",
    "/var/log/redis",
    "/var/log/syslog*",
    "/var/log/auth.log*",
]


# ═══════════════════════════════════════════════════════════════════════════════
# DISK MENU
# ═══════════════════════════════════════════════════════════════════════════════

DISK_MENU_CHOICES = [
    {"name": "📊 Disk Space Overview", "value": "overview"},
    {"name": "📁 Directory Size Analysis", "value": "analyze"},
    questionary.Separator("─" * 30),
    {"name": "🧹 Quick Cleanup", "value": "quick_cleanup"},
    {"name": "🗑️ Deep Cleanup", "value": "deep_cleanup"},
    {"name": "📦 Clean APT Cache", "value": "apt_cleanup"},
    {"name": "🐳 Clean Docker", "value": "docker_cleanup"},
    questionary.Separator("─" * 30),
    {"name": "📜 Log Rotation Status", "value": "log_rotation"},
    {"name": "🔄 Rotate Logs Now", "value": "rotate_now"},
    {"name": "📋 Large Log Files", "value": "large_logs"},
    questionary.Separator("─" * 30),
    {"name": "🔍 Find Large Files", "value": "find_large"},
    {"name": "📅 Find Old Files", "value": "find_old"},
    {"name": "📂 Duplicate Files", "value": "duplicates"},
    questionary.Separator("─" * 30),
    {"name": "💾 Swap Management", "value": "swap"},
    {"name": "⏰ Setup Cleanup Cron", "value": "setup_cron"},
    questionary.Separator("─" * 30),
    {"name": "⬅️ Back", "value": "back"},
]


def run_disk_menu():
    """Display the disk management menu."""
    DISK_DATA_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "Disk Management"])

        choice = questionary.select(
            "Disk Management:",
            choices=DISK_MENU_CHOICES,
            qmark="💾",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "overview":
            show_disk_overview()
        elif choice == "analyze":
            analyze_directory_sizes()
        elif choice == "quick_cleanup":
            quick_cleanup()
        elif choice == "deep_cleanup":
            deep_cleanup()
        elif choice == "apt_cleanup":
            clean_apt_cache()
        elif choice == "docker_cleanup":
            clean_docker()
        elif choice == "log_rotation":
            show_log_rotation_status()
        elif choice == "rotate_now":
            rotate_logs_now()
        elif choice == "large_logs":
            find_large_log_files()
        elif choice == "find_large":
            find_large_files()
        elif choice == "find_old":
            find_old_files()
        elif choice == "duplicates":
            find_duplicate_files()
        elif choice == "swap":
            manage_swap()
        elif choice == "setup_cron":
            setup_cleanup_cron()


# ═══════════════════════════════════════════════════════════════════════════════
# DISK OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

def show_disk_overview():
    """Show comprehensive disk space overview."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Overview"])

    console.print("\n[bold]📊 Disk Space Overview[/bold]\n")

    # Get disk usage
    code, stdout, _ = run_command("df -h --type=ext4 --type=xfs --type=btrfs 2>/dev/null || df -h", check=False)

    if code == 0 and stdout:
        table = Table(title="💾 Filesystem Usage", box=box.ROUNDED)
        table.add_column("Filesystem", style="cyan")
        table.add_column("Size")
        table.add_column("Used")
        table.add_column("Available", style="green")
        table.add_column("Use%")
        table.add_column("Mount Point")

        lines = stdout.strip().split("\n")[1:]  # Skip header
        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                use_pct = parts[4].replace("%", "")
                try:
                    pct = int(use_pct)
                    if pct >= 90:
                        pct_display = f"[red]{parts[4]}[/red]"
                    elif pct >= 75:
                        pct_display = f"[yellow]{parts[4]}[/yellow]"
                    else:
                        pct_display = f"[green]{parts[4]}[/green]"
                except ValueError:
                    pct_display = parts[4]

                table.add_row(
                    parts[0][:20],
                    parts[1],
                    parts[2],
                    parts[3],
                    pct_display,
                    parts[5],
                )

        console.print(table)

    # Show inode usage
    console.print("\n[bold]📁 Inode Usage[/bold]\n")
    code, stdout, _ = run_command("df -i --type=ext4 --type=xfs 2>/dev/null | head -5", check=False)
    if code == 0 and stdout:
        console.print(f"[dim]{stdout}[/dim]")

    # Show swap
    console.print("\n[bold]💾 Swap Usage[/bold]\n")
    code, stdout, _ = run_command("free -h | grep -i swap", check=False)
    if code == 0 and stdout:
        console.print(f"[dim]{stdout}[/dim]")

    # Get swap details
    code, stdout, _ = run_command("swapon --show 2>/dev/null", check=False)
    if code == 0 and stdout:
        console.print(f"\n[dim]{stdout}[/dim]")
    else:
        print_warning("No swap configured")

    # Disk health check for critical partitions
    console.print("\n[bold]⚠️ Warnings[/bold]\n")

    warnings = []
    code, stdout, _ = run_command("df --output=pcent,target / /var /home 2>/dev/null | tail -n +2", check=False)
    if code == 0:
        for line in stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    pct = int(parts[0].replace("%", ""))
                    if pct >= 90:
                        warnings.append(f"[red]CRITICAL: {parts[1]} is {pct}% full![/red]")
                    elif pct >= 80:
                        warnings.append(f"[yellow]WARNING: {parts[1]} is {pct}% full[/yellow]")
                except ValueError:
                    pass

    if warnings:
        for w in warnings:
            console.print(f"  • {w}")
    else:
        console.print("  [green]✓ All partitions have sufficient space[/green]")

    questionary.press_any_key_to_continue().ask()


def analyze_directory_sizes():
    """Analyze directory sizes to find space hogs."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Analyze"])

    console.print("\n[bold]📁 Directory Size Analysis[/bold]\n")

    # Common directories to analyze
    dirs_to_check = [
        "/var/www",
        "/var/log",
        "/var/cache",
        "/home",
        "/tmp",
        "/opt",
    ]

    table = Table(title="📊 Directory Sizes", box=box.ROUNDED)
    table.add_column("Directory", style="cyan")
    table.add_column("Size", justify="right")
    table.add_column("Files", justify="right")
    table.add_column("Status")

    for dir_path in dirs_to_check:
        if not Path(dir_path).exists():
            continue

        code, stdout, _ = run_command(
            f"sudo du -sh {dir_path} 2>/dev/null | cut -f1",
            check=False
        )
        size = stdout.strip() if code == 0 and stdout else "N/A"

        # Count files
        code, stdout, _ = run_command(
            f"find {dir_path} -type f 2>/dev/null | wc -l",
            check=False
        )
        file_count = stdout.strip() if code == 0 and stdout else "N/A"

        # Determine status
        try:
            size_val = size.replace("G", "").replace("M", "").replace("K", "")
            if "G" in size and float(size_val) > 10:
                status = "[red]Large[/red]"
            elif "G" in size:
                status = "[yellow]Moderate[/yellow]"
            else:
                status = "[green]OK[/green]"
        except:
            status = "[dim]Unknown[/dim]"

        table.add_row(dir_path, size, file_count, status)

    console.print(table)

    # Top 10 largest directories in /var
    console.print("\n[bold]Top 10 Largest in /var:[/bold]\n")
    code, stdout, _ = run_command(
        "sudo du -h /var --max-depth=2 2>/dev/null | sort -hr | head -10",
        check=False
    )
    if code == 0 and stdout:
        for line in stdout.strip().split("\n"):
            console.print(f"  {line}")

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# CLEANUP FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def quick_cleanup():
    """Perform quick cleanup of common safe locations."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Quick Cleanup"])

    console.print("\n[bold]🧹 Quick Cleanup[/bold]\n")
    console.print("This will clean:\n")
    console.print("  • APT package cache")
    console.print("  • Old kernel packages")
    console.print("  • Thumbnail cache")
    console.print("  • Temporary files older than 7 days")
    console.print("  • Old log files (*.gz)")
    console.print()

    # Calculate potential savings
    console.print("[cyan]Calculating potential space savings...[/cyan]\n")

    savings = 0

    # APT cache
    code, stdout, _ = run_command("du -s /var/cache/apt/archives 2>/dev/null | cut -f1", check=False)
    if code == 0 and stdout:
        try:
            savings += int(stdout.strip())
        except:
            pass

    # Old logs
    code, stdout, _ = run_command("find /var/log -name '*.gz' -exec du -c {} + 2>/dev/null | tail -1 | cut -f1", check=False)
    if code == 0 and stdout:
        try:
            savings += int(stdout.strip())
        except:
            pass

    savings_mb = savings / 1024
    console.print(f"[bold]Estimated savings: ~{savings_mb:.1f} MB[/bold]\n")

    if not confirm_action("Proceed with quick cleanup?"):
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # APT cleanup
        task = progress.add_task("Cleaning APT cache...", total=None)
        run_command("sudo apt-get clean", check=False)
        run_command("sudo apt-get autoremove -y", check=False)
        progress.update(task, description="[green]✓ APT cache cleaned[/green]")

        # Old kernels
        task = progress.add_task("Removing old kernels...", total=None)
        run_command("sudo apt-get autoremove --purge -y", check=False)
        progress.update(task, description="[green]✓ Old kernels removed[/green]")

        # Temp files
        task = progress.add_task("Cleaning temp files...", total=None)
        run_command("sudo find /tmp -type f -atime +7 -delete 2>/dev/null", check=False)
        run_command("sudo find /var/tmp -type f -atime +7 -delete 2>/dev/null", check=False)
        progress.update(task, description="[green]✓ Temp files cleaned[/green]")

        # Old logs
        task = progress.add_task("Removing old compressed logs...", total=None)
        run_command("sudo find /var/log -name '*.gz' -mtime +30 -delete 2>/dev/null", check=False)
        progress.update(task, description="[green]✓ Old logs removed[/green]")

        # Thumbnail cache
        task = progress.add_task("Clearing thumbnail cache...", total=None)
        run_command("rm -rf ~/.cache/thumbnails/* 2>/dev/null", check=False)
        progress.update(task, description="[green]✓ Thumbnails cleared[/green]")

    # Show new disk usage
    code, stdout, _ = run_command("df -h / | tail -1", check=False)
    console.print(f"\n[bold]Current disk usage:[/bold] {stdout.strip()}")

    record_lineage("disk", "quick_cleanup", "cleanup", {"estimated_savings_mb": savings_mb})

    print_success("Quick cleanup complete!")
    questionary.press_any_key_to_continue().ask()


def deep_cleanup():
    """Perform deep cleanup with more aggressive cleaning."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Deep Cleanup"])

    console.print("\n[bold]🗑️ Deep Cleanup[/bold]\n")

    console.print("[yellow]⚠️ Warning: This will perform aggressive cleanup![/yellow]\n")
    console.print("Additional actions:\n")
    console.print("  • Clear systemd journal (keep 7 days)")
    console.print("  • Remove orphaned packages")
    console.print("  • Clear pip cache")
    console.print("  • Clear npm cache")
    console.print("  • Clear composer cache")
    console.print("  • Remove old PHP sessions")
    console.print()

    if not confirm_action("This is aggressive. Are you sure?"):
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Quick cleanup first
        task = progress.add_task("Running quick cleanup...", total=None)
        run_command("sudo apt-get clean && sudo apt-get autoremove -y", check=False)
        progress.update(task, description="[green]✓ Quick cleanup done[/green]")

        # Systemd journal
        task = progress.add_task("Cleaning systemd journal...", total=None)
        run_command("sudo journalctl --vacuum-time=7d", check=False)
        progress.update(task, description="[green]✓ Journal cleaned[/green]")

        # Package caches
        task = progress.add_task("Cleaning package caches...", total=None)
        run_command("pip3 cache purge 2>/dev/null", check=False)
        run_command("npm cache clean --force 2>/dev/null", check=False)
        run_command("composer clear-cache 2>/dev/null", check=False)
        progress.update(task, description="[green]✓ Package caches cleared[/green]")

        # PHP sessions
        task = progress.add_task("Cleaning PHP sessions...", total=None)
        run_command("sudo find /var/lib/php/sessions -type f -mtime +7 -delete 2>/dev/null", check=False)
        progress.update(task, description="[green]✓ PHP sessions cleaned[/green]")

        # Old rotated logs
        task = progress.add_task("Removing old rotated logs...", total=None)
        run_command("sudo find /var/log -name '*.1' -mtime +7 -delete 2>/dev/null", check=False)
        run_command("sudo find /var/log -name '*.old' -mtime +7 -delete 2>/dev/null", check=False)
        progress.update(task, description="[green]✓ Rotated logs cleaned[/green]")

    # Show new disk usage
    code, stdout, _ = run_command("df -h / | tail -1", check=False)
    console.print(f"\n[bold]Current disk usage:[/bold] {stdout.strip()}")

    record_lineage("disk", "deep_cleanup", "cleanup", {})

    print_success("Deep cleanup complete!")
    questionary.press_any_key_to_continue().ask()


def clean_apt_cache():
    """Clean APT package cache."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "APT Cleanup"])

    console.print("\n[bold]📦 APT Cache Cleanup[/bold]\n")

    # Show current cache size
    code, stdout, _ = run_command("du -sh /var/cache/apt/archives 2>/dev/null", check=False)
    if code == 0:
        console.print(f"Current APT cache size: [cyan]{stdout.strip().split()[0]}[/cyan]\n")

    # Count packages
    code, stdout, _ = run_command("ls -1 /var/cache/apt/archives/*.deb 2>/dev/null | wc -l", check=False)
    if code == 0:
        console.print(f"Cached packages: [cyan]{stdout.strip()}[/cyan]\n")

    # Check for removable packages
    code, stdout, _ = run_command("apt-get --dry-run autoremove 2>/dev/null | grep '^Remv' | wc -l", check=False)
    removable = stdout.strip() if code == 0 else "0"
    console.print(f"Packages that can be removed: [cyan]{removable}[/cyan]\n")

    if confirm_action("Clean APT cache and remove unused packages?"):
        console.print("\n[cyan]Cleaning...[/cyan]")
        run_command("sudo apt-get clean", check=False)
        run_command("sudo apt-get autoremove -y", check=False)
        run_command("sudo apt-get autoclean", check=False)
        print_success("APT cache cleaned!")

    questionary.press_any_key_to_continue().ask()


def clean_docker():
    """Clean Docker resources."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Docker Cleanup"])

    console.print("\n[bold]🐳 Docker Cleanup[/bold]\n")

    # Check if Docker is installed
    code, _, _ = run_command("which docker", check=False)
    if code != 0:
        print_warning("Docker is not installed.")
        questionary.press_any_key_to_continue().ask()
        return

    # Show Docker disk usage
    code, stdout, _ = run_command("docker system df 2>/dev/null", check=False)
    if code == 0:
        console.print("[bold]Docker Disk Usage:[/bold]")
        console.print(f"[dim]{stdout}[/dim]\n")

    # Count unused resources
    code, stdout, _ = run_command("docker images -f 'dangling=true' -q | wc -l", check=False)
    dangling_images = stdout.strip() if code == 0 else "0"

    code, stdout, _ = run_command("docker ps -a -f 'status=exited' -q | wc -l", check=False)
    stopped_containers = stdout.strip() if code == 0 else "0"

    console.print(f"Dangling images: [cyan]{dangling_images}[/cyan]")
    console.print(f"Stopped containers: [cyan]{stopped_containers}[/cyan]\n")

    cleanup_type = questionary.select(
        "Select cleanup type:",
        choices=[
            {"name": "🧹 Safe cleanup (unused images, containers, networks)", "value": "safe"},
            {"name": "🗑️ Aggressive cleanup (includes build cache)", "value": "aggressive"},
            {"name": "⬅️ Cancel", "value": None},
        ],
    ).ask()

    if not cleanup_type:
        return

    if cleanup_type == "safe":
        run_command("docker system prune -f", check=False)
    else:
        run_command("docker system prune -af --volumes", check=False)

    print_success("Docker cleanup complete!")
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# LOG MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def show_log_rotation_status():
    """Show logrotate configuration status."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Log Rotation"])

    console.print("\n[bold]📜 Log Rotation Status[/bold]\n")

    # Check logrotate
    code, stdout, _ = run_command("logrotate --version 2>&1 | head -1", check=False)
    if code == 0:
        console.print(f"[green]✓ Logrotate installed:[/green] {stdout.strip()}")
    else:
        print_warning("Logrotate is not installed")

    # Show configured rotations
    console.print("\n[bold]Configured Log Rotations:[/bold]\n")

    configs = [
        ("/etc/logrotate.d/nginx", "Nginx"),
        ("/etc/logrotate.d/php*-fpm", "PHP-FPM"),
        ("/etc/logrotate.d/mysql-server", "MySQL"),
        ("/etc/logrotate.d/postgresql-common", "PostgreSQL"),
        ("/etc/logrotate.d/rsyslog", "Syslog"),
    ]

    table = Table(box=box.SIMPLE)
    table.add_column("Service", style="cyan")
    table.add_column("Status")
    table.add_column("Config File")

    for config_path, service in configs:
        code, stdout, _ = run_command(f"ls {config_path} 2>/dev/null", check=False)
        if code == 0:
            table.add_row(service, "[green]✓ Configured[/green]", config_path)
        else:
            table.add_row(service, "[dim]Not found[/dim]", config_path)

    console.print(table)

    # Last rotation time
    console.print("\n[bold]Last Rotation:[/bold]")
    code, stdout, _ = run_command("ls -la /var/lib/logrotate/status 2>/dev/null", check=False)
    if code == 0:
        console.print(f"[dim]{stdout.strip()}[/dim]")

    questionary.press_any_key_to_continue().ask()


def rotate_logs_now():
    """Force log rotation."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Rotate Logs"])

    console.print("\n[bold]🔄 Force Log Rotation[/bold]\n")

    if not confirm_action("Force rotate all logs now?"):
        return

    console.print("[cyan]Rotating logs...[/cyan]\n")

    code, stdout, stderr = run_command("sudo logrotate -f /etc/logrotate.conf", check=False)

    if code == 0:
        print_success("Logs rotated successfully!")
    else:
        print_error(f"Error rotating logs: {stderr}")

    # Show log sizes after rotation
    console.print("\n[bold]Log sizes after rotation:[/bold]")
    run_command("du -sh /var/log/* 2>/dev/null | sort -hr | head -10", check=False)

    questionary.press_any_key_to_continue().ask()


def find_large_log_files():
    """Find large log files."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Large Logs"])

    console.print("\n[bold]📋 Large Log Files[/bold]\n")

    # Find log files > 100MB
    code, stdout, _ = run_command(
        "sudo find /var/log -type f -size +100M -exec ls -lh {} \\; 2>/dev/null | sort -k5 -hr",
        check=False
    )

    if code == 0 and stdout:
        console.print("[bold]Log files > 100MB:[/bold]\n")
        for line in stdout.strip().split("\n")[:20]:
            console.print(f"  {line}")
    else:
        console.print("[green]✓ No log files larger than 100MB[/green]")

    # Top 15 largest log files
    console.print("\n[bold]Top 15 Largest Log Files:[/bold]\n")
    code, stdout, _ = run_command(
        "sudo find /var/log -type f -exec du -h {} + 2>/dev/null | sort -hr | head -15",
        check=False
    )
    if code == 0 and stdout:
        for line in stdout.strip().split("\n"):
            console.print(f"  {line}")

    # Offer to truncate large logs
    console.print()
    if confirm_action("Truncate log files larger than 500MB?"):
        code, stdout, _ = run_command(
            "sudo find /var/log -type f -size +500M -exec truncate -s 0 {} \\;",
            check=False
        )
        print_success("Large log files truncated!")

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# FILE FINDING
# ═══════════════════════════════════════════════════════════════════════════════

def find_large_files():
    """Find large files on the system."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Large Files"])

    console.print("\n[bold]🔍 Find Large Files[/bold]\n")

    min_size = questionary.select(
        "Minimum file size:",
        choices=[
            {"name": "100 MB", "value": "+100M"},
            {"name": "500 MB", "value": "+500M"},
            {"name": "1 GB", "value": "+1G"},
            {"name": "5 GB", "value": "+5G"},
        ],
    ).ask()

    if not min_size:
        return

    search_path = questionary.select(
        "Search in:",
        choices=[
            {"name": "/ (Entire system)", "value": "/"},
            {"name": "/var", "value": "/var"},
            {"name": "/home", "value": "/home"},
            {"name": "/var/www", "value": "/var/www"},
        ],
    ).ask()

    if not search_path:
        return

    console.print(f"\n[cyan]Searching for files larger than {min_size.replace('+', '')}...[/cyan]\n")

    code, stdout, _ = run_command(
        f"sudo find {search_path} -type f -size {min_size} -exec ls -lh {{}} \\; 2>/dev/null | sort -k5 -hr | head -30",
        check=False
    )

    if code == 0 and stdout:
        console.print("[bold]Large files found:[/bold]\n")
        for line in stdout.strip().split("\n"):
            console.print(f"  {line}")
    else:
        console.print(f"[green]✓ No files larger than {min_size.replace('+', '')} found[/green]")

    questionary.press_any_key_to_continue().ask()


def find_old_files():
    """Find old files that haven't been accessed."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Old Files"])

    console.print("\n[bold]📅 Find Old Files[/bold]\n")

    age = questionary.select(
        "Find files not accessed in:",
        choices=[
            {"name": "30 days", "value": "30"},
            {"name": "90 days", "value": "90"},
            {"name": "180 days", "value": "180"},
            {"name": "365 days", "value": "365"},
        ],
    ).ask()

    if not age:
        return

    search_path = questionary.text(
        "Search in directory:",
        default="/var/www",
    ).ask()

    if not search_path or not Path(search_path).exists():
        print_error("Invalid directory")
        questionary.press_any_key_to_continue().ask()
        return

    console.print(f"\n[cyan]Finding files not accessed in {age} days...[/cyan]\n")

    # Find and show size summary
    code, stdout, _ = run_command(
        f"find {search_path} -type f -atime +{age} -exec du -ch {{}} + 2>/dev/null | tail -1",
        check=False
    )

    if code == 0 and stdout:
        console.print(f"[bold]Total size of old files:[/bold] {stdout.strip()}\n")

    # Show some examples
    code, stdout, _ = run_command(
        f"find {search_path} -type f -atime +{age} -exec ls -lh {{}} \\; 2>/dev/null | head -20",
        check=False
    )

    if code == 0 and stdout:
        console.print("[bold]Sample old files:[/bold]\n")
        for line in stdout.strip().split("\n"):
            console.print(f"  {line}")

    questionary.press_any_key_to_continue().ask()


def find_duplicate_files():
    """Find duplicate files."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Duplicates"])

    console.print("\n[bold]📂 Find Duplicate Files[/bold]\n")

    # Check if fdupes is installed
    code, _, _ = run_command("which fdupes", check=False)
    if code != 0:
        print_warning("fdupes is not installed.")
        if confirm_action("Install fdupes?"):
            run_command("sudo apt-get install -y fdupes", check=False)
        else:
            return

    search_path = questionary.text(
        "Search in directory:",
        default="/var/www",
    ).ask()

    if not search_path or not Path(search_path).exists():
        print_error("Invalid directory")
        questionary.press_any_key_to_continue().ask()
        return

    console.print(f"\n[cyan]Scanning for duplicates in {search_path}...[/cyan]\n")
    console.print("[dim]This may take a while for large directories...[/dim]\n")

    code, stdout, _ = run_command(
        f"fdupes -r -S {search_path} 2>/dev/null | head -100",
        check=False
    )

    if code == 0 and stdout:
        console.print("[bold]Duplicate files found:[/bold]\n")
        console.print(stdout)
    else:
        console.print("[green]✓ No duplicate files found[/green]")

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# SWAP MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def manage_swap():
    """Manage system swap."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Swap"])

    console.print("\n[bold]💾 Swap Management[/bold]\n")

    # Show current swap
    code, stdout, _ = run_command("swapon --show 2>/dev/null", check=False)

    if code == 0 and stdout:
        console.print("[bold]Current Swap:[/bold]")
        console.print(f"[dim]{stdout}[/dim]\n")
    else:
        print_warning("No swap currently configured")
        console.print()

    # Show memory info
    code, stdout, _ = run_command("free -h", check=False)
    if code == 0:
        console.print("[bold]Memory Information:[/bold]")
        console.print(f"[dim]{stdout}[/dim]")

    # Get total RAM
    code, stdout, _ = run_command("grep MemTotal /proc/meminfo | awk '{print $2}'", check=False)
    ram_kb = int(stdout.strip()) if code == 0 and stdout else 0
    ram_gb = ram_kb / 1024 / 1024

    # Recommend swap size based on RAM
    if ram_gb <= 2:
        recommended_swap = "2G"
    elif ram_gb <= 8:
        recommended_swap = f"{int(ram_gb)}G"
    elif ram_gb <= 64:
        recommended_swap = f"{int(ram_gb / 2)}G"
    else:
        recommended_swap = "32G"

    console.print(f"\n[bold]System RAM:[/bold] {ram_gb:.1f} GB")
    console.print(f"[bold]Recommended Swap:[/bold] {recommended_swap}")

    # Actions
    action = questionary.select(
        "What would you like to do?",
        choices=[
            {"name": f"➕ Create swap file ({recommended_swap} recommended)", "value": "create"},
            {"name": "🔧 Adjust swappiness", "value": "swappiness"},
            {"name": "🗑️ Remove swap", "value": "remove"},
            {"name": "⬅️ Back", "value": None},
        ],
    ).ask()

    if not action:
        return

    if action == "create":
        create_swap_file(recommended_swap)
    elif action == "swappiness":
        adjust_swappiness()
    elif action == "remove":
        remove_swap()


def create_swap_file(recommended: str):
    """Create a swap file."""
    size = questionary.text(
        "Swap file size (e.g., 2G, 4G):",
        default=recommended,
    ).ask()

    if not size:
        return

    swap_path = "/swapfile"

    console.print(f"\n[cyan]Creating {size} swap file at {swap_path}...[/cyan]\n")

    if not confirm_action(f"Create {size} swap file?"):
        return

    # Check if swap file exists
    if Path(swap_path).exists():
        print_warning(f"Swap file already exists at {swap_path}")
        if not confirm_action("Remove existing and create new?"):
            return
        run_command(f"sudo swapoff {swap_path} 2>/dev/null", check=False)
        run_command(f"sudo rm {swap_path}", check=False)

    # Create swap file
    console.print("[cyan]Allocating space...[/cyan]")
    code, _, stderr = run_command(f"sudo fallocate -l {size} {swap_path}", check=False)

    if code != 0:
        # Try dd as fallback
        size_mb = int(size.replace("G", "")) * 1024 if "G" in size else int(size.replace("M", ""))
        run_command(f"sudo dd if=/dev/zero of={swap_path} bs=1M count={size_mb}", check=False)

    console.print("[cyan]Setting permissions...[/cyan]")
    run_command(f"sudo chmod 600 {swap_path}", check=False)

    console.print("[cyan]Formatting as swap...[/cyan]")
    run_command(f"sudo mkswap {swap_path}", check=False)

    console.print("[cyan]Enabling swap...[/cyan]")
    run_command(f"sudo swapon {swap_path}", check=False)

    # Add to fstab
    code, stdout, _ = run_command(f"grep -q '{swap_path}' /etc/fstab", check=False)
    if code != 0:
        run_command(f"echo '{swap_path} none swap sw 0 0' | sudo tee -a /etc/fstab", check=False)
        console.print("[green]✓ Added to /etc/fstab for persistence[/green]")

    print_success(f"Swap file created: {size}")

    # Show new status
    run_command("swapon --show", check=False)

    record_lineage("disk", "swap", "create", {"size": size, "path": swap_path})

    questionary.press_any_key_to_continue().ask()


def adjust_swappiness():
    """Adjust system swappiness."""
    # Get current swappiness
    code, stdout, _ = run_command("cat /proc/sys/vm/swappiness", check=False)
    current = stdout.strip() if code == 0 else "60"

    console.print(f"\n[bold]Current swappiness:[/bold] {current}")
    console.print("\n[dim]Swappiness values:[/dim]")
    console.print("  • 0-10: Minimal swapping (for servers with lots of RAM)")
    console.print("  • 10-30: Low swapping (recommended for production)")
    console.print("  • 60: Default (desktop)")
    console.print("  • 100: Aggressive swapping")
    console.print()

    new_value = questionary.select(
        "Select swappiness value:",
        choices=[
            {"name": "10 - Production server (recommended)", "value": "10"},
            {"name": "30 - Moderate", "value": "30"},
            {"name": "60 - Default", "value": "60"},
        ],
    ).ask()

    if not new_value:
        return

    # Set temporarily
    run_command(f"sudo sysctl vm.swappiness={new_value}", check=False)

    # Set permanently
    code, stdout, _ = run_command("grep -q 'vm.swappiness' /etc/sysctl.conf", check=False)
    if code == 0:
        run_command(f"sudo sed -i 's/vm.swappiness=.*/vm.swappiness={new_value}/' /etc/sysctl.conf", check=False)
    else:
        run_command(f"echo 'vm.swappiness={new_value}' | sudo tee -a /etc/sysctl.conf", check=False)

    print_success(f"Swappiness set to {new_value}")

    questionary.press_any_key_to_continue().ask()


def remove_swap():
    """Remove swap file."""
    code, stdout, _ = run_command("swapon --show --noheadings", check=False)

    if code != 0 or not stdout:
        print_info("No swap to remove")
        questionary.press_any_key_to_continue().ask()
        return

    if not confirm_action("Remove all swap?"):
        return

    # Get swap files/partitions
    for line in stdout.strip().split("\n"):
        parts = line.split()
        if parts:
            swap_path = parts[0]
            console.print(f"[cyan]Disabling {swap_path}...[/cyan]")
            run_command(f"sudo swapoff {swap_path}", check=False)

            if swap_path.startswith("/swapfile") or swap_path.endswith("swap"):
                run_command(f"sudo rm {swap_path}", check=False)
                console.print(f"[green]✓ Removed {swap_path}[/green]")

    # Remove from fstab
    run_command("sudo sed -i '/swap/d' /etc/fstab", check=False)

    print_success("Swap removed!")
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# CRON SETUP
# ═══════════════════════════════════════════════════════════════════════════════

def setup_cleanup_cron():
    """Setup automatic cleanup cron job."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Disk", "Setup Cron"])

    console.print("\n[bold]⏰ Setup Cleanup Cron[/bold]\n")

    frequency = questionary.select(
        "How often should cleanup run?",
        choices=[
            {"name": "📅 Weekly (Sunday 3 AM) - Recommended", "value": "weekly"},
            {"name": "📅 Daily (3 AM)", "value": "daily"},
            {"name": "📅 Monthly (1st, 3 AM)", "value": "monthly"},
        ],
    ).ask()

    if not frequency:
        return

    # Build cron expression
    if frequency == "daily":
        cron_expr = "0 3 * * *"
    elif frequency == "weekly":
        cron_expr = "0 3 * * 0"
    else:
        cron_expr = "0 3 1 * *"

    # Cleanup command
    cleanup_cmd = (
        "apt-get clean && "
        "apt-get autoremove -y && "
        "find /tmp -type f -atime +7 -delete && "
        "find /var/log -name '*.gz' -mtime +30 -delete && "
        "journalctl --vacuum-time=7d"
    )

    cron_line = f"{cron_expr} {cleanup_cmd} >/dev/null 2>&1"

    console.print(f"[cyan]Cron expression: {cron_expr}[/cyan]")
    console.print(f"[dim]Command: {cleanup_cmd[:60]}...[/dim]\n")

    if not confirm_action("Add this cleanup cron job?"):
        return

    # Add to root crontab
    code, existing, _ = run_command("sudo crontab -l 2>/dev/null", check=False)
    existing = existing if code == 0 else ""

    # Remove old cleanup entries
    new_lines = [l for l in existing.split("\n") if "disk cleanup" not in l.lower() and "apt-get clean" not in l]
    new_lines.append(f"# Forge disk cleanup ({frequency})")
    new_lines.append(cron_line)

    new_crontab = "\n".join(new_lines).strip() + "\n"
    run_command(f"echo '{new_crontab}' | sudo crontab -", check=False)

    print_success(f"Cleanup cron job configured ({frequency})!")
    questionary.press_any_key_to_continue().ask()
