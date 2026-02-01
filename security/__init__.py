"""
Security Module - ClamAV antivirus, malware scanning, and security tools
"""

import os
import re
import json
import questionary
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, print_warning, print_info, confirm_action
)
from utils.shell import run_command, get_command_output
from state import record_lineage

console = Console()


# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY MENU
# ═══════════════════════════════════════════════════════════════════════════════

SECURITY_MENU_CHOICES = [
    {"name": "🛡️ ClamAV Status", "value": "status"},
    {"name": "📥 Install ClamAV", "value": "install"},
    questionary.Separator("─" * 30),
    {"name": "🔍 Quick Scan", "value": "quick_scan"},
    {"name": "📂 Scan Directory", "value": "scan_dir"},
    {"name": "🌐 Scan Web Files", "value": "scan_web"},
    {"name": "🏠 Full System Scan", "value": "full_scan"},
    questionary.Separator("─" * 30),
    {"name": "📋 View Scan Reports", "value": "reports"},
    {"name": "🔔 File Change Detection", "value": "file_changes"},
    {"name": "🚨 Malware Signatures", "value": "signatures"},
    questionary.Separator("─" * 30),
    {"name": "⏰ Schedule Scans", "value": "schedule"},
    {"name": "🔄 Update Virus Database", "value": "update_db"},
    questionary.Separator("─" * 30),
    {"name": "⬅️ Back", "value": "back"},
]

# Scan report storage
SCAN_REPORT_DIR = Path.home() / ".forge" / "security"


