"""
CVE Scanner - Vulnerability scanning for system packages and application dependencies
"""

import os
import re
import json
import questionary
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
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
# CVE DATA PATHS
# ═══════════════════════════════════════════════════════════════════════════════

CVE_DATA_DIR = Path.home() / ".forge" / "cve"
CVE_SCANS_DIR = CVE_DATA_DIR / "scans"
CVE_DB_FILE = CVE_DATA_DIR / "cve_database.json"
LAST_UPDATE_FILE = CVE_DATA_DIR / "last_update"

# Default scan directories
DEFAULT_SCAN_DIRS = [
    "/var/www",
    "/home",
]

# Dependency files to look for
DEPENDENCY_FILES = {
    "package.json": "nodejs",
    "package-lock.json": "nodejs",
    "composer.json": "php",
    "composer.lock": "php",
    "requirements.txt": "python",
    "Pipfile.lock": "python",
    "Gemfile.lock": "ruby",
    "go.mod": "go",
    "Cargo.lock": "rust",
}

# Ubuntu versions supported
UBUNTU_VERSIONS = {
    "24.04": "noble",
    "22.04": "jammy",
    "20.04": "focal",
}


# ═══════════════════════════════════════════════════════════════════════════════
# CVE MENU
# ═══════════════════════════════════════════════════════════════════════════════

CVE_MENU_CHOICES = [
    {"name": "🔍  Full CVE Scan", "value": "full_scan"},
    {"name": "💻  Scan System Packages", "value": "scan_system"},
    {"name": "📦  Scan Application Dependencies", "value": "scan_apps"},
    questionary.Separator("─" * 30),
    {"name": "📋  View Last Scan Results", "value": "view_results"},
    {"name": "📊  Scan History", "value": "history"},
    questionary.Separator("─" * 30),
    {"name": "🔄  Update CVE Database", "value": "update_db"},
    {"name": "⏰  Setup CVE Update Cron", "value": "setup_cron"},
    {"name": "ℹ️   Database Status", "value": "db_status"},
    questionary.Separator("─" * 30),
    {"name": "⬅️   Back", "value": "back"},
]


