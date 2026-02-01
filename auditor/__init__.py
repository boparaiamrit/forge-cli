"""
Configuration Auditor - Analyze and optimize server configurations
"""

import os
import re
import questionary
from typing import Dict, List, Optional, Tuple
from pathlib import Path
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
# AUDIT DEFINITIONS - Best practice configurations
# ═══════════════════════════════════════════════════════════════════════════════

# Nginx security headers that should be present
NGINX_SECURITY_HEADERS = {
    "X-Frame-Options": {
        "value": "SAMEORIGIN",
        "directive": 'add_header X-Frame-Options "SAMEORIGIN" always;',
        "description": "Prevents clickjacking attacks",
        "severity": "high",
    },
    "X-Content-Type-Options": {
        "value": "nosniff",
        "directive": 'add_header X-Content-Type-Options "nosniff" always;',
        "description": "Prevents MIME-type sniffing",
        "severity": "high",
    },
    "X-XSS-Protection": {
        "value": "1; mode=block",
        "directive": 'add_header X-XSS-Protection "1; mode=block" always;',
        "description": "Enables XSS filtering",
        "severity": "medium",
    },
    "Referrer-Policy": {
        "value": "strict-origin-when-cross-origin",
        "directive": 'add_header Referrer-Policy "strict-origin-when-cross-origin" always;',
        "description": "Controls referrer information",
        "severity": "medium",
    },
    "Content-Security-Policy": {
        "value": "default-src 'self'",
        "directive": "add_header Content-Security-Policy \"default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;\" always;",
        "description": "Defines content loading policy",
        "severity": "medium",
    },
    "Permissions-Policy": {
        "value": "geolocation=(), microphone=(), camera=()",
        "directive": 'add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;',
        "description": "Controls browser features",
        "severity": "low",
    },
}

# Nginx optimization settings
NGINX_OPTIMIZATIONS = {
    "gzip": {
        "check": "gzip on",
        "directive": """    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/rss+xml application/atom+xml image/svg+xml;""",
        "description": "Enable gzip compression",
        "severity": "medium",
    },
    "client_max_body_size": {
        "check": "client_max_body_size",
        "directive": "    client_max_body_size 100M;",
        "description": "Allow large file uploads",
        "default": "1M",
        "recommended": "100M",
        "severity": "low",
    },
    "proxy_buffers": {
        "check": "proxy_buffer_size",
        "directive": """    proxy_buffer_size 128k;
    proxy_buffers 4 256k;
    proxy_busy_buffers_size 256k;""",
        "description": "Optimize proxy buffering",
        "severity": "low",
    },
    "timeouts": {
        "check": "proxy_read_timeout",
        "directive": """    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;""",
        "description": "Proper timeout settings",
        "severity": "low",
    },
}