def run_security_menu():
    """Display the security management menu."""
    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "Security"])

        choice = questionary.select(
            "Security & Antivirus:",
            choices=SECURITY_MENU_CHOICES,
            qmark="🔒",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "status":
            show_clamav_status()
        elif choice == "install":
            install_clamav()
        elif choice == "quick_scan":
            quick_scan()
        elif choice == "scan_dir":
            scan_directory()
        elif choice == "scan_web":
            scan_web_files()
        elif choice == "full_scan":
            full_system_scan()
        elif choice == "reports":
            view_scan_reports()
        elif choice == "file_changes":
            file_change_detection()
        elif choice == "signatures":
            malware_signatures()
        elif choice == "schedule":
            schedule_scans()
        elif choice == "update_db":
            update_virus_database()


# ═══════════════════════════════════════════════════════════════════════════════
# CLAMAV STATUS
# ═══════════════════════════════════════════════════════════════════════════════

def show_clamav_status():
    """Show ClamAV installation and status."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Security", "Status"])

    console.print("\n[bold]🛡️ ClamAV Antivirus Status[/bold]\n")

    # Check if ClamAV is installed
    code, version, _ = run_command("clamscan --version 2>/dev/null", check=False)

    if code != 0:
        console.print("[red]✗ ClamAV is NOT installed[/red]")
        console.print("\n[dim]Use 'Install ClamAV' to set up antivirus protection.[/dim]")
        questionary.press_any_key_to_continue().ask()
        return

    # ClamAV version
    console.print(f"[green]✓ ClamAV Installed[/green]: {version.strip()}")

    # Check freshclam service
    code, stdout, _ = run_command("systemctl is-active clamav-freshclam 2>/dev/null", check=False)
    freshclam_active = stdout.strip() == "active"

    if freshclam_active:
        console.print("[green]✓ Freshclam Service[/green]: Active (auto-updating)")
    else:
        console.print("[yellow]⚠ Freshclam Service[/yellow]: Not running")

    # Check clamd service
    code, stdout, _ = run_command("systemctl is-active clamav-daemon 2>/dev/null", check=False)
    clamd_active = stdout.strip() == "active"

    if clamd_active:
        console.print("[green]✓ ClamAV Daemon[/green]: Active")
    else:
        console.print("[dim]• ClamAV Daemon[/dim]: Not running (on-demand scanning only)")

    # Get database info
    console.print("\n[bold cyan]Virus Database:[/bold cyan]")

    code, db_info, _ = run_command("sigtool --info /var/lib/clamav/main.cvd 2>/dev/null", check=False)
    if code == 0:
        for line in db_info.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                console.print(f"  {key.strip()}: [dim]{value.strip()}[/dim]")
    else:
        # Try main.cld
        code, db_info, _ = run_command("sigtool --info /var/lib/clamav/main.cld 2>/dev/null", check=False)
        if code == 0:
            for line in db_info.split("\n")[:5]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    console.print(f"  {key.strip()}: [dim]{value.strip()}[/dim]")

    # Show signature counts
    console.print("\n[bold cyan]Signature Counts:[/bold cyan]")
    code, sigs, _ = run_command("clamscan --debug 2>&1 | grep -i 'loaded' | head -5", check=False)
    if code == 0 and sigs:
        for line in sigs.split("\n"):
            if "loaded" in line.lower():
                console.print(f"  [dim]{line.strip()}[/dim]")

    # Show recent scans
    show_recent_scans()

    console.print()
    questionary.press_any_key_to_continue().ask()


def show_recent_scans():
    """Show recent scan results."""
    SCAN_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    reports = sorted(SCAN_REPORT_DIR.glob("scan_*.json"), reverse=True)[:5]

    if not reports:
        console.print("\n[dim]No recent scans found.[/dim]")
        return

    console.print("\n[bold cyan]Recent Scans:[/bold cyan]")

    table = Table(box=box.SIMPLE)
    table.add_column("Date", style="dim")
    table.add_column("Type")
    table.add_column("Files", justify="right")
    table.add_column("Infected", justify="right")
    table.add_column("Status")

    for report_file in reports:
        try:
            with open(report_file) as f:
                report = json.load(f)

            date = report.get("timestamp", "?")[:16]
            scan_type = report.get("scan_type", "?")
            files = str(report.get("files_scanned", 0))
            infected = report.get("infected_files", 0)

            if infected > 0:
                status = f"[red]⚠ {infected} threats[/red]"
            else:
                status = "[green]✓ Clean[/green]"

            table.add_row(date, scan_type, files, str(infected), status)
        except Exception:
            continue

    console.print(table)


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALL CLAMAV
# ═══════════════════════════════════════════════════════════════════════════════

def install_clamav():
    """Install ClamAV antivirus."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Security", "Install ClamAV"])

    console.print("\n[bold]📥 Install ClamAV Antivirus[/bold]\n")

    # Check if already installed
    code, _, _ = run_command("which clamscan", check=False)
    if code == 0:
        print_info("ClamAV is already installed.")
        if not confirm_action("Reinstall/upgrade ClamAV?"):
            return

    console.print("[cyan]Installing ClamAV packages...[/cyan]\n")

    with console.status("[bold green]Installing ClamAV...", spinner="dots"):
        # Install packages
        code, stdout, stderr = run_command(
            "sudo apt-get update && sudo apt-get install -y clamav clamav-daemon clamav-freshclam",
            check=False
        )

    if code != 0:
        print_error(f"Failed to install ClamAV: {stderr}")
        questionary.press_any_key_to_continue().ask()
        return

    print_success("ClamAV installed successfully!")

    # Stop freshclam temporarily to update database
    console.print("\n[cyan]Updating virus database (this may take a few minutes)...[/cyan]")

    run_command("sudo systemctl stop clamav-freshclam", check=False)

    with console.status("[bold green]Downloading virus signatures...", spinner="dots"):
        code, _, stderr = run_command("sudo freshclam", check=False)

    if code == 0:
        print_success("Virus database updated!")
    else:
        print_warning("Database update may have partially failed. Will retry on next update.")

    # Start services
    run_command("sudo systemctl start clamav-freshclam", check=False)
    run_command("sudo systemctl enable clamav-freshclam", check=False)

    print_success("ClamAV is now active and will auto-update virus signatures.")

    # Record in state
    record_lineage(
        entity_type="security",
        entity_id="clamav",
        action="install",
        old_state=None,
        new_state={"installed": True, "timestamp": datetime.now().isoformat()},
    )

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# SCANNING
# ═══════════════════════════════════════════════════════════════════════════════

