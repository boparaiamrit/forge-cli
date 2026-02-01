"""
Cron Management - Schedule and manage cron jobs
"""

import re
import os
import questionary
from typing import List, Dict, Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, print_warning, print_info, confirm_action
)
from utils.shell import run_command, get_command_output

console = Console()


# ═══════════════════════════════════════════════════════════════════════════════
# CRON MENU
# ═══════════════════════════════════════════════════════════════════════════════

CRON_MENU_CHOICES = [
    {"name": "📋 List Cron Jobs", "value": "list"},
    {"name": "➕ Add Cron Job", "value": "add"},
    {"name": "🗑️ Remove Cron Job", "value": "remove"},
    questionary.Separator("─" * 30),
    {"name": "🔒 SSL Auto-Renewal", "value": "ssl_renewal"},
    {"name": "🧹 Cleanup Jobs", "value": "cleanup"},
    {"name": "📊 Backup Jobs", "value": "backup"},
    questionary.Separator("─" * 30),
    {"name": "📝 Edit Crontab", "value": "edit"},
    {"name": "🔄 Reload Cron", "value": "reload"},
    questionary.Separator("─" * 30),
    {"name": "⬅️ Back", "value": "back"},
]

# Common cron schedules
CRON_SCHEDULES = {
    "every_minute": {"cron": "* * * * *", "desc": "Every minute"},
    "every_5_minutes": {"cron": "*/5 * * * *", "desc": "Every 5 minutes"},
    "every_15_minutes": {"cron": "*/15 * * * *", "desc": "Every 15 minutes"},
    "every_30_minutes": {"cron": "*/30 * * * *", "desc": "Every 30 minutes"},
    "hourly": {"cron": "0 * * * *", "desc": "Every hour"},
    "daily_midnight": {"cron": "0 0 * * *", "desc": "Daily at midnight"},
    "daily_3am": {"cron": "0 3 * * *", "desc": "Daily at 3:00 AM"},
    "daily_6am": {"cron": "0 6 * * *", "desc": "Daily at 6:00 AM"},
    "weekly_sunday": {"cron": "0 0 * * 0", "desc": "Weekly on Sunday midnight"},
    "weekly_monday": {"cron": "0 0 * * 1", "desc": "Weekly on Monday midnight"},
    "monthly": {"cron": "0 0 1 * *", "desc": "First day of month midnight"},
    "twice_daily": {"cron": "0 0,12 * * *", "desc": "Twice daily (midnight & noon)"},
}