# PHP recommended production settings
PHP_RECOMMENDED_SETTINGS = {
    "memory_limit": {
        "min": "256M",
        "recommended": "512M",
        "description": "PHP memory limit",
        "severity": "medium",
    },
    "upload_max_filesize": {
        "min": "10M",
        "recommended": "100M",
        "description": "Maximum upload file size",
        "severity": "low",
    },
    "post_max_size": {
        "min": "10M",
        "recommended": "100M",
        "description": "Maximum POST data size",
        "severity": "low",
    },
    "max_execution_time": {
        "min": "60",
        "recommended": "300",
        "description": "Maximum script execution time",
        "severity": "low",
    },
    "max_input_vars": {
        "min": "1000",
        "recommended": "3000",
        "description": "Maximum input variables",
        "severity": "low",
    },
    "opcache.enable": {
        "min": "1",
        "recommended": "1",
        "description": "Enable OPcache",
        "severity": "high",
    },
    "opcache.memory_consumption": {
        "min": "64",
        "recommended": "256",
        "description": "OPcache memory",
        "severity": "medium",
    },
    "expose_php": {
        "min": "Off",
        "recommended": "Off",
        "description": "Hide PHP version",
        "severity": "medium",
    },
    "display_errors": {
        "min": "Off",
        "recommended": "Off",
        "description": "Hide errors in production",
        "severity": "high",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT MENU
# ═══════════════════════════════════════════════════════════════════════════════

AUDITOR_MENU_CHOICES = [
    {"name": "🔍 Audit All Configurations", "value": "audit_all"},
    questionary.Separator("─" * 30),
    {"name": "🌐 Audit Nginx Sites", "value": "audit_nginx"},
    {"name": "🐘 Audit PHP Configuration", "value": "audit_php"},
    {"name": "⚙️ Audit Services", "value": "audit_services"},
    {"name": "🔒 Audit Security", "value": "audit_security"},
    questionary.Separator("─" * 30),
    {"name": "🛠️ Quick Fix All Issues", "value": "fix_all"},
    {"name": "⬅️ Back", "value": "back"},
]


def run_auditor_menu():
    """Display the configuration auditor menu."""
    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "Configuration Auditor"])

        choice = questionary.select(
            "Configuration Auditor:",
            choices=AUDITOR_MENU_CHOICES,
            qmark="🔍",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "audit_all":
            audit_all_configurations()
        elif choice == "audit_nginx":
            audit_nginx_sites()
        elif choice == "audit_php":
            audit_php_configuration()
        elif choice == "audit_services":
            audit_services()
        elif choice == "audit_security":
            audit_security_configuration()
        elif choice == "fix_all":
            fix_all_issues()


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT ALL
# ═══════════════════════════════════════════════════════════════════════════════

def audit_all_configurations():
    """Run all audits and show summary."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Auditor", "Full Audit"])

    console.print("\n[bold]🔍 Full Configuration Audit[/bold]\n")
    console.print("[cyan]Analyzing configurations...[/cyan]\n")

    # Collect all issues
    all_issues = []

    # Nginx audit
    nginx_issues = run_nginx_audit(silent=True)
    all_issues.extend([("Nginx", i) for i in nginx_issues])

    # PHP audit
    php_issues = run_php_audit(silent=True)
    all_issues.extend([("PHP", i) for i in php_issues])

    # Services audit
    service_issues = run_services_audit(silent=True)
    all_issues.extend([("Services", i) for i in service_issues])

    # Security audit
    security_issues = run_security_audit(silent=True)
    all_issues.extend([("Security", i) for i in security_issues])

    # Show summary
    if not all_issues:
        console.print(Panel(
            "[green]✓ All configurations are optimized![/green]\n\n"
            "No issues found across:\n"
            "• Nginx site configurations\n"
            "• PHP settings\n"
            "• Service configurations\n"
            "• Security settings",
            title="✅ Audit Complete",
            border_style="green",
        ))
    else:
        # Group by category
        by_category = {}
        for category, issue in all_issues:
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(issue)

        table = Table(
            title="🔍 Issues Found",
            box=box.ROUNDED,
            header_style="bold red",
        )
        table.add_column("Category", style="cyan")
        table.add_column("Issue", style="white")
        table.add_column("Severity", justify="center")
        table.add_column("Fixable", justify="center")

        for category, issues in by_category.items():
            for issue in issues[:5]:  # Limit per category
                severity = issue.get("severity", "low")
                if severity == "high":
                    sev_display = "[red]HIGH[/red]"
                elif severity == "medium":
                    sev_display = "[yellow]MEDIUM[/yellow]"
                else:
                    sev_display = "[dim]LOW[/dim]"

                fixable = "[green]✓[/green]" if issue.get("fixable") else "[dim]✗[/dim]"
                table.add_row(category, issue.get("description", "Unknown"), sev_display, fixable)

        console.print(table)
        console.print(f"\n[bold]Total issues found: {len(all_issues)}[/bold]")

        # Offer to fix
        fixable_count = sum(1 for _, i in all_issues if i.get("fixable"))
        if fixable_count > 0:
            console.print(f"[green]{fixable_count} issues can be automatically fixed[/green]\n")

            if confirm_action(f"Fix all {fixable_count} fixable issues?"):
                fix_issues(all_issues)

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# NGINX AUDIT
# ═══════════════════════════════════════════════════════════════════════════════

def audit_nginx_sites():
    """Audit Nginx site configurations."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Auditor", "Nginx"])

    console.print("\n[bold]🌐 Nginx Site Audit[/bold]\n")

    issues = run_nginx_audit(silent=False)

    if not issues:
        print_success("All Nginx sites are properly configured!")
    else:
        # Offer to fix
        fixable = [i for i in issues if i.get("fixable")]
        if fixable:
            console.print(f"\n[green]{len(fixable)} issues can be automatically fixed[/green]\n")

            if confirm_action("Fix all fixable issues?"):
                fix_nginx_issues(fixable)

    questionary.press_any_key_to_continue().ask()