def quick_scan():
    """Perform a quick scan of common attack locations."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Security", "Quick Scan"])

    console.print("\n[bold]🔍 Quick Scan[/bold]\n")

    # Common attack vectors
    scan_paths = [
        "/tmp",
        "/var/tmp",
        "/dev/shm",
        "/var/www",
    ]

    existing_paths = [p for p in scan_paths if os.path.exists(p)]

    if not existing_paths:
        print_warning("No common scan paths found.")
        questionary.press_any_key_to_continue().ask()
        return

    console.print("[dim]Scanning common attack locations:[/dim]")
    for path in existing_paths:
        console.print(f"  • {path}")
    console.print()

    if not confirm_action("Start quick scan?"):
        return

    run_clamscan(existing_paths, scan_type="quick")


def scan_directory():
    """Scan a specific directory."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Security", "Scan Directory"])

    console.print("\n[bold]📂 Scan Directory[/bold]\n")

    directory = questionary.text(
        "Directory to scan:",
        default="/var/www",
        validate=lambda x: os.path.isdir(x),
    ).ask()

    if not directory:
        return

    # Options
    recursive = questionary.confirm("Scan recursively?", default=True).ask()

    run_clamscan([directory], scan_type="directory", recursive=recursive)


def scan_web_files():
    """Scan web server files for malware."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Security", "Scan Web Files"])

    console.print("\n[bold]🌐 Scan Web Files[/bold]\n")

    # Common web directories
    web_dirs = ["/var/www", "/home/*/public_html", "/srv/www"]
    existing = []

    for d in web_dirs:
        import glob
        matches = glob.glob(d)
        existing.extend([m for m in matches if os.path.isdir(m)])

    if not existing:
        print_warning("No web directories found.")
        questionary.press_any_key_to_continue().ask()
        return

    console.print("[dim]Web directories to scan:[/dim]")
    for path in existing:
        console.print(f"  • {path}")
    console.print()

    # Options
    console.print("\n[bold]Scan Options:[/bold]")

    scan_php = questionary.confirm("Focus on PHP files? (faster)", default=True).ask()

    if scan_php:
        # Scan only PHP files which are common attack targets
        run_clamscan(
            existing,
            scan_type="web",
            extra_args="--include='*.php' --include='*.phtml' --include='*.php?' --include='.htaccess'"
        )
    else:
        run_clamscan(existing, scan_type="web")


def full_system_scan():
    """Perform a full system scan."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Security", "Full Scan"])

    console.print("\n[bold]🏠 Full System Scan[/bold]\n")

    print_warning("Full system scan may take a long time!")
    console.print("[dim]This will scan the entire filesystem excluding system directories.[/dim]\n")

    if not confirm_action("Start full system scan?"):
        return

    # Exclude system directories
    exclude_dirs = [
        "/proc",
        "/sys",
        "/dev",
        "/run",
        "/var/lib/clamav",
    ]

    exclude_args = " ".join([f"--exclude-dir={d}" for d in exclude_dirs])

    run_clamscan(["/"], scan_type="full", extra_args=exclude_args)