def run_cron_menu():
    """Display the cron management menu."""
    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "Cron Jobs"])

        choice = questionary.select(
            "Cron Job Management:",
            choices=CRON_MENU_CHOICES,
            qmark="⏰",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "list":
            list_cron_jobs()
        elif choice == "add":
            add_cron_job()
        elif choice == "remove":
            remove_cron_job()
        elif choice == "ssl_renewal":
            setup_ssl_renewal()
        elif choice == "cleanup":
            setup_cleanup_jobs()
        elif choice == "backup":
            setup_backup_jobs()
        elif choice == "edit":
            edit_crontab()
        elif choice == "reload":
            reload_cron()


# ═══════════════════════════════════════════════════════════════════════════════
# LIST CRON JOBS
# ═══════════════════════════════════════════════════════════════════════════════

def list_cron_jobs():
    """List all cron jobs for current user and root."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Cron Jobs", "List"])

    console.print("\n[bold]📋 Cron Jobs[/bold]\n")

    # Get user crontab
    user_jobs = get_crontab_entries()

    # Get root crontab
    root_jobs = get_crontab_entries(user="root")

    # Get system cron directories
    system_jobs = get_system_cron_jobs()

    # Display user jobs
    if user_jobs:
        console.print("[bold cyan]User Crontab:[/bold cyan]")
        display_cron_table(user_jobs)
    else:
        console.print("[dim]No user cron jobs found.[/dim]")

    console.print()

    # Display root jobs
    if root_jobs:
        console.print("[bold cyan]Root Crontab:[/bold cyan]")
        display_cron_table(root_jobs)
    else:
        console.print("[dim]No root cron jobs found.[/dim]")

    console.print()

    # Display system jobs summary
    if system_jobs:
        console.print("[bold cyan]System Cron Jobs:[/bold cyan]")
        for directory, jobs in system_jobs.items():
            console.print(f"\n[dim]{directory}/[/dim]")
            for job in jobs[:5]:  # Show first 5
                console.print(f"  • {job}")
            if len(jobs) > 5:
                console.print(f"  [dim]... and {len(jobs) - 5} more[/dim]")

    console.print()
    questionary.press_any_key_to_continue().ask()


def get_crontab_entries(user: str = None) -> List[Dict]:
    """Get crontab entries for a user."""
    cmd = "crontab -l" if not user else f"sudo crontab -u {user} -l"
    code, stdout, _ = run_command(cmd, check=False)

    if code != 0 or not stdout:
        return []

    jobs = []
    for line in stdout.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            # Parse cron entry
            parts = line.split(None, 5)
            if len(parts) >= 6:
                jobs.append({
                    "minute": parts[0],
                    "hour": parts[1],
                    "day": parts[2],
                    "month": parts[3],
                    "weekday": parts[4],
                    "command": parts[5],
                    "schedule": f"{parts[0]} {parts[1]} {parts[2]} {parts[3]} {parts[4]}",
                })

    return jobs


def get_system_cron_jobs() -> Dict[str, List[str]]:
    """Get jobs from system cron directories."""
    cron_dirs = [
        "/etc/cron.d",
        "/etc/cron.hourly",
        "/etc/cron.daily",
        "/etc/cron.weekly",
        "/etc/cron.monthly",
    ]

    result = {}
    for cron_dir in cron_dirs:
        code, stdout, _ = run_command(f"ls {cron_dir} 2>/dev/null", check=False)
        if code == 0 and stdout:
            files = [f for f in stdout.split("\n") if f and not f.startswith(".")]
            if files:
                result[cron_dir] = files

    return result


def display_cron_table(jobs: List[Dict]):
    """Display cron jobs in a table."""
    table = Table(box=box.ROUNDED, header_style="bold magenta")
    table.add_column("Schedule", style="cyan")
    table.add_column("Human Readable", style="dim")
    table.add_column("Command")

    for job in jobs:
        human = cron_to_human(job["schedule"])
        command = job["command"][:50] + "..." if len(job["command"]) > 50 else job["command"]
        table.add_row(job["schedule"], human, command)

    console.print(table)


def cron_to_human(schedule: str) -> str:
    """Convert cron schedule to human readable format."""
    parts = schedule.split()
    if len(parts) != 5:
        return schedule

    minute, hour, day, month, weekday = parts

    # Check common patterns
    if schedule == "* * * * *":
        return "Every minute"
    if schedule == "0 * * * *":
        return "Every hour"
    if schedule == "0 0 * * *":
        return "Daily at midnight"
    if schedule == "0 0 * * 0":
        return "Weekly (Sunday)"
    if schedule == "0 0 1 * *":
        return "Monthly (1st)"

    # Build description
    desc = []

    if minute.startswith("*/"):
        desc.append(f"Every {minute[2:]} min")
    elif minute != "*":
        desc.append(f"At minute {minute}")

    if hour.startswith("*/"):
        desc.append(f"Every {hour[2:]} hours")
    elif hour != "*":
        desc.append(f"At {hour}:00")

    if day != "*":
        desc.append(f"Day {day}")

    if weekday != "*":
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        if weekday.isdigit():
            desc.append(days[int(weekday) % 7])

    return ", ".join(desc) if desc else schedule


# ═══════════════════════════════════════════════════════════════════════════════
# ADD CRON JOB
# ═══════════════════════════════════════════════════════════════════════════════

def add_cron_job():
    """Add a new cron job."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Cron Jobs", "Add"])

    console.print("\n[bold]➕ Add Cron Job[/bold]\n")

    # Choose schedule type
    schedule_type = questionary.select(
        "Select schedule:",
        choices=[
            {"name": "📅 Use preset schedule", "value": "preset"},
            {"name": "✏️ Custom cron expression", "value": "custom"},
        ],
    ).ask()

    if not schedule_type:
        return

    if schedule_type == "preset":
        # Show preset schedules
        schedule_choices = [
            {"name": f"{v['desc']} ({v['cron']})", "value": k}
            for k, v in CRON_SCHEDULES.items()
        ]
        schedule_choices.append(questionary.Separator())
        schedule_choices.append({"name": "Cancel", "value": None})

        selected = questionary.select(
            "Select schedule:",
            choices=schedule_choices,
        ).ask()

        if not selected:
            return

        cron_expr = CRON_SCHEDULES[selected]["cron"]
    else:
        cron_expr = questionary.text(
            "Cron expression (e.g., '0 3 * * *'):",
            validate=lambda x: len(x.split()) == 5,
        ).ask()

        if not cron_expr:
            return

    # Get command
    command = questionary.text(
        "Command to run:",
        validate=lambda x: len(x) > 0,
    ).ask()

    if not command:
        return

    # Choose user
    run_as = questionary.select(
        "Run as user:",
        choices=[
            {"name": "Current user", "value": "user"},
            {"name": "Root (sudo)", "value": "root"},
        ],
    ).ask()

    # Confirm
    console.print(f"\n[bold]New cron job:[/bold]")
    console.print(f"  Schedule: [cyan]{cron_expr}[/cyan] ({cron_to_human(cron_expr)})")
    console.print(f"  Command: [cyan]{command}[/cyan]")
    console.print(f"  User: [cyan]{run_as}[/cyan]")
    console.print()

    if not confirm_action("Add this cron job?"):
        return

    # Add to crontab
    add_to_crontab(cron_expr, command, as_root=(run_as == "root"))