def run_nginx_audit(silent: bool = False) -> List[Dict]:
    """Run Nginx configuration audit."""
    issues = []
    sites_available = Path("/etc/nginx/sites-available")
    sites_enabled = Path("/etc/nginx/sites-enabled")

    if not sites_enabled.exists():
        if not silent:
            print_warning("Nginx sites-enabled directory not found")
        return issues

    # Get enabled sites
    enabled_sites = []
    for site in sites_enabled.iterdir():
        if site.name != "default":
            enabled_sites.append(site.name)

    if not silent:
        console.print(f"[dim]Found {len(enabled_sites)} enabled sites[/dim]\n")

    for site_name in enabled_sites:
        config_path = sites_available / site_name

        if not config_path.exists():
            config_path = sites_enabled / site_name

        if not config_path.exists():
            continue

        site_issues = audit_nginx_config(config_path, site_name, silent)
        issues.extend(site_issues)

    return issues


def audit_nginx_config(config_path: Path, site_name: str, silent: bool = False) -> List[Dict]:
    """Audit a single Nginx configuration file."""
    issues = []

    # Read config
    code, content, _ = run_command(f"sudo cat {config_path}", check=False)
    if code != 0:
        return issues

    if not silent:
        console.print(f"[bold cyan]Site: {site_name}[/bold cyan]")

    # Check security headers
    missing_headers = []
    for header, info in NGINX_SECURITY_HEADERS.items():
        if header.lower() not in content.lower():
            missing_headers.append(header)
            issues.append({
                "type": "nginx_header",
                "site": site_name,
                "config_path": str(config_path),
                "header": header,
                "directive": info["directive"],
                "description": f"Missing {header} header ({info['description']})",
                "severity": info["severity"],
                "fixable": True,
            })

    # Check optimizations
    missing_opts = []
    for opt_name, opt_info in NGINX_OPTIMIZATIONS.items():
        if opt_info["check"].lower() not in content.lower():
            missing_opts.append(opt_name)
            issues.append({
                "type": "nginx_optimization",
                "site": site_name,
                "config_path": str(config_path),
                "optimization": opt_name,
                "directive": opt_info["directive"],
                "description": f"Missing {opt_info['description']}",
                "severity": opt_info["severity"],
                "fixable": True,
            })

    # Check SSL
    has_ssl = "ssl_certificate" in content.lower()
    if not has_ssl and "listen 443" in content:
        issues.append({
            "type": "nginx_ssl",
            "site": site_name,
            "config_path": str(config_path),
            "description": "SSL listener without certificate configured",
            "severity": "high",
            "fixable": False,
        })

    if not silent:
        if missing_headers:
            console.print(f"  [red]✗ Missing security headers:[/red] {', '.join(missing_headers)}")
        else:
            console.print(f"  [green]✓ All security headers present[/green]")

        if missing_opts:
            console.print(f"  [yellow]⚠ Missing optimizations:[/yellow] {', '.join(missing_opts)}")
        else:
            console.print(f"  [green]✓ All optimizations present[/green]")

        console.print()

    return issues


def fix_nginx_issues(issues: List[Dict]):
    """Fix Nginx configuration issues."""
    # Group by site
    by_site = {}
    for issue in issues:
        site = issue.get("config_path")
        if site not in by_site:
            by_site[site] = []
        by_site[site].append(issue)

    for config_path, site_issues in by_site.items():
        site_name = site_issues[0].get("site", "unknown")
        console.print(f"\n[cyan]Fixing {site_name}...[/cyan]")

        # Read current config
        code, content, _ = run_command(f"sudo cat {config_path}", check=False)
        if code != 0:
            print_error(f"Cannot read {config_path}")
            continue

        # Find location to insert (inside server block, after listen)
        lines = content.split("\n")
        insert_index = -1

        for i, line in enumerate(lines):
            if "server_name" in line:
                insert_index = i + 1
                break

        if insert_index == -1:
            print_warning(f"Could not find insertion point in {site_name}")
            continue

        # Build insertions
        insertions = []
        for issue in site_issues:
            if issue.get("type") in ["nginx_header", "nginx_optimization"]:
                directive = issue.get("directive", "")
                if directive and directive not in content:
                    insertions.append(f"    {directive.strip()}")

        if insertions:
            # Insert directives
            new_lines = lines[:insert_index] + insertions + lines[insert_index:]
            new_content = "\n".join(new_lines)

            # Write back
            escaped_content = new_content.replace("'", "'\\''")
            code, _, stderr = run_command(
                f"echo '{escaped_content}' | sudo tee {config_path} > /dev/null",
                check=False
            )

            if code == 0:
                print_success(f"Fixed {len(insertions)} issues in {site_name}")
            else:
                print_error(f"Failed to update {site_name}: {stderr}")

    # Test and reload Nginx
    console.print("\n[cyan]Testing Nginx configuration...[/cyan]")
    code, stdout, stderr = run_command("sudo nginx -t", check=False)

    if code == 0:
        run_command("sudo systemctl reload nginx", check=False)
        print_success("Nginx configuration updated and reloaded!")
    else:
        print_error(f"Nginx configuration test failed: {stderr}")
        print_warning("Please check and fix manually")