def run_clamscan(
    paths: List[str],
    scan_type: str = "custom",
    recursive: bool = True,
    extra_args: str = "",
):
    """Run clamscan with specified options."""
    # Check if ClamAV is installed
    code, _, _ = run_command("which clamscan", check=False)
    if code != 0:
        print_error("ClamAV is not installed. Please install it first.")
        questionary.press_any_key_to_continue().ask()
        return

    # Build command
    paths_str = " ".join(paths)
    recursive_flag = "-r" if recursive else ""

    # Create report file
    SCAN_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = SCAN_REPORT_DIR / f"scan_{timestamp}.json"
    log_file = SCAN_REPORT_DIR / f"scan_{timestamp}.log"

    cmd = f"sudo clamscan {recursive_flag} --infected --bell {extra_args} {paths_str} 2>&1 | tee {log_file}"

    console.print("\n[bold cyan]Scanning...[/bold cyan]")
    console.print(f"[dim]Log file: {log_file}[/dim]\n")

    # Run scan
    start_time = datetime.now()
    code, stdout, _ = run_command(cmd, check=False)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Parse results
    result = parse_clamscan_output(stdout)
    result["scan_type"] = scan_type
    result["paths"] = paths
    result["timestamp"] = start_time.isoformat()
    result["duration_seconds"] = duration
    result["log_file"] = str(log_file)

    # Save report
    with open(report_file, "w") as f:
        json.dump(result, f, indent=2)

    # Display results
    console.print("\n" + "─" * 50)
    console.print("\n[bold]📊 Scan Results[/bold]\n")

    if result.get("infected_files", 0) > 0:
        console.print(Panel(
            f"[red bold]⚠️ THREATS DETECTED: {result['infected_files']} infected files[/red bold]",
            border_style="red",
        ))

        if result.get("infected_list"):
            console.print("\n[bold red]Infected Files:[/bold red]")
            for infected in result["infected_list"][:20]:
                console.print(f"  [red]• {infected}[/red]")

            if len(result["infected_list"]) > 20:
                console.print(f"  [dim]... and {len(result['infected_list']) - 20} more[/dim]")

        console.print(f"\n[yellow]Review the log file for details: {log_file}[/yellow]")
    else:
        console.print(Panel(
            "[green bold]✓ No threats detected[/green bold]",
            border_style="green",
        ))

    # Statistics
    console.print(f"\n[dim]Files scanned: {result.get('files_scanned', 'N/A')}[/dim]")
    console.print(f"[dim]Data scanned: {result.get('data_scanned', 'N/A')}[/dim]")
    console.print(f"[dim]Duration: {duration:.1f} seconds[/dim]")
    console.print(f"[dim]Report saved: {report_file}[/dim]")

    # Record in state
    record_lineage(
        entity_type="scan",
        entity_id=timestamp,
        action="complete",
        old_state=None,
        new_state=result,
    )

    questionary.press_any_key_to_continue().ask()


def parse_clamscan_output(output: str) -> Dict:
    """Parse clamscan output."""
    result = {
        "infected_files": 0,
        "files_scanned": 0,
        "data_scanned": "0",
        "infected_list": [],
    }

    for line in output.split("\n"):
        line = line.strip()

        # Infected file
        if "FOUND" in line:
            result["infected_list"].append(line.split(":")[0])

        # Stats
        if line.startswith("Infected files:"):
            match = re.search(r"(\d+)", line)
            if match:
                result["infected_files"] = int(match.group(1))

        if line.startswith("Scanned files:"):
            match = re.search(r"(\d+)", line)
            if match:
                result["files_scanned"] = int(match.group(1))

        if line.startswith("Data scanned:"):
            result["data_scanned"] = line.split(":")[-1].strip()

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# REPORTS & FILE CHANGES
# ═══════════════════════════════════════════════════════════════════════════════