def add_to_crontab(schedule: str, command: str, as_root: bool = False):
    """Add an entry to crontab."""
    # Get existing crontab
    cmd = "crontab -l 2>/dev/null" if not as_root else "sudo crontab -l 2>/dev/null"
    code, existing, _ = run_command(cmd, check=False)

    existing = existing if code == 0 else ""

    # Add new entry
    new_entry = f"{schedule} {command}"
    new_crontab = existing.strip() + "\n" + new_entry + "\n"

    # Write back
    if as_root:
        code, _, stderr = run_command(
            f"echo '{new_crontab}' | sudo crontab -",
            check=False
        )
    else:
        code, _, stderr = run_command(
            f"echo '{new_crontab}' | crontab -",
            check=False
        )

    if code == 0:
        print_success("Cron job added successfully!")
    else:
        print_error(f"Failed to add cron job: {stderr}")

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# REMOVE CRON JOB
# ═══════════════════════════════════════════════════════════════════════════════

def remove_cron_job():
    """Remove a cron job."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Cron Jobs", "Remove"])

    console.print("\n[bold]🗑️ Remove Cron Job[/bold]\n")

    # Get all jobs
    user_jobs = get_crontab_entries()

    if not user_jobs:
        print_warning("No cron jobs found to remove.")
        questionary.press_any_key_to_continue().ask()
        return

    # Build choices
    choices = []
    for i, job in enumerate(user_jobs):
        human = cron_to_human(job["schedule"])
        cmd = job["command"][:40] + "..." if len(job["command"]) > 40 else job["command"]
        choices.append({
            "name": f"{job['schedule']} - {cmd} ({human})",
            "value": i,
        })

    choices.append(questionary.Separator())
    choices.append({"name": "Cancel", "value": None})

    selected = questionary.select(
        "Select job to remove:",
        choices=choices,
    ).ask()

    if selected is None:
        return

    # Confirm
    job = user_jobs[selected]
    console.print(f"\n[bold red]Will remove:[/bold red]")
    console.print(f"  {job['schedule']} {job['command']}")
    console.print()

    if not confirm_action("Remove this cron job?"):
        return

    # Remove from crontab
    remove_from_crontab(selected)


def remove_from_crontab(index: int, as_root: bool = False):
    """Remove an entry from crontab by index."""
    # Get existing crontab
    cmd = "crontab -l" if not as_root else "sudo crontab -l"
    code, existing, _ = run_command(cmd, check=False)

    if code != 0:
        print_error("Failed to read crontab")
        return

    # Filter out the line
    lines = existing.split("\n")
    job_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]

    if index >= len(job_lines):
        print_error("Invalid job index")
        return

    # Remove the job
    line_to_remove = job_lines[index]
    new_lines = [l for l in lines if l.strip() != line_to_remove]
    new_crontab = "\n".join(new_lines)

    # Write back
    if as_root:
        code, _, stderr = run_command(f"echo '{new_crontab}' | sudo crontab -", check=False)
    else:
        code, _, stderr = run_command(f"echo '{new_crontab}' | crontab -", check=False)

    if code == 0:
        print_success("Cron job removed successfully!")
    else:
        print_error(f"Failed to remove cron job: {stderr}")

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# SSL RENEWAL
# ═══════════════════════════════════════════════════════════════════════════════

def setup_ssl_renewal():
    """Setup automatic SSL certificate renewal."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Cron Jobs", "SSL Renewal"])

    console.print("\n[bold]🔒 SSL Certificate Auto-Renewal[/bold]\n")

    # Check if certbot renewal is already scheduled
    code, stdout, _ = run_command("sudo cat /etc/cron.d/certbot 2>/dev/null", check=False)

    if code == 0 and stdout:
        console.print("[green]✓ Certbot auto-renewal is already configured[/green]")
        console.print(f"\n[dim]{stdout}[/dim]")
    else:
        # Check for certbot timer (systemd)
        code, stdout, _ = run_command("systemctl is-active certbot.timer 2>/dev/null", check=False)

        if stdout.strip() == "active":
            console.print("[green]✓ Certbot systemd timer is active[/green]")
        else:
            console.print("[yellow]⚠ SSL auto-renewal is NOT configured[/yellow]")
            console.print()

            if confirm_action("Would you like to set up SSL auto-renewal?"):
                # Add certbot renewal cron
                renewal_cron = "0 0,12 * * * root test -x /usr/bin/certbot && certbot renew --quiet"
                code, _, _ = run_command(
                    f"echo '{renewal_cron}' | sudo tee /etc/cron.d/certbot",
                    check=False
                )

                if code == 0:
                    print_success("SSL auto-renewal configured!")
                    print_info("Certbot will check for renewals twice daily.")
                else:
                    print_error("Failed to configure auto-renewal")

    console.print()

    # Show certificate renewal status
    show_ssl_renewal_status()

    questionary.press_any_key_to_continue().ask()