# ═══════════════════════════════════════════════════════════════════════════════
# PHP AUDIT
# ═══════════════════════════════════════════════════════════════════════════════

def audit_php_configuration():
    """Audit PHP configuration."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Auditor", "PHP"])

    console.print("\n[bold]🐘 PHP Configuration Audit[/bold]\n")

    issues = run_php_audit(silent=False)

    if not issues:
        print_success("All PHP configurations are optimized!")
    else:
        fixable = [i for i in issues if i.get("fixable")]
        if fixable:
            console.print(f"\n[green]{len(fixable)} issues can be automatically fixed[/green]\n")

            if confirm_action("Fix all fixable issues?"):
                fix_php_issues(fixable)

    questionary.press_any_key_to_continue().ask()


def run_php_audit(silent: bool = False) -> List[Dict]:
    """Run PHP configuration audit."""
    issues = []

    # Find installed PHP versions
    php_versions = []
    for version in ["8.5", "8.4", "8.3", "8.2", "8.1", "8.0", "7.4"]:
        code, _, _ = run_command(f"php{version} -v 2>/dev/null", check=False)
        if code == 0:
            php_versions.append(version)

    if not php_versions:
        if not silent:
            print_warning("No PHP installations found")
        return issues

    if not silent:
        console.print(f"[dim]Found PHP versions: {', '.join(php_versions)}[/dim]\n")

    for version in php_versions:
        version_issues = audit_php_version(version, silent)
        issues.extend(version_issues)

    return issues


def audit_php_version(version: str, silent: bool = False) -> List[Dict]:
    """Audit a specific PHP version configuration."""
    issues = []

    if not silent:
        console.print(f"[bold cyan]PHP {version}:[/bold cyan]")

    for setting, info in PHP_RECOMMENDED_SETTINGS.items():
        # Get current value
        code, stdout, _ = run_command(
            f"php{version} -i 2>/dev/null | grep '^{setting}' | head -1",
            check=False
        )

        if code != 0 or not stdout:
            continue

        parts = stdout.split("=>")
        current_value = parts[-1].strip() if len(parts) >= 2 else "unknown"

        # Compare with recommended
        recommended = info["recommended"]
        is_issue = False

        # Compare values (handle units like M for memory)
        current_num = parse_php_value(current_value)
        recommended_num = parse_php_value(recommended)
        min_num = parse_php_value(info["min"])

        if current_num is not None and min_num is not None:
            if current_num < min_num:
                is_issue = True

        # Special checks for On/Off values
        if recommended.lower() in ["on", "off", "1", "0"]:
            if current_value.lower() != recommended.lower() and current_value != recommended:
                is_issue = True

        if is_issue:
            issues.append({
                "type": "php_setting",
                "version": version,
                "setting": setting,
                "current": current_value,
                "recommended": recommended,
                "description": f"{info['description']}: {current_value} (recommended: {recommended})",
                "severity": info["severity"],
                "fixable": True,
            })

            if not silent:
                console.print(f"  [yellow]⚠ {setting}:[/yellow] {current_value} → {recommended}")
        elif not silent and setting in ["opcache.enable", "memory_limit"]:
            console.print(f"  [green]✓ {setting}:[/green] {current_value}")

    if not silent:
        console.print()

    return issues


def parse_php_value(value: str) -> Optional[int]:
    """Parse PHP value with units (like 128M) to bytes."""
    if value is None:
        return None

    value = value.strip().upper()

    if value in ["ON", "1", "TRUE"]:
        return 1
    if value in ["OFF", "0", "FALSE", "NONE"]:
        return 0

    try:
        if value.endswith("G"):
            return int(value[:-1]) * 1024 * 1024 * 1024
        elif value.endswith("M"):
            return int(value[:-1]) * 1024 * 1024
        elif value.endswith("K"):
            return int(value[:-1]) * 1024
        else:
            return int(value)
    except ValueError:
        return None


def fix_php_issues(issues: List[Dict]):
    """Fix PHP configuration issues."""
    # Group by version
    by_version = {}
    for issue in issues:
        version = issue.get("version")
        if version not in by_version:
            by_version[version] = []
        by_version[version].append(issue)

    for version, version_issues in by_version.items():
        console.print(f"\n[cyan]Fixing PHP {version}...[/cyan]")

        ini_file = f"/etc/php/{version}/fpm/php.ini"

        for issue in version_issues:
            setting = issue.get("setting")
            recommended = issue.get("recommended")

            # Use sed to replace
            code, _, _ = run_command(
                f"sudo sed -i 's/^{setting} = .*/{setting} = {recommended}/' {ini_file}",
                check=False
            )

            if code == 0:
                console.print(f"  [green]✓[/green] Set {setting} = {recommended}")
            else:
                console.print(f"  [red]✗[/red] Failed to set {setting}")

        # Restart PHP-FPM
        code, _, _ = run_command(f"sudo systemctl restart php{version}-fpm", check=False)
        if code == 0:
            print_success(f"PHP {version}-fpm restarted")


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICES AUDIT
# ═══════════════════════════════════════════════════════════════════════════════

def audit_services():
    """Audit service configurations."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Auditor", "Services"])

    console.print("\n[bold]⚙️ Services Audit[/bold]\n")

    issues = run_services_audit(silent=False)

    if not issues:
        print_success("All services are properly configured!")
    else:
        fixable = [i for i in issues if i.get("fixable")]
        if fixable:
            console.print(f"\n[green]{len(fixable)} issues can be automatically fixed[/green]\n")

            if confirm_action("Fix all fixable issues?"):
                fix_service_issues(fixable)

    questionary.press_any_key_to_continue().ask()