def view_scan_reports():
    """View saved scan reports."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Security", "Scan Reports"])

    console.print("\n[bold]📋 Scan Reports[/bold]\n")

    SCAN_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    reports = sorted(SCAN_REPORT_DIR.glob("scan_*.json"), reverse=True)

    if not reports:
        print_info("No scan reports found.")
        questionary.press_any_key_to_continue().ask()
        return

    # Build table
    table = Table(box=box.ROUNDED, header_style="bold magenta")
    table.add_column("#", style="dim")
    table.add_column("Date", style="cyan")
    table.add_column("Type")
    table.add_column("Paths")
    table.add_column("Files", justify="right")
    table.add_column("Infected", justify="right")
    table.add_column("Duration", justify="right")
    table.add_column("Status")

    for i, report_file in enumerate(reports[:20], 1):
        try:
            with open(report_file) as f:
                report = json.load(f)

            date = report.get("timestamp", "?")[:16]
            scan_type = report.get("scan_type", "?")
            paths = ", ".join(report.get("paths", []))[:30]
            files = str(report.get("files_scanned", 0))
            infected = report.get("infected_files", 0)
            duration = f"{report.get('duration_seconds', 0):.0f}s"

            if infected > 0:
                status = f"[red]⚠ {infected} threats[/red]"
            else:
                status = "[green]✓ Clean[/green]"

            table.add_row(str(i), date, scan_type, paths, files, str(infected), duration, status)
        except Exception:
            continue

    console.print(table)

    # Options
    console.print()
    action = questionary.select(
        "Action:",
        choices=[
            {"name": "📄 View Report Details", "value": "view"},
            {"name": "🗑️ Clear Old Reports", "value": "clear"},
            {"name": "⬅️ Back", "value": "back"},
        ],
    ).ask()

    if action == "view" and reports:
        # Select report to view
        choices = [
            {"name": f"{r.name} ({r.stat().st_mtime})", "value": r}
            for r in reports[:10]
        ]
        selected = questionary.select("Select report:", choices=choices).ask()

        if selected:
            with open(selected) as f:
                report = json.load(f)
            console.print(Panel(json.dumps(report, indent=2), title="Report Details"))
            questionary.press_any_key_to_continue().ask()

    elif action == "clear":
        if confirm_action("Delete all reports older than 30 days?"):
            import time
            cutoff = time.time() - (30 * 24 * 60 * 60)
            deleted = 0
            for report in reports:
                if report.stat().st_mtime < cutoff:
                    report.unlink()
                    deleted += 1
            print_success(f"Deleted {deleted} old reports.")
            questionary.press_any_key_to_continue().ask()


def file_change_detection():
    """Setup and run file change detection."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Security", "File Changes"])

    console.print("\n[bold]🔔 File Change Detection[/bold]\n")

    # Check for aide or similar tools
    tools = {
        "aide": "Advanced Intrusion Detection Environment",
        "tripwire": "File integrity checker",
        "inotifywait": "Real-time file monitoring (inotify-tools)",
    }

    installed = []
    for tool, desc in tools.items():
        code, _, _ = run_command(f"which {tool}", check=False)
        if code == 0:
            installed.append(tool)
            console.print(f"[green]✓[/green] {tool}: {desc}")
        else:
            console.print(f"[dim]✗ {tool}: {desc}[/dim]")

    console.print()

    # Options
    action = questionary.select(
        "Action:",
        choices=[
            {"name": "📥 Install inotify-tools", "value": "install_inotify"},
            {"name": "👁️ Monitor Directory (live)", "value": "monitor"},
            {"name": "📊 Generate File Baseline", "value": "baseline"},
            {"name": "🔍 Check Against Baseline", "value": "check"},
            {"name": "⬅️ Back", "value": "back"},
        ],
    ).ask()

    if action == "install_inotify":
        with console.status("[bold green]Installing inotify-tools..."):
            run_command("sudo apt-get install -y inotify-tools", check=False)
        print_success("inotify-tools installed!")
        questionary.press_any_key_to_continue().ask()

    elif action == "monitor":
        directory = questionary.text(
            "Directory to monitor:",
            default="/var/www",
        ).ask()

        if directory and os.path.isdir(directory):
            console.print(f"\n[cyan]Monitoring {directory} for changes...[/cyan]")
            console.print("[dim]Press Ctrl+C to stop[/dim]\n")

            try:
                os.system(f"inotifywait -m -r -e create -e modify -e delete {directory}")
            except KeyboardInterrupt:
                pass

    elif action == "baseline":
        generate_file_baseline()

    elif action == "check":
        check_file_baseline()


def generate_file_baseline():
    """Generate a baseline of file checksums."""
    directory = questionary.text(
        "Directory to baseline:",
        default="/var/www",
    ).ask()

    if not directory or not os.path.isdir(directory):
        return

    console.print(f"\n[cyan]Generating file baseline for {directory}...[/cyan]")

    baseline_file = SCAN_REPORT_DIR / "file_baseline.json"
    SCAN_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = {
        "directory": directory,
        "timestamp": datetime.now().isoformat(),
        "files": {},
    }

    with console.status("[bold green]Scanning files..."):
        code, stdout, _ = run_command(
            f"find {directory} -type f -exec md5sum {{}} \\; 2>/dev/null",
            check=False
        )

    if code == 0 and stdout:
        for line in stdout.split("\n"):
            if "  " in line:
                checksum, filepath = line.split("  ", 1)
                baseline["files"][filepath] = {
                    "md5": checksum,
                    "seen": datetime.now().isoformat(),
                }

    with open(baseline_file, "w") as f:
        json.dump(baseline, f, indent=2)

    print_success(f"Baseline created with {len(baseline['files'])} files!")
    console.print(f"[dim]Saved to: {baseline_file}[/dim]")
    questionary.press_any_key_to_continue().ask()