def show_ssl_renewal_status():
    """Show SSL certificate renewal status table."""
    console.print("\n[bold]📜 Certificate Renewal Status[/bold]\n")

    # Get certificate info
    code, stdout, _ = run_command(
        "sudo certbot certificates 2>/dev/null",
        check=False
    )

    if code != 0 or "No certificates found" in stdout or not stdout:
        console.print("[dim]No certificates managed by Certbot.[/dim]")
        return

    # Parse certificate info
    certs = parse_certbot_output(stdout)

    if not certs:
        console.print("[dim]No certificates found.[/dim]")
        return

    # Create table
    table = Table(
        title="🔐 SSL Certificates",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Domain", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Expires", style="yellow")
    table.add_column("Days Left", justify="right")
    table.add_column("Last Renewed", style="dim")
    table.add_column("Next Renewal", style="green")

    for cert in certs:
        # Status
        days = cert.get("days_remaining", 0)
        if days <= 0:
            status = "[red]❌ EXPIRED[/red]"
        elif days <= 7:
            status = "[red]⚠️ CRITICAL[/red]"
        elif days <= 30:
            status = "[yellow]⚠️ WARNING[/yellow]"
        else:
            status = "[green]✓ VALID[/green]"

        # Days styling
        if days <= 7:
            days_str = f"[red]{days}[/red]"
        elif days <= 30:
            days_str = f"[yellow]{days}[/yellow]"
        else:
            days_str = f"[green]{days}[/green]"

        table.add_row(
            cert.get("domain", "?"),
            status,
            cert.get("expiry", "?"),
            days_str,
            cert.get("last_renewed", "-"),
            cert.get("next_renewal", "-"),
        )

    console.print(table)


def parse_certbot_output(output: str) -> List[Dict]:
    """Parse certbot certificates output."""
    certs = []
    current_cert = {}

    for line in output.split("\n"):
        line = line.strip()

        if line.startswith("Certificate Name:"):
            if current_cert:
                certs.append(current_cert)
            current_cert = {"domain": line.split(":")[-1].strip()}
        elif line.startswith("Domains:"):
            domains = line.split(":")[-1].strip()
            current_cert["domains"] = domains
        elif line.startswith("Expiry Date:"):
            # Parse: "Expiry Date: 2024-03-15 10:30:45+00:00 (VALID: 89 days)"
            parts = line.split(":")
            if len(parts) >= 2:
                date_part = ":".join(parts[1:]).strip()
                current_cert["expiry"] = date_part.split("(")[0].strip()[:10]

                # Extract days
                if "days" in date_part:
                    match = re.search(r"(\d+)\s*days", date_part)
                    if match:
                        current_cert["days_remaining"] = int(match.group(1))

                        # Calculate next renewal (30 days before expiry)
                        if current_cert["days_remaining"] > 30:
                            next_renewal_days = current_cert["days_remaining"] - 30
                            current_cert["next_renewal"] = f"In {next_renewal_days} days"
                        else:
                            current_cert["next_renewal"] = "Soon"

    if current_cert:
        certs.append(current_cert)

    return certs


# ═══════════════════════════════════════════════════════════════════════════════
# CLEANUP & BACKUP JOBS
# ═══════════════════════════════════════════════════════════════════════════════