def run_services_audit(silent: bool = False) -> List[Dict]:
    """Run services audit."""
    issues = []

    # Critical services that should be running
    critical_services = [
        ("nginx", "Web server"),
        ("cron", "Scheduled tasks"),
        ("ssh", "SSH access"),
    ]

    # Services that should be enabled on boot
    boot_services = [
        ("nginx", "Web server"),
        ("mysql", "MySQL database"),
        ("postgresql", "PostgreSQL database"),
        ("redis-server", "Redis cache"),
    ]

    if not silent:
        console.print("[bold]Critical Services:[/bold]")

    for service, description in critical_services:
        code, stdout, _ = run_command(f"systemctl is-active {service}", check=False)
        is_running = stdout.strip() == "active"

        # Check if service exists
        code2, _, _ = run_command(f"systemctl list-unit-files {service}.service | grep -q {service}", check=False)
        exists = code2 == 0

        if exists and not is_running:
            issues.append({
                "type": "service_not_running",
                "service": service,
                "description": f"{description} is not running",
                "severity": "high",
                "fixable": True,
            })
            if not silent:
                console.print(f"  [red]✗ {service}:[/red] Not running")
        elif exists and not silent:
            console.print(f"  [green]✓ {service}:[/green] Running")

    if not silent:
        console.print("\n[bold]Boot-Enabled Services:[/bold]")

    for service, description in boot_services:
        code, stdout, _ = run_command(f"systemctl is-enabled {service}", check=False)
        is_enabled = stdout.strip() == "enabled"

        # Check if service exists
        code2, _, _ = run_command(f"systemctl list-unit-files {service}.service | grep -q {service}", check=False)
        exists = code2 == 0

        if exists and not is_enabled:
            issues.append({
                "type": "service_not_enabled",
                "service": service,
                "description": f"{description} not enabled on boot",
                "severity": "medium",
                "fixable": True,
            })
            if not silent:
                console.print(f"  [yellow]⚠ {service}:[/yellow] Not enabled on boot")
        elif exists and not silent:
            console.print(f"  [green]✓ {service}:[/green] Enabled")

    if not silent:
        console.print()

    return issues