def check_file_baseline():
    """Check current files against baseline."""
    baseline_file = SCAN_REPORT_DIR / "file_baseline.json"

    if not baseline_file.exists():
        print_warning("No baseline found. Generate one first.")
        questionary.press_any_key_to_continue().ask()
        return

    with open(baseline_file) as f:
        baseline = json.load(f)

    directory = baseline["directory"]
    console.print(f"\n[cyan]Checking {directory} against baseline...[/cyan]")

    with console.status("[bold green]Scanning files..."):
        code, stdout, _ = run_command(
            f"find {directory} -type f -exec md5sum {{}} \\; 2>/dev/null",
            check=False
        )

    current_files = {}
    if code == 0 and stdout:
        for line in stdout.split("\n"):
            if "  " in line:
                checksum, filepath = line.split("  ", 1)
                current_files[filepath] = checksum

    # Compare
    baseline_files = baseline["files"]

    new_files = set(current_files.keys()) - set(baseline_files.keys())
    deleted_files = set(baseline_files.keys()) - set(current_files.keys())
    modified_files = [
        f for f in current_files
        if f in baseline_files and current_files[f] != baseline_files[f]["md5"]
    ]

    console.print("\n[bold]📊 Change Detection Results[/bold]\n")

    if new_files:
        console.print(f"[yellow]➕ New files ({len(new_files)}):[/yellow]")
        for f in list(new_files)[:10]:
            console.print(f"   {f}")
        if len(new_files) > 10:
            console.print(f"   [dim]... and {len(new_files) - 10} more[/dim]")
        console.print()

    if deleted_files:
        console.print(f"[red]➖ Deleted files ({len(deleted_files)}):[/red]")
        for f in list(deleted_files)[:10]:
            console.print(f"   {f}")
        if len(deleted_files) > 10:
            console.print(f"   [dim]... and {len(deleted_files) - 10} more[/dim]")
        console.print()

    if modified_files:
        console.print(f"[orange1]✏️  Modified files ({len(modified_files)}):[/orange1]")
        for f in modified_files[:10]:
            console.print(f"   {f}")
        if len(modified_files) > 10:
            console.print(f"   [dim]... and {len(modified_files) - 10} more[/dim]")
        console.print()

    if not new_files and not deleted_files and not modified_files:
        console.print("[green]✓ No changes detected![/green]")

    console.print(f"\n[dim]Baseline from: {baseline['timestamp']}[/dim]")
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# MALWARE SIGNATURES & UPDATE
# ═══════════════════════════════════════════════════════════════════════════════