def setup_cleanup_jobs():
    """Setup common cleanup cron jobs."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Cron Jobs", "Cleanup Jobs"])

    console.print("\n[bold]🧹 Setup Cleanup Jobs[/bold]\n")

    cleanup_jobs = [
        {
            "name": "Clear old logs (> 30 days)",
            "schedule": "0 3 * * *",
            "command": "find /var/log -type f -name '*.log' -mtime +30 -delete",
        },
        {
            "name": "Clear apt cache",
            "schedule": "0 4 * * 0",
            "command": "apt-get clean && apt-get autoclean",
        },
        {
            "name": "Clear temp files",
            "schedule": "0 3 * * *",
            "command": "find /tmp -type f -atime +7 -delete",
        },
        {
            "name": "Clear old PHP sessions",
            "schedule": "0 2 * * *",
            "command": "find /var/lib/php/sessions -type f -mmin +1440 -delete 2>/dev/null",
        },
        {
            "name": "Restart PHP-FPM weekly",
            "schedule": "0 4 * * 0",
            "command": "systemctl restart php*-fpm",
        },
    ]

    choices = [
        {"name": f"{job['name']} ({job['schedule']})", "value": i}
        for i, job in enumerate(cleanup_jobs)
    ]
    choices.append(questionary.Separator())
    choices.append({"name": "Cancel", "value": None})

    selected = questionary.select(
        "Select cleanup job to add:",
        choices=choices,
    ).ask()

    if selected is None:
        return

    job = cleanup_jobs[selected]
    console.print(f"\n[bold]Adding:[/bold] {job['name']}")
    console.print(f"[dim]Schedule: {job['schedule']}[/dim]")
    console.print(f"[dim]Command: {job['command']}[/dim]")
    console.print()

    if confirm_action("Add this cleanup job?"):
        add_to_crontab(job["schedule"], job["command"], as_root=True)


def setup_backup_jobs():
    """Setup backup cron jobs."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Cron Jobs", "Backup Jobs"])

    console.print("\n[bold]📊 Setup Backup Jobs[/bold]\n")

    # Get backup location
    backup_dir = questionary.text(
        "Backup directory:",
        default="/var/backups/forge",
    ).ask()

    if not backup_dir:
        return

    backup_jobs = [
        {
            "name": "Backup Nginx configs",
            "schedule": "0 2 * * *",
            "command": f"tar -czf {backup_dir}/nginx-$(date +%Y%m%d).tar.gz /etc/nginx",
        },
        {
            "name": "Backup MySQL databases",
            "schedule": "0 3 * * *",
            "command": f"mysqldump --all-databases | gzip > {backup_dir}/mysql-$(date +%Y%m%d).sql.gz",
        },
        {
            "name": "Backup PostgreSQL databases",
            "schedule": "0 3 * * *",
            "command": f"pg_dumpall | gzip > {backup_dir}/postgres-$(date +%Y%m%d).sql.gz",
        },
        {
            "name": "Backup web files",
            "schedule": "0 4 * * 0",
            "command": f"tar -czf {backup_dir}/www-$(date +%Y%m%d).tar.gz /var/www",
        },
    ]

    choices = [
        {"name": f"{job['name']} ({job['schedule']})", "value": i}
        for i, job in enumerate(backup_jobs)
    ]
    choices.append(questionary.Separator())
    choices.append({"name": "Cancel", "value": None})

    selected = questionary.select(
        "Select backup job to add:",
        choices=choices,
    ).ask()

    if selected is None:
        return

    job = backup_jobs[selected]

    # Create backup directory
    run_command(f"sudo mkdir -p {backup_dir}", check=False)

    console.print(f"\n[bold]Adding:[/bold] {job['name']}")
    console.print(f"[dim]Schedule: {job['schedule']}[/dim]")
    console.print(f"[dim]Command: {job['command']}[/dim]")
    console.print()

    if confirm_action("Add this backup job?"):
        add_to_crontab(job["schedule"], job["command"], as_root=True)


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def edit_crontab():
    """Open crontab in editor."""
    console.print("\n[cyan]Opening crontab in editor...[/cyan]")
    os.system("crontab -e")


def reload_cron():
    """Reload cron daemon."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Cron Jobs", "Reload"])

    console.print("\n[bold]🔄 Reloading Cron Daemon[/bold]\n")

    code, _, stderr = run_command("sudo systemctl reload cron", check=False)

    if code == 0:
        print_success("Cron daemon reloaded successfully!")
    else:
        # Try alternative
        code, _, _ = run_command("sudo service cron reload", check=False)
        if code == 0:
            print_success("Cron daemon reloaded successfully!")
        else:
            print_error(f"Failed to reload cron: {stderr}")

    questionary.press_any_key_to_continue().ask()