def fix_service_issues(issues: List[Dict]):
    """Fix service issues."""
    for issue in issues:
        service = issue.get("service")
        issue_type = issue.get("type")

        if issue_type == "service_not_running":
            console.print(f"[cyan]Starting {service}...[/cyan]")
            code, _, stderr = run_command(f"sudo systemctl start {service}", check=False)
            if code == 0:
                print_success(f"{service} started")
            else:
                print_error(f"Failed to start {service}: {stderr}")

        elif issue_type == "service_not_enabled":
            console.print(f"[cyan]Enabling {service} on boot...[/cyan]")
            code, _, stderr = run_command(f"sudo systemctl enable {service}", check=False)
            if code == 0:
                print_success(f"{service} enabled on boot")
            else:
                print_error(f"Failed to enable {service}: {stderr}")


# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY AUDIT
# ═══════════════════════════════════════════════════════════════════════════════

def audit_security_configuration():
    """Audit security configuration."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Auditor", "Security"])

    console.print("\n[bold]🔒 Security Audit[/bold]\n")

    issues = run_security_audit(silent=False)

    if not issues:
        print_success("All security configurations are optimal!")
    else:
        fixable = [i for i in issues if i.get("fixable")]
        if fixable:
            console.print(f"\n[green]{len(fixable)} issues can be automatically fixed[/green]\n")

            if confirm_action("Fix all fixable issues?"):
                fix_security_issues(fixable)

    questionary.press_any_key_to_continue().ask()


def run_security_audit(silent: bool = False) -> List[Dict]:
    """Run security audit."""
    issues = []

    # Check UFW (firewall)
    if not silent:
        console.print("[bold]Firewall:[/bold]")

    code, stdout, _ = run_command("sudo ufw status", check=False)
    if "inactive" in stdout.lower():
        issues.append({
            "type": "security_firewall",
            "description": "UFW firewall is inactive",
            "severity": "high",
            "fixable": True,
        })
        if not silent:
            console.print("  [red]✗ UFW:[/red] Inactive")
    elif code == 0 and not silent:
        console.print("  [green]✓ UFW:[/green] Active")
    elif code != 0:
        issues.append({
            "type": "security_firewall_missing",
            "description": "UFW firewall is not installed",
            "severity": "high",
            "fixable": True,
        })
        if not silent:
            console.print("  [red]✗ UFW:[/red] Not installed")

    # Check Fail2ban
    if not silent:
        console.print("\n[bold]Intrusion Prevention:[/bold]")

    code, stdout, _ = run_command("systemctl is-active fail2ban", check=False)
    if stdout.strip() != "active":
        code2, _, _ = run_command("which fail2ban-server", check=False)
        if code2 != 0:
            issues.append({
                "type": "security_fail2ban_missing",
                "description": "Fail2ban is not installed",
                "severity": "high",
                "fixable": True,
            })
            if not silent:
                console.print("  [red]✗ Fail2ban:[/red] Not installed")
        else:
            issues.append({
                "type": "security_fail2ban",
                "description": "Fail2ban is not running",
                "severity": "high",
                "fixable": True,
            })
            if not silent:
                console.print("  [yellow]⚠ Fail2ban:[/yellow] Not running")
    elif not silent:
        console.print("  [green]✓ Fail2ban:[/green] Active")

    # Check SSH configuration
    if not silent:
        console.print("\n[bold]SSH Security:[/bold]")

    code, stdout, _ = run_command("sudo grep '^PermitRootLogin' /etc/ssh/sshd_config", check=False)
    if "yes" in stdout.lower():
        issues.append({
            "type": "security_ssh_root",
            "description": "SSH root login is enabled",
            "severity": "high",
            "fixable": True,
        })
        if not silent:
            console.print("  [red]✗ Root Login:[/red] Enabled (should be disabled)")
    elif not silent:
        console.print("  [green]✓ Root Login:[/green] Disabled or key-only")

    code, stdout, _ = run_command("sudo grep '^PasswordAuthentication' /etc/ssh/sshd_config", check=False)
    if "yes" in stdout.lower():
        issues.append({
            "type": "security_ssh_password",
            "description": "SSH password authentication enabled",
            "severity": "medium",
            "fixable": False,  # User should decide
        })
        if not silent:
            console.print("  [yellow]⚠ Password Auth:[/yellow] Enabled (consider key-only)")
    elif not silent:
        console.print("  [green]✓ Password Auth:[/green] Disabled")

    if not silent:
        console.print()

    return issues


def fix_security_issues(issues: List[Dict]):
    """Fix security issues."""
    for issue in issues:
        issue_type = issue.get("type")

        if issue_type == "security_firewall":
            console.print("[cyan]Enabling UFW firewall...[/cyan]")
            # Enable SSH first to avoid lockout
            run_command("sudo ufw allow ssh", check=False)
            run_command("sudo ufw allow http", check=False)
            run_command("sudo ufw allow https", check=False)
            code, _, _ = run_command("echo 'y' | sudo ufw enable", check=False)
            if code == 0:
                print_success("UFW firewall enabled")

        elif issue_type == "security_firewall_missing":
            console.print("[cyan]Installing UFW firewall...[/cyan]")
            run_command("sudo apt-get install -y ufw", check=False)
            run_command("sudo ufw allow ssh", check=False)
            run_command("sudo ufw allow http", check=False)
            run_command("sudo ufw allow https", check=False)
            run_command("echo 'y' | sudo ufw enable", check=False)
            print_success("UFW installed and enabled")

        elif issue_type == "security_fail2ban_missing":
            console.print("[cyan]Installing Fail2ban...[/cyan]")
            code, _, _ = run_command("sudo apt-get install -y fail2ban", check=False)
            if code == 0:
                run_command("sudo systemctl enable fail2ban", check=False)
                run_command("sudo systemctl start fail2ban", check=False)
                print_success("Fail2ban installed and started")

        elif issue_type == "security_fail2ban":
            console.print("[cyan]Starting Fail2ban...[/cyan]")
            code, _, _ = run_command("sudo systemctl start fail2ban", check=False)
            if code == 0:
                print_success("Fail2ban started")

        elif issue_type == "security_ssh_root":
            console.print("[cyan]Disabling SSH root login...[/cyan]")
            run_command(
                "sudo sed -i 's/^PermitRootLogin yes/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config",
                check=False
            )
            run_command("sudo systemctl reload sshd", check=False)
            print_success("SSH root login disabled")


# ═══════════════════════════════════════════════════════════════════════════════
# FIX ALL
# ═══════════════════════════════════════════════════════════════════════════════

def fix_all_issues():
    """Fix all detected issues."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Auditor", "Fix All"])

    console.print("\n[bold]🛠️ Fix All Issues[/bold]\n")
    console.print("[cyan]Scanning for issues...[/cyan]\n")

    # Collect all issues
    all_issues = []

    nginx_issues = run_nginx_audit(silent=True)
    all_issues.extend([("Nginx", i) for i in nginx_issues])

    php_issues = run_php_audit(silent=True)
    all_issues.extend([("PHP", i) for i in php_issues])

    service_issues = run_services_audit(silent=True)
    all_issues.extend([("Services", i) for i in service_issues])

    security_issues = run_security_audit(silent=True)
    all_issues.extend([("Security", i) for i in security_issues])

    fixable = [(cat, i) for cat, i in all_issues if i.get("fixable")]

    if not fixable:
        print_success("No fixable issues found! Everything is optimized.")
        questionary.press_any_key_to_continue().ask()
        return

    # Show what will be fixed
    console.print(f"[bold]Found {len(fixable)} fixable issues:[/bold]\n")

    for category, issue in fixable:
        console.print(f"  • [{category}] {issue.get('description')}")

    console.print()

    if not confirm_action(f"Fix all {len(fixable)} issues?"):
        return

    # Fix issues
    fix_issues(all_issues)

    print_success("All fixable issues have been addressed!")
    questionary.press_any_key_to_continue().ask()


def fix_issues(all_issues: List[Tuple[str, Dict]]):
    """Fix all issues by category."""
    nginx_issues = [i for cat, i in all_issues if cat == "Nginx" and i.get("fixable")]
    php_issues = [i for cat, i in all_issues if cat == "PHP" and i.get("fixable")]
    service_issues = [i for cat, i in all_issues if cat == "Services" and i.get("fixable")]
    security_issues = [i for cat, i in all_issues if cat == "Security" and i.get("fixable")]

    if nginx_issues:
        console.print("\n[bold cyan]Fixing Nginx issues...[/bold cyan]")
        fix_nginx_issues(nginx_issues)

    if php_issues:
        console.print("\n[bold cyan]Fixing PHP issues...[/bold cyan]")
        fix_php_issues(php_issues)

    if service_issues:
        console.print("\n[bold cyan]Fixing Service issues...[/bold cyan]")
        fix_service_issues(service_issues)

    if security_issues:
        console.print("\n[bold cyan]Fixing Security issues...[/bold cyan]")
        fix_security_issues(security_issues)