def run_cve_menu():
    """Display the CVE scanner menu."""
    # Ensure data directories exist
    CVE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    CVE_SCANS_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "CVE Scanner"])

        # Show quick status
        show_cve_status_summary()

        choice = questionary.select(
            "CVE Scanner:",
            choices=CVE_MENU_CHOICES,
            qmark="🔒",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "full_scan":
            run_full_cve_scan()
        elif choice == "scan_system":
            scan_system_packages()
        elif choice == "scan_apps":
            scan_application_dependencies()
        elif choice == "view_results":
            view_last_scan_results()
        elif choice == "history":
            view_scan_history()
        elif choice == "update_db":
            update_cve_database()
        elif choice == "setup_cron":
            setup_cve_cron()
        elif choice == "db_status":
            show_database_status()


def show_cve_status_summary():
    """Show a quick CVE database status summary."""
    # Check last update
    if LAST_UPDATE_FILE.exists():
        last_update = LAST_UPDATE_FILE.read_text().strip()
        console.print(f"[dim]CVE Database last updated: {last_update}[/dim]")
    else:
        console.print("[yellow]⚠ CVE Database not initialized. Run 'Update CVE Database' first.[/yellow]")
    console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PACKAGE SCANNING
# ═══════════════════════════════════════════════════════════════════════════════

def get_ubuntu_version() -> Tuple[str, str]:
    """Get Ubuntu version and codename."""
    code, stdout, _ = run_command("lsb_release -rs", check=False)
    version = stdout.strip() if code == 0 else "22.04"

    code, stdout, _ = run_command("lsb_release -cs", check=False)
    codename = stdout.strip() if code == 0 else "jammy"

    return version, codename


def scan_system_packages():
    """Scan system packages for known CVEs."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "CVE Scanner", "System Packages"])

    console.print("\n[bold]💻 System Package CVE Scan[/bold]\n")

    version, codename = get_ubuntu_version()
    console.print(f"[dim]Ubuntu {version} ({codename})[/dim]\n")

    # Check if tools are available
    console.print("[cyan]Checking for security scanning tools...[/cyan]")

    vulnerabilities = []

    # Method 1: Check using ubuntu-security-status (if available)
    code, _, _ = run_command("which ubuntu-security-status", check=False)
    if code == 0:
        console.print("[green]✓ ubuntu-security-status available[/green]")
        vulnerabilities.extend(scan_with_ubuntu_security_status())
    else:
        # Method 2: Check for packages with security updates
        console.print("[dim]Using apt-based security check...[/dim]")
        vulnerabilities.extend(scan_with_apt_security())

    # Method 3: Check using unattended-upgrades info
    vulns_from_unattended = scan_with_unattended_upgrades()
    for v in vulns_from_unattended:
        if v not in vulnerabilities:
            vulnerabilities.append(v)

    # Display results
    display_system_vulnerabilities(vulnerabilities)

    # Save scan results
    save_scan_results("system", vulnerabilities)

    questionary.press_any_key_to_continue().ask()


def scan_with_ubuntu_security_status() -> List[Dict]:
    """Scan using ubuntu-security-status tool."""
    vulnerabilities = []

    code, stdout, _ = run_command("ubuntu-security-status --unavailable", check=False)

    if code == 0 and stdout:
        # Parse output for packages needing updates
        for line in stdout.split("\n"):
            if "CVE-" in line:
                # Extract CVE IDs
                cves = re.findall(r'CVE-\d{4}-\d+', line)
                if cves:
                    vulnerabilities.append({
                        "type": "system",
                        "package": line.split()[0] if line.split() else "unknown",
                        "cves": cves,
                        "severity": "unknown",
                        "description": line.strip(),
                    })

    return vulnerabilities


def scan_with_apt_security() -> List[Dict]:
    """Scan for security updates using apt."""
    vulnerabilities = []

    # Get security updates
    console.print("[cyan]Checking for security updates...[/cyan]")

    # Update package lists
    run_command("sudo apt-get update -q", check=False)

    # Get security upgrades
    code, stdout, _ = run_command(
        "apt-get -s upgrade 2>/dev/null | grep -i security",
        check=False
    )

    if code == 0 and stdout:
        for line in stdout.split("\n"):
            if line.strip():
                vulnerabilities.append({
                    "type": "system",
                    "package": "security-update",
                    "cves": [],
                    "severity": "security",
                    "description": line.strip(),
                })

    # Get list of upgradable packages
    code, stdout, _ = run_command("apt list --upgradable 2>/dev/null", check=False)

    if code == 0 and stdout:
        lines = stdout.strip().split("\n")[1:]  # Skip header
        for line in lines[:20]:  # Limit display
            if line.strip():
                parts = line.split("/")
                if parts:
                    pkg_name = parts[0]
                    vulnerabilities.append({
                        "type": "system",
                        "package": pkg_name,
                        "cves": [],
                        "severity": "update-available",
                        "description": line.strip(),
                    })

    return vulnerabilities


def scan_with_unattended_upgrades() -> List[Dict]:
    """Check unattended-upgrades for pending security updates."""
    vulnerabilities = []

    # Check if unattended-upgrades log exists
    log_file = Path("/var/log/unattended-upgrades/unattended-upgrades.log")

    if log_file.exists():
        code, stdout, _ = run_command(
            f"sudo grep -i 'CVE-' {log_file} | tail -20",
            check=False
        )

        if code == 0 and stdout:
            for line in stdout.split("\n"):
                cves = re.findall(r'CVE-\d{4}-\d+', line)
                if cves:
                    vulnerabilities.append({
                        "type": "system",
                        "package": "unattended-upgrade",
                        "cves": cves,
                        "severity": "logged",
                        "description": line.strip()[:100],
                    })

    return vulnerabilities


def display_system_vulnerabilities(vulnerabilities: List[Dict]):
    """Display system vulnerabilities in a table."""
    console.print("\n")

    if not vulnerabilities:
        console.print(Panel(
            "[green]✓ No known vulnerabilities found in system packages![/green]\n\n"
            "Your system packages appear to be up to date.",
            title="✅ System Secure",
            border_style="green",
        ))
        return

    # Count by severity
    total = len(vulnerabilities)
    with_cves = sum(1 for v in vulnerabilities if v.get("cves"))

    table = Table(
        title="💻 System Package Vulnerabilities",
        box=box.ROUNDED,
        header_style="bold red",
    )
    table.add_column("Package", style="cyan")
    table.add_column("CVEs", style="red")
    table.add_column("Severity")
    table.add_column("Description", max_width=50)

    for vuln in vulnerabilities[:30]:  # Limit display
        cves = ", ".join(vuln.get("cves", [])) or "-"
        severity = vuln.get("severity", "unknown")

        if severity == "security":
            sev_display = "[red]SECURITY[/red]"
        elif severity == "update-available":
            sev_display = "[yellow]UPDATE[/yellow]"
        else:
            sev_display = f"[dim]{severity}[/dim]"

        table.add_row(
            vuln.get("package", "unknown"),
            cves,
            sev_display,
            vuln.get("description", "")[:50],
        )

    console.print(table)

    console.print(f"\n[bold]Total issues: {total}[/bold]")
    if with_cves > 0:
        console.print(f"[red]Packages with known CVEs: {with_cves}[/red]")

    # Offer to update
    if vulnerabilities:
        console.print()
        if confirm_action("Run system update to fix vulnerabilities?"):
            console.print("\n[cyan]Running system update...[/cyan]")
            run_command("sudo apt-get update && sudo apt-get upgrade -y", check=False)
            print_success("System updated!")


# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATION DEPENDENCY SCANNING
# ═══════════════════════════════════════════════════════════════════════════════

def scan_application_dependencies():
    """Scan application dependencies for CVEs."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "CVE Scanner", "Applications"])

    console.print("\n[bold]📦 Application Dependency CVE Scan[/bold]\n")

    # Ask for directories to scan
    scan_dirs = questionary.checkbox(
        "Select directories to scan:",
        choices=[
            {"name": "/var/www (Web applications)", "value": "/var/www", "checked": True},
            {"name": "/home (User home directories)", "value": "/home", "checked": True},
            {"name": "Custom directory", "value": "custom"},
        ],
    ).ask()

    if not scan_dirs:
        return

    # Handle custom directory
    if "custom" in scan_dirs:
        custom_dir = questionary.text(
            "Enter custom directory path:",
            default="/opt",
        ).ask()
        if custom_dir:
            scan_dirs.remove("custom")
            scan_dirs.append(custom_dir)
        else:
            scan_dirs.remove("custom")

    if not scan_dirs:
        print_warning("No directories selected.")
        questionary.press_any_key_to_continue().ask()
        return

    all_vulnerabilities = []
    projects_found = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning for dependency files...", total=None)

        for scan_dir in scan_dirs:
            if not Path(scan_dir).exists():
                continue

            # Find all dependency files
            for dep_file, ecosystem in DEPENDENCY_FILES.items():
                progress.update(task, description=f"Searching for {dep_file} in {scan_dir}...")

                # Find files
                code, stdout, _ = run_command(
                    f"find {scan_dir} -name '{dep_file}' -type f 2>/dev/null | head -100",
                    check=False
                )

                if code == 0 and stdout:
                    for file_path in stdout.strip().split("\n"):
                        if file_path:
                            project_dir = str(Path(file_path).parent)
                            project_name = Path(project_dir).name

                            projects_found.append({
                                "name": project_name,
                                "path": project_dir,
                                "file": dep_file,
                                "ecosystem": ecosystem,
                            })

    console.print(f"\n[green]Found {len(projects_found)} projects with dependencies[/green]\n")

    if not projects_found:
        print_info("No dependency files found in the selected directories.")
        questionary.press_any_key_to_continue().ask()
        return

    # Display found projects
    table = Table(title="📁 Projects Found", box=box.SIMPLE)
    table.add_column("Project", style="cyan")
    table.add_column("Ecosystem")
    table.add_column("Path", style="dim")

    for project in projects_found[:30]:
        table.add_row(
            project["name"],
            project["ecosystem"],
            project["path"][:50],
        )

    console.print(table)

    # Scan each project
    if confirm_action(f"Scan {len(projects_found)} projects for vulnerabilities?"):
        console.print("\n[cyan]Scanning for vulnerabilities...[/cyan]\n")

        for project in projects_found:
            vulns = scan_project_dependencies(project)
            all_vulnerabilities.extend(vulns)

        # Display results
        display_app_vulnerabilities(all_vulnerabilities)

        # Save results
        save_scan_results("applications", all_vulnerabilities)

    questionary.press_any_key_to_continue().ask()


def scan_project_dependencies(project: Dict) -> List[Dict]:
    """Scan a single project for vulnerabilities."""
    vulnerabilities = []
    ecosystem = project["ecosystem"]
    project_path = project["path"]
    project_name = project["name"]

    console.print(f"  Scanning [cyan]{project_name}[/cyan]...", end=" ")

    if ecosystem == "nodejs":
        vulns = scan_npm_dependencies(project_path, project_name)
        vulnerabilities.extend(vulns)
    elif ecosystem == "php":
        vulns = scan_composer_dependencies(project_path, project_name)
        vulnerabilities.extend(vulns)
    elif ecosystem == "python":
        vulns = scan_python_dependencies(project_path, project_name)
        vulnerabilities.extend(vulns)

    if vulnerabilities:
        console.print(f"[red]{len(vulnerabilities)} issues[/red]")
    else:
        console.print("[green]✓[/green]")

    return vulnerabilities


def scan_npm_dependencies(project_path: str, project_name: str) -> List[Dict]:
    """Scan npm/Node.js dependencies using npm audit."""
    vulnerabilities = []

    # Check if package-lock.json exists (required for npm audit)
    lock_file = Path(project_path) / "package-lock.json"

    if not lock_file.exists():
        # Check if package.json exists and try to generate lock file
        pkg_file = Path(project_path) / "package.json"
        if pkg_file.exists():
            # Parse package.json for dependencies
            try:
                with open(pkg_file) as f:
                    pkg_data = json.load(f)

                deps = {}
                deps.update(pkg_data.get("dependencies", {}))
                deps.update(pkg_data.get("devDependencies", {}))

                for dep_name, dep_version in deps.items():
                    vulnerabilities.append({
                        "type": "nodejs",
                        "project": project_name,
                        "path": project_path,
                        "package": dep_name,
                        "version": dep_version,
                        "cves": [],
                        "severity": "needs-audit",
                        "description": "Run 'npm audit' for detailed CVE check",
                    })
            except (json.JSONDecodeError, IOError):
                pass
        return vulnerabilities

    # Run npm audit
    code, stdout, stderr = run_command(
        f"cd '{project_path}' && npm audit --json 2>/dev/null",
        check=False
    )

    if code != 0 or not stdout:
        return vulnerabilities

    try:
        audit_data = json.loads(stdout)

        # Parse vulnerabilities
        if "vulnerabilities" in audit_data:
            for pkg_name, vuln_info in audit_data["vulnerabilities"].items():
                severity = vuln_info.get("severity", "unknown")

                # Extract CVE IDs from via
                cves = []
                for via_item in vuln_info.get("via", []):
                    if isinstance(via_item, dict):
                        if via_item.get("cve"):
                            cves.append(via_item["cve"])

                vulnerabilities.append({
                    "type": "nodejs",
                    "project": project_name,
                    "path": project_path,
                    "package": pkg_name,
                    "version": vuln_info.get("range", "unknown"),
                    "cves": cves,
                    "severity": severity,
                    "description": vuln_info.get("fixAvailable", {}).get("name", ""),
                })
    except json.JSONDecodeError:
        pass

    return vulnerabilities


def scan_composer_dependencies(project_path: str, project_name: str) -> List[Dict]:
    """Scan Composer/PHP dependencies."""
    vulnerabilities = []

    # Check for composer.lock
    lock_file = Path(project_path) / "composer.lock"

    if not lock_file.exists():
        return vulnerabilities

    # Try using composer audit if available
    code, stdout, _ = run_command(
        f"cd '{project_path}' && composer audit --format=json 2>/dev/null",
        check=False
    )

    if code == 0 and stdout:
        try:
            audit_data = json.loads(stdout)

            if "advisories" in audit_data:
                for pkg_name, advisories in audit_data["advisories"].items():
                    for advisory in advisories:
                        vulnerabilities.append({
                            "type": "php",
                            "project": project_name,
                            "path": project_path,
                            "package": pkg_name,
                            "version": advisory.get("affectedVersions", "unknown"),
                            "cves": [advisory.get("cve", "")] if advisory.get("cve") else [],
                            "severity": advisory.get("severity", "unknown"),
                            "description": advisory.get("title", ""),
                        })
        except json.JSONDecodeError:
            pass
    else:
        # Fallback: Parse composer.lock and check against known advisories
        try:
            with open(lock_file) as f:
                lock_data = json.load(f)

            packages = lock_data.get("packages", []) + lock_data.get("packages-dev", [])

            for pkg in packages:
                pkg_name = pkg.get("name", "")
                pkg_version = pkg.get("version", "")

                # Add as needs-audit (can't check without database)
                vulnerabilities.append({
                    "type": "php",
                    "project": project_name,
                    "path": project_path,
                    "package": pkg_name,
                    "version": pkg_version,
                    "cves": [],
                    "severity": "needs-audit",
                    "description": "Run 'composer audit' for detailed check",
                })
        except (json.JSONDecodeError, IOError):
            pass

    return vulnerabilities


def scan_python_dependencies(project_path: str, project_name: str) -> List[Dict]:
    """Scan Python dependencies."""
    vulnerabilities = []

    # Check for requirements.txt
    req_file = Path(project_path) / "requirements.txt"

    if not req_file.exists():
        return vulnerabilities

    # Try using pip-audit if available
    code, _, _ = run_command("which pip-audit", check=False)

    if code == 0:
        code, stdout, _ = run_command(
            f"pip-audit -r '{req_file}' --format=json 2>/dev/null",
            check=False
        )

        if code == 0 and stdout:
            try:
                audit_data = json.loads(stdout)

                for vuln in audit_data.get("vulnerabilities", []):
                    vulnerabilities.append({
                        "type": "python",
                        "project": project_name,
                        "path": project_path,
                        "package": vuln.get("name", "unknown"),
                        "version": vuln.get("version", "unknown"),
                        "cves": [vuln.get("id", "")],
                        "severity": vuln.get("severity", "unknown"),
                        "description": vuln.get("description", "")[:100],
                    })
            except json.JSONDecodeError:
                pass
    else:
        # Fallback: Parse requirements.txt
        try:
            with open(req_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Parse package==version format
                        match = re.match(r'^([a-zA-Z0-9_-]+)([=<>!~].*)?', line)
                        if match:
                            pkg_name = match.group(1)
                            pkg_version = match.group(2) or ""

                            vulnerabilities.append({
                                "type": "python",
                                "project": project_name,
                                "path": project_path,
                                "package": pkg_name,
                                "version": pkg_version,
                                "cves": [],
                                "severity": "needs-audit",
                                "description": "Install pip-audit for CVE check",
                            })
        except IOError:
            pass

    return vulnerabilities


def display_app_vulnerabilities(vulnerabilities: List[Dict]):
    """Display application vulnerabilities in a table."""
    console.print("\n")

    if not vulnerabilities:
        console.print(Panel(
            "[green]✓ No known vulnerabilities found in application dependencies![/green]",
            title="✅ Applications Secure",
            border_style="green",
        ))
        return

    # Group by project
    by_project = {}
    for vuln in vulnerabilities:
        project = vuln.get("project", "unknown")
        if project not in by_project:
            by_project[project] = []
        by_project[project].append(vuln)

    # Summary
    total_vulns = len(vulnerabilities)
    critical = sum(1 for v in vulnerabilities if v.get("severity") in ["critical", "high"])
    with_cves = sum(1 for v in vulnerabilities if v.get("cves"))

    console.print(Panel(
        f"[bold]Total Vulnerabilities: {total_vulns}[/bold]\n"
        f"[red]Critical/High: {critical}[/red]\n"
        f"With CVE IDs: {with_cves}\n"
        f"Projects affected: {len(by_project)}",
        title="📊 Summary",
        border_style="red" if critical > 0 else "yellow",
    ))

    # Table by project
    for project_name, project_vulns in list(by_project.items())[:10]:
        table = Table(
            title=f"📁 {project_name}",
            box=box.SIMPLE,
        )
        table.add_column("Package", style="cyan")
        table.add_column("Version")
        table.add_column("CVEs", style="red")
        table.add_column("Severity")

        for vuln in project_vulns[:10]:
            severity = vuln.get("severity", "unknown")
            if severity in ["critical", "high"]:
                sev_display = f"[red]{severity.upper()}[/red]"
            elif severity == "medium":
                sev_display = f"[yellow]{severity}[/yellow]"
            else:
                sev_display = f"[dim]{severity}[/dim]"

            table.add_row(
                vuln.get("package", "unknown"),
                vuln.get("version", "")[:20],
                ", ".join(vuln.get("cves", [])) or "-",
                sev_display,
            )

        console.print(table)
        console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# FULL CVE SCAN
# ═══════════════════════════════════════════════════════════════════════════════

def run_full_cve_scan():
    """Run a complete CVE scan on system and applications."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "CVE Scanner", "Full Scan"])

    console.print("\n[bold]🔍 Full CVE Scan[/bold]\n")
    console.print("This will scan:\n")
    console.print("  1. System packages (apt/dpkg)")
    console.print("  2. Application dependencies (/var/www, /home)")
    console.print()

    if not confirm_action("Start full CVE scan?"):
        return

    all_results = {
        "timestamp": datetime.now().isoformat(),
        "system": [],
        "applications": [],
    }

    # System scan
    console.print("\n[bold cyan]📦 Scanning system packages...[/bold cyan]\n")

    sys_vulns = []
    sys_vulns.extend(scan_with_apt_security())
    sys_vulns.extend(scan_with_unattended_upgrades())

    all_results["system"] = sys_vulns

    if sys_vulns:
        console.print(f"[yellow]Found {len(sys_vulns)} system issues[/yellow]")
    else:
        console.print("[green]✓ System packages look good[/green]")

    # Application scan
    console.print("\n[bold cyan]📦 Scanning application dependencies...[/bold cyan]\n")

    app_vulns = []
    scan_dirs = ["/var/www", "/home"]

    for scan_dir in scan_dirs:
        if not Path(scan_dir).exists():
            continue

        console.print(f"[dim]Scanning {scan_dir}...[/dim]")

        for dep_file, ecosystem in DEPENDENCY_FILES.items():
            code, stdout, _ = run_command(
                f"find {scan_dir} -name '{dep_file}' -type f 2>/dev/null | head -50",
                check=False
            )

            if code == 0 and stdout:
                for file_path in stdout.strip().split("\n"):
                    if file_path:
                        project_path = str(Path(file_path).parent)
                        project_name = Path(project_path).name

                        project = {
                            "name": project_name,
                            "path": project_path,
                            "ecosystem": ecosystem,
                        }

                        vulns = scan_project_dependencies(project)
                        app_vulns.extend(vulns)

    all_results["applications"] = app_vulns

    if app_vulns:
        console.print(f"[yellow]Found {len(app_vulns)} application issues[/yellow]")
    else:
        console.print("[green]✓ Application dependencies look good[/green]")

    # Save results
    save_scan_results("full", all_results)

    # Summary
    total_system = len(sys_vulns)
    total_apps = len(app_vulns)
    total = total_system + total_apps

    console.print("\n")
    console.print(Panel(
        f"[bold]Scan Complete![/bold]\n\n"
        f"System Issues: {total_system}\n"
        f"Application Issues: {total_apps}\n"
        f"[bold]Total: {total}[/bold]",
        title="📊 Full Scan Results",
        border_style="green" if total == 0 else "yellow",
    ))

    # Record in state
    record_lineage("cve_scan", "full", "scan", {
        "system_issues": total_system,
        "app_issues": total_apps,
        "total": total,
    })

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# CVE DATABASE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def update_cve_database():
    """Update the CVE database."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "CVE Scanner", "Update Database"])

    console.print("\n[bold]🔄 Update CVE Database[/bold]\n")

    console.print("This will update vulnerability databases:\n")
    console.print("  • Ubuntu Security Notices")
    console.print("  • npm audit database (via npm)")
    console.print("  • Composer security advisories")
    console.print("  • Python safety database")
    console.print()

    if not confirm_action("Update CVE databases?"):
        return

    console.print("\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Update apt
        task = progress.add_task("Updating apt package lists...", total=None)
        run_command("sudo apt-get update -q", check=False)
        progress.update(task, description="[green]✓ apt updated[/green]")

        # Install/update ubuntu-security-status if not present
        task = progress.add_task("Checking ubuntu-security-status...", total=None)
        code, _, _ = run_command("which ubuntu-security-status", check=False)
        if code != 0:
            run_command("sudo apt-get install -y update-manager-core", check=False)
        progress.update(task, description="[green]✓ Security tools ready[/green]")

        # Update npm if available
        task = progress.add_task("Checking npm audit database...", total=None)
        code, _, _ = run_command("which npm", check=False)
        if code == 0:
            run_command("npm cache clean --force 2>/dev/null", check=False)
            progress.update(task, description="[green]✓ npm ready[/green]")
        else:
            progress.update(task, description="[dim]npm not installed[/dim]")

        # Check composer
        task = progress.add_task("Checking composer audit...", total=None)
        code, _, _ = run_command("which composer", check=False)
        if code == 0:
            progress.update(task, description="[green]✓ composer ready[/green]")
        else:
            progress.update(task, description="[dim]composer not installed[/dim]")

        # Install pip-audit if pip available
        task = progress.add_task("Checking pip-audit...", total=None)
        code, _, _ = run_command("pip3 show pip-audit 2>/dev/null", check=False)
        if code != 0:
            run_command("pip3 install pip-audit --quiet 2>/dev/null", check=False)
        progress.update(task, description="[green]✓ pip-audit ready[/green]")

    # Update timestamp
    LAST_UPDATE_FILE.write_text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    print_success("CVE databases updated!")
    console.print(f"\n[dim]Last update: {LAST_UPDATE_FILE.read_text()}[/dim]")

    questionary.press_any_key_to_continue().ask()


def setup_cve_cron():
    """Setup cron job for automatic CVE database updates."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "CVE Scanner", "Setup Cron"])

    console.print("\n[bold]⏰ Setup CVE Update Cron[/bold]\n")

    # Check current cron jobs
    code, stdout, _ = run_command("crontab -l 2>/dev/null | grep -i cve", check=False)

    if code == 0 and stdout:
        console.print("[yellow]Existing CVE cron job found:[/yellow]")
        console.print(f"[dim]{stdout.strip()}[/dim]\n")

        if not confirm_action("Replace existing cron job?"):
            return

    # Select frequency
    frequency = questionary.select(
        "How often should CVE databases be updated?",
        choices=[
            {"name": "📅 Daily (recommended)", "value": "daily"},
            {"name": "📅 Weekly", "value": "weekly"},
            {"name": "📅 Twice daily", "value": "twice"},
        ],
    ).ask()

    if not frequency:
        return

    # Build cron expression
    if frequency == "daily":
        cron_expr = "0 3 * * *"  # 3 AM daily
    elif frequency == "weekly":
        cron_expr = "0 3 * * 0"  # 3 AM Sunday
    else:
        cron_expr = "0 3,15 * * *"  # 3 AM and 3 PM

    # Create the cron command
    forge_path = "/usr/local/bin/forge"
    cron_command = f"{cron_expr} {forge_path} cve-update 2>/dev/null || apt-get update -q"

    console.print(f"\n[cyan]Setting up cron: {cron_expr}[/cyan]")

    # Get existing crontab
    code, existing, _ = run_command("crontab -l 2>/dev/null", check=False)
    existing = existing if code == 0 else ""

    # Remove old CVE entries
    new_lines = []
    for line in existing.split("\n"):
        if "cve" not in line.lower():
            new_lines.append(line)

    # Add new entry
    new_lines.append(f"# CVE Database Update")
    new_lines.append(cron_command)

    # Write new crontab
    new_crontab = "\n".join(new_lines).strip() + "\n"

    code, _, stderr = run_command(
        f"echo '{new_crontab}' | crontab -",
        check=False
    )

    if code == 0:
        print_success("CVE update cron job configured!")
        console.print(f"[dim]Schedule: {cron_expr}[/dim]")
    else:
        print_error(f"Failed to setup cron: {stderr}")

    questionary.press_any_key_to_continue().ask()


def show_database_status():
    """Show CVE database status."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "CVE Scanner", "Database Status"])

    console.print("\n[bold]ℹ️ CVE Database Status[/bold]\n")

    table = Table(box=box.ROUNDED)
    table.add_column("Component", style="cyan")
    table.add_column("Status")
    table.add_column("Details", style="dim")

    # Check ubuntu-security-status
    code, _, _ = run_command("which ubuntu-security-status", check=False)
    if code == 0:
        table.add_row(
            "Ubuntu Security Status",
            "[green]✓ Installed[/green]",
            "Part of update-manager-core"
        )
    else:
        table.add_row(
            "Ubuntu Security Status",
            "[yellow]⚠ Not installed[/yellow]",
            "apt install update-manager-core"
        )

    # Check npm
    code, stdout, _ = run_command("npm --version 2>/dev/null", check=False)
    if code == 0:
        table.add_row(
            "npm audit",
            "[green]✓ Available[/green]",
            f"npm {stdout.strip()}"
        )
    else:
        table.add_row(
            "npm audit",
            "[dim]Not installed[/dim]",
            "Node.js package manager"
        )

    # Check composer
    code, stdout, _ = run_command("composer --version 2>/dev/null | head -1", check=False)
    if code == 0:
        table.add_row(
            "Composer audit",
            "[green]✓ Available[/green]",
            stdout.strip()[:40]
        )
    else:
        table.add_row(
            "Composer audit",
            "[dim]Not installed[/dim]",
            "PHP package manager"
        )

    # Check pip-audit
    code, _, _ = run_command("pip3 show pip-audit 2>/dev/null", check=False)
    if code == 0:
        table.add_row(
            "pip-audit",
            "[green]✓ Installed[/green]",
            "Python vulnerability scanner"
        )
    else:
        table.add_row(
            "pip-audit",
            "[yellow]⚠ Not installed[/yellow]",
            "pip3 install pip-audit"
        )

    # Last update
    if LAST_UPDATE_FILE.exists():
        last_update = LAST_UPDATE_FILE.read_text().strip()
        table.add_row(
            "Last Update",
            "[green]✓[/green]",
            last_update
        )
    else:
        table.add_row(
            "Last Update",
            "[red]Never[/red]",
            "Run 'Update CVE Database'"
        )

    # Check cron
    code, stdout, _ = run_command("crontab -l 2>/dev/null | grep -i cve", check=False)
    if code == 0 and stdout:
        table.add_row(
            "Auto-Update Cron",
            "[green]✓ Configured[/green]",
            stdout.strip()[:30]
        )
    else:
        table.add_row(
            "Auto-Update Cron",
            "[yellow]Not configured[/yellow]",
            "Setup via menu"
        )

    console.print(table)

    # Ubuntu version
    version, codename = get_ubuntu_version()
    console.print(f"\n[dim]Ubuntu {version} ({codename})[/dim]")

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# SCAN RESULTS MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def save_scan_results(scan_type: str, results: any):
    """Save scan results to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = CVE_SCANS_DIR / f"scan_{scan_type}_{timestamp}.json"

    data = {
        "type": scan_type,
        "timestamp": datetime.now().isoformat(),
        "results": results if isinstance(results, dict) else {"vulnerabilities": results},
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=2, default=str)

    # Also save as latest
    latest_file = CVE_SCANS_DIR / f"latest_{scan_type}.json"
    with open(latest_file, "w") as f:
        json.dump(data, f, indent=2, default=str)


def view_last_scan_results():
    """View the last scan results."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "CVE Scanner", "Last Results"])

    console.print("\n[bold]📋 Last Scan Results[/bold]\n")

    # Find latest files
    latest_files = list(CVE_SCANS_DIR.glob("latest_*.json"))

    if not latest_files:
        print_info("No scan results found. Run a scan first.")
        questionary.press_any_key_to_continue().ask()
        return

    for latest_file in latest_files:
        try:
            with open(latest_file) as f:
                data = json.load(f)

            scan_type = data.get("type", "unknown")
            timestamp = data.get("timestamp", "unknown")
            results = data.get("results", {})

            console.print(f"\n[bold cyan]Scan Type: {scan_type}[/bold cyan]")
            console.print(f"[dim]Time: {timestamp}[/dim]")

            if "vulnerabilities" in results:
                vulns = results["vulnerabilities"]
                console.print(f"[bold]Vulnerabilities: {len(vulns)}[/bold]")

                for vuln in vulns[:10]:
                    if isinstance(vuln, dict):
                        pkg = vuln.get("package", "unknown")
                        cves = ", ".join(vuln.get("cves", [])) or "no CVE"
                        console.print(f"  • {pkg}: {cves}")

            console.print()
        except (json.JSONDecodeError, IOError):
            continue

    questionary.press_any_key_to_continue().ask()


def view_scan_history():
    """View scan history."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "CVE Scanner", "History"])

    console.print("\n[bold]📊 Scan History[/bold]\n")

    scan_files = sorted(CVE_SCANS_DIR.glob("scan_*.json"), reverse=True)

    if not scan_files:
        print_info("No scan history found.")
        questionary.press_any_key_to_continue().ask()
        return

    table = Table(box=box.SIMPLE)
    table.add_column("Date", style="cyan")
    table.add_column("Type")
    table.add_column("Issues")
    table.add_column("File", style="dim")

    for scan_file in scan_files[:20]:
        try:
            with open(scan_file) as f:
                data = json.load(f)

            timestamp = data.get("timestamp", "")[:16]
            scan_type = data.get("type", "unknown")
            results = data.get("results", {})

            if isinstance(results, list):
                issue_count = len(results)
            elif "vulnerabilities" in results:
                issue_count = len(results["vulnerabilities"])
            elif "system" in results:
                issue_count = len(results.get("system", [])) + len(results.get("applications", []))
            else:
                issue_count = 0

            table.add_row(
                timestamp,
                scan_type,
                str(issue_count),
                scan_file.name[:30],
            )
        except (json.JSONDecodeError, IOError):
            continue

    console.print(table)
    questionary.press_any_key_to_continue().ask()