def malware_signatures():
    """View and manage malware signatures."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Security", "Signatures"])

    console.print("\n[bold]🚨 Malware Signatures[/bold]\n")

    # Get signature info
    code, _, _ = run_command("which sigtool", check=False)
    if code != 0:
        print_warning("ClamAV tools not installed.")
        questionary.press_any_key_to_continue().ask()
        return

    # List database files
    console.print("[bold cyan]Virus Databases:[/bold cyan]\n")

    db_files = [
        "/var/lib/clamav/main.cvd",
        "/var/lib/clamav/main.cld",
        "/var/lib/clamav/daily.cvd",
        "/var/lib/clamav/daily.cld",
        "/var/lib/clamav/bytecode.cvd",
        "/var/lib/clamav/bytecode.cld",
    ]

    table = Table(box=box.SIMPLE)
    table.add_column("Database", style="cyan")
    table.add_column("Version", style="dim")
    table.add_column("Signatures", justify="right")
    table.add_column("Build Time", style="dim")

    for db in db_files:
        if os.path.exists(db):
            code, info, _ = run_command(f"sigtool --info {db} 2>/dev/null", check=False)
            if code == 0:
                version = "?"
                sigs = "?"
                build = "?"

                for line in info.split("\n"):
                    if line.startswith("Version:"):
                        version = line.split(":")[-1].strip()
                    elif line.startswith("Signatures:"):
                        sigs = line.split(":")[-1].strip()
                    elif line.startswith("Build time:"):
                        build = line.split(":", 1)[-1].strip()

                table.add_row(os.path.basename(db), version, sigs, build)

    console.print(table)

    # Total signatures
    code, stdout, _ = run_command("sigtool --list-sigs 2>/dev/null | wc -l", check=False)
    if code == 0 and stdout:
        console.print(f"\n[bold]Total Signatures:[/bold] {stdout.strip()}")

    # Last update
    code, stdout, _ = run_command("stat -c '%y' /var/lib/clamav/daily.cvd 2>/dev/null", check=False)
    if code == 0 and stdout:
        console.print(f"[dim]Last database update: {stdout.strip()[:19]}[/dim]")

    console.print()
    questionary.press_any_key_to_continue().ask()


def update_virus_database():
    """Update ClamAV virus database."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Security", "Update Database"])

    console.print("\n[bold]🔄 Update Virus Database[/bold]\n")

    # Check if freshclam is running
    code, stdout, _ = run_command("systemctl is-active clamav-freshclam", check=False)

    if stdout.strip() == "active":
        print_info("Freshclam service is running (auto-updates enabled).")

        if not confirm_action("Force an immediate update?"):
            return

        # Stop freshclam temporarily
        run_command("sudo systemctl stop clamav-freshclam", check=False)

    console.print("[cyan]Downloading latest virus signatures...[/cyan]\n")

    with console.status("[bold green]Updating database...", spinner="dots"):
        code, stdout, stderr = run_command("sudo freshclam", check=False)

    if code == 0:
        print_success("Virus database updated successfully!")
        console.print(f"\n[dim]{stdout}[/dim]")
    else:
        print_warning("Database update completed with warnings.")
        console.print(f"\n[dim]{stderr}[/dim]")

    # Restart freshclam
    run_command("sudo systemctl start clamav-freshclam", check=False)

    questionary.press_any_key_to_continue().ask()


def schedule_scans():
    """Schedule automatic antivirus scans."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Security", "Schedule Scans"])

    console.print("\n[bold]⏰ Schedule Automatic Scans[/bold]\n")

    # Check if clamdscan is available (faster)
    code, _, _ = run_command("which clamdscan", check=False)
    use_clamdscan = code == 0

    scan_command = "clamdscan" if use_clamdscan else "clamscan"

    schedules = [
        {
            "name": "Daily web scan (3 AM)",
            "cron": "0 3 * * *",
            "command": f"sudo {scan_command} -r --infected /var/www 2>&1 | logger -t clamav-scan",
        },
        {
            "name": "Weekly full scan (Sunday 2 AM)",
            "cron": "0 2 * * 0",
            "command": f"sudo {scan_command} -r --infected --exclude-dir=/proc --exclude-dir=/sys / 2>&1 | logger -t clamav-scan",
        },
        {
            "name": "Hourly temp directory scan",
            "cron": "0 * * * *",
            "command": f"sudo {scan_command} -r --infected /tmp /var/tmp 2>&1 | logger -t clamav-scan",
        },
    ]

    for sched in schedules:
        console.print(f"[cyan]{sched['name']}[/cyan]")
        console.print(f"  Schedule: [dim]{sched['cron']}[/dim]")
        console.print()

    selected = questionary.select(
        "Select scan to schedule:",
        choices=[
            {"name": s["name"], "value": i}
            for i, s in enumerate(schedules)
        ] + [{"name": "Cancel", "value": None}],
    ).ask()

    if selected is None:
        return

    sched = schedules[selected]

    if confirm_action(f"Add '{sched['name']}' to cron?"):
        # Add to root crontab
        code, existing, _ = run_command("sudo crontab -l 2>/dev/null", check=False)
        existing = existing if code == 0 else ""

        new_entry = f"{sched['cron']} {sched['command']}"
        new_crontab = existing.strip() + "\n" + new_entry + "\n"

        code, _, _ = run_command(f"echo '{new_crontab}' | sudo crontab -", check=False)

        if code == 0:
            print_success("Scan scheduled successfully!")
        else:
            print_error("Failed to schedule scan.")

    questionary.press_any_key_to_continue().ask()
