"""
Site Management - Create and manage Nginx sites with hardened configurations
"""

import os
import questionary
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, print_warning, print_info, confirm_action
)
from utils.shell import run_command, get_command_output
from nginx.templates import render_template, get_template_types
from state import (
    save_site_state, delete_site_state, list_sites_state,
    update_site_ssl, check_ssl_status, get_site_state
)

console = Console()

SITES_AVAILABLE = "/etc/nginx/sites-available"
SITES_ENABLED = "/etc/nginx/sites-enabled"

# ═══════════════════════════════════════════════════════════════════════════════
# SITES MENU
# ═══════════════════════════════════════════════════════════════════════════════

SITES_MENU_CHOICES = [
    {"name": "📋  List Sites", "value": "list"},
    {"name": "➕  Create Site", "value": "create"},
    {"name": "🔒  Provision SSL", "value": "ssl"},
    {"name": "📜  View Site Logs", "value": "logs"},
    {"name": "👁️   View Configuration", "value": "view_config"},
    {"name": "🏥  Health Check", "value": "health"},
    questionary.Separator("─" * 30),
    {"name": "🔄  Enable/Disable Site", "value": "toggle"},
    {"name": "🗑️   Delete Site", "value": "delete"},
    questionary.Separator("─" * 30),
    {"name": "⬅️   Back", "value": "back"},
]


def run_sites_menu():
    """Display the sites management menu."""
    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "Manage Sites"])

        choice = questionary.select(
            "Site Management:",
            choices=SITES_MENU_CHOICES,
            qmark="🌐",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "list":
            list_sites()
        elif choice == "create":
            create_site()
        elif choice == "ssl":
            provision_ssl_for_site()
        elif choice == "logs":
            view_site_logs()
        elif choice == "view_config":
            view_site_config()
        elif choice == "health":
            check_site_health()
        elif choice == "delete":
            delete_site()
        elif choice == "toggle":
            toggle_site()


# ═══════════════════════════════════════════════════════════════════════════════
# LIST SITES
# ═══════════════════════════════════════════════════════════════════════════════

def list_sites():
    """List all Nginx sites with SSL status and type."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Manage Sites", "List"])

    # Get available sites
    code, stdout, _ = run_command(f"ls {SITES_AVAILABLE}", check=False)
    available = [s for s in stdout.split() if s != "default"] if code == 0 else []

    # Get enabled sites
    code, stdout, _ = run_command(f"ls {SITES_ENABLED}", check=False)
    enabled = stdout.split() if code == 0 else []

    if not available:
        print_warning("No sites found.")
        console.print()

        if confirm_action("Would you like to create a new site?"):
            create_site()
            return
    else:
        table = Table(
            title="🌐 Nginx Sites",
            box=box.ROUNDED,
            header_style="bold magenta",
        )
        table.add_column("Site", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("SSL", justify="center")
        table.add_column("Type", justify="center")
        table.add_column("Port/Root", style="dim")

        for site in available:
            # Enabled status
            enabled_status = "🟢 Enabled" if site in enabled else "⚪ Disabled"

            # SSL status
            ssl_info = check_ssl_status(site)
            if ssl_info["ssl_enabled"]:
                days = ssl_info.get("days_remaining", 0)
                if days and days < 7:
                    ssl_status = f"🔒 [red]{days}d[/red]"
                elif days and days < 30:
                    ssl_status = f"🔒 [yellow]{days}d[/yellow]"
                else:
                    ssl_status = "🔒 [green]OK[/green]"
            else:
                ssl_status = "🔓 [dim]None[/dim]"

            # Site type from state or detect from config
            site_state = get_site_state(site)
            if site_state:
                site_type = site_state.get("type", "unknown")
                port_root = site_state.get("port") or site_state.get("document_root") or "-"
            else:
                # Try to detect from config
                site_type, port_root = detect_site_type(site)

            type_icons = {
                "nextjs": "⚡ Next.js",
                "nuxt": "🟢 Nuxt.js",
                "php": "🐘 PHP",
                "static": "📄 Static",
                "unknown": "❓",
            }

            table.add_row(
                site,
                enabled_status,
                ssl_status,
                type_icons.get(site_type, site_type),
                str(port_root)[:30] if port_root else "-",
            )

        console.print(table)

        # Show summary
        ssl_count = sum(1 for s in available if check_ssl_status(s)["ssl_enabled"])
        enabled_count = sum(1 for s in available if s in enabled)

        console.print()
        console.print(f"[dim]Total: {len(available)} sites | Enabled: {enabled_count} | With SSL: {ssl_count}[/dim]")

    console.print()
    questionary.press_any_key_to_continue().ask()


def detect_site_type(domain: str) -> tuple:
    """Detect site type from Nginx config."""
    config_path = f"{SITES_AVAILABLE}/{domain}"
    if not os.path.exists(config_path):
        code, stdout, _ = run_command(f"sudo cat {config_path}", check=False)
        if code != 0:
            return "unknown", None
        content = stdout
    else:
        try:
            with open(config_path) as f:
                content = f.read()
        except PermissionError:
            code, content, _ = run_command(f"sudo cat {config_path}", check=False)

    # Detect type
    if "proxy_pass" in content:
        # Extract port
        import re
        match = re.search(r'proxy_pass\s+http://127\.0\.0\.1:(\d+)', content)
        port = match.group(1) if match else None

        if "Next.js" in content:
            return "nextjs", port
        elif "Nuxt" in content:
            return "nuxt", port
        return "nextjs", port  # Default to nextjs for proxy configs

    elif "fastcgi_pass" in content:
        # Extract document root
        import re
        match = re.search(r'root\s+([^;]+)', content)
        root = match.group(1).strip() if match else None
        return "php", root

    else:
        # Static
        import re
        match = re.search(r'root\s+([^;]+)', content)
        root = match.group(1).strip() if match else None
        return "static", root


# ═══════════════════════════════════════════════════════════════════════════════
# CREATE SITE
# ═══════════════════════════════════════════════════════════════════════════════

def create_site():
    """Create a new site interactively with hardened configuration."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Manage Sites", "Create"])

    # Select site type
    type_choices = get_template_types()
    site_type = questionary.select(
        "Select site type:",
        choices=[{"name": t["name"], "value": t["value"]} for t in type_choices],
        qmark="🌐",
    ).ask()

    if not site_type:
        return

    # Get domain name
    domain = questionary.text(
        "Enter domain name (e.g., example.com):",
        validate=lambda x: len(x) > 0 and "." in x,
    ).ask()

    if not domain:
        return

    # Include www?
    include_www = questionary.confirm(
        f"Include www.{domain}?",
        default=True,
    ).ask()

    # Type-specific configuration
    config = {
        "domain": domain,
        "www": include_www,
    }

    if site_type in ["nextjs", "nuxt"]:
        port = questionary.text(
            "Enter application port:",
            default="3000",
            validate=lambda x: x.isdigit() and 1000 <= int(x) <= 65535,
        ).ask()
        config["port"] = int(port)

    elif site_type == "php":
        doc_root = questionary.text(
            "Enter document root path:",
            default=f"/var/www/{domain}/public",
        ).ask()
        php_version = questionary.select(
            "Select PHP version:",
            choices=["8.3", "8.2", "8.1", "8.0"],
        ).ask()
        config["document_root"] = doc_root
        config["php_version"] = php_version

    else:  # static
        doc_root = questionary.text(
            "Enter document root path:",
            default=f"/var/www/{domain}",
        ).ask()
        config["document_root"] = doc_root

    # Advanced options
    if questionary.confirm("Configure advanced options?", default=False).ask():
        max_body = questionary.text(
            "Max upload size (e.g., 100M):",
            default="100M",
        ).ask()
        config["max_body_size"] = max_body

    # Generate config using hardened template
    rendered = render_template(site_type=site_type, **config)

    console.print("\n[bold]Generated Configuration:[/bold]")
    console.print(Panel(rendered, title=f"{domain}", border_style="dim"))

    if not confirm_action("Create this site?", default=True):
        return

    # Write config file
    config_path = f"{SITES_AVAILABLE}/{domain}"

    # Write to temp file first, then move with sudo
    temp_path = f"/tmp/{domain}.conf"
    with open(temp_path, "w") as f:
        f.write(rendered)

    run_command(f"sudo mv {temp_path} {config_path}", check=False)

    # Create document root if needed
    if "document_root" in config:
        run_command(f"sudo mkdir -p {config['document_root']}", check=False)
        run_command(f"sudo chown -R www-data:www-data {config['document_root']}", check=False)

    # Create log files
    run_command(f"sudo touch /var/log/nginx/{domain}.access.log", check=False)
    run_command(f"sudo touch /var/log/nginx/{domain}.error.log", check=False)

    # Enable site
    run_command(f"sudo ln -sf {config_path} {SITES_ENABLED}/{domain}", check=False)

    # Test and reload nginx
    code, _, stderr = run_command("sudo nginx -t", check=False)
    if code != 0:
        print_error(f"Nginx config test failed: {stderr}")
        # Disable the problematic site
        run_command(f"sudo rm -f {SITES_ENABLED}/{domain}", check=False)
        return

    run_command("sudo systemctl reload nginx", check=False)

    # Save state
    save_site_state(
        domain=domain,
        site_type=site_type,
        ssl_enabled=False,
        port=config.get("port"),
        document_root=config.get("document_root"),
        php_version=config.get("php_version"),
        enabled=True,
    )

    print_success(f"Site {domain} created and enabled!")

    # Ask about SSL
    if questionary.confirm("Would you like to set up SSL now?", default=True).ask():
        provision_ssl_for_domain(domain, include_www)

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# SSL PROVISIONING
# ═══════════════════════════════════════════════════════════════════════════════

def provision_ssl_for_site():
    """Provision SSL for an existing site."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Manage Sites", "SSL"])

    # Get sites without SSL
    code, stdout, _ = run_command(f"ls {SITES_ENABLED}", check=False)
    sites = [s for s in stdout.split() if s != "default"] if code == 0 else []

    if not sites:
        print_warning("No enabled sites found.")
        questionary.press_any_key_to_continue().ask()
        return

    # Build choices with SSL status
    choices = []
    for site in sites:
        ssl_info = check_ssl_status(site)
        if ssl_info["ssl_enabled"]:
            status = f"🔒 {site} [dim](SSL active)[/dim]"
        else:
            status = f"🔓 {site} [yellow](needs SSL)[/yellow]"
        choices.append({"name": status, "value": site})

    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Back", "value": None})

    site = questionary.select(
        "Select site to provision SSL:",
        choices=choices,
    ).ask()

    if not site:
        return

    include_www = questionary.confirm(f"Include www.{site}?", default=True).ask()
    provision_ssl_for_domain(site, include_www)


def provision_ssl_for_domain(domain: str, include_www: bool = True):
    """Provision SSL certificate for a domain."""
    from utils.shell import command_exists

    if not command_exists("certbot"):
        print_error("Certbot is not installed!")
        print_info("Install it from the 'Install Packages' menu.")
        return

    # Build certbot command
    domains = f"-d {domain}"
    if include_www:
        domains += f" -d www.{domain}"

    console.print("\n[cyan]Provisioning SSL certificate...[/cyan]\n")

    cmd = f"sudo certbot --nginx {domains} --non-interactive --agree-tos --register-unsafely-without-email"
    code, stdout, stderr = run_command(cmd, check=False)

    if code == 0:
        print_success(f"SSL certificate provisioned for {domain}!")
        console.print("[green]✓ HTTPS is now enabled[/green]")

        # Update state
        update_site_ssl(domain, True)

        # Reload nginx
        run_command("sudo systemctl reload nginx", check=False)
    else:
        print_error(f"Failed to provision certificate: {stderr}")
        console.print()
        print_info("Common issues:")
        console.print("  • Domain DNS must point to this server")
        console.print("  • Port 80 must be accessible from internet")
        console.print("  • Try DNS verification instead")

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW SITE LOGS
# ═══════════════════════════════════════════════════════════════════════════════

def view_site_logs():
    """View logs for a specific site."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Manage Sites", "Logs"])

    # Get sites
    code, stdout, _ = run_command(f"ls {SITES_ENABLED}", check=False)
    sites = [s for s in stdout.split() if s != "default"] if code == 0 else []

    if not sites:
        print_warning("No sites found.")
        questionary.press_any_key_to_continue().ask()
        return

    site = questionary.select(
        "Select site:",
        choices=sites + [questionary.Separator(), {"name": "⬅️ Cancel", "value": None}],
    ).ask()

    if not site:
        return

    log_type = questionary.select(
        "Log type:",
        choices=[
            {"name": "🌐 Access Log", "value": "access"},
            {"name": "❌ Error Log", "value": "error"},
            {"name": "📡 Live (tail -f)", "value": "live"},
        ],
    ).ask()

    log_path = f"/var/log/nginx/{site}.{log_type.replace('live', 'access')}.log"

    if log_type == "live":
        console.print(f"\n[cyan]📡 Live monitoring: {log_path}[/cyan]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        try:
            import subprocess
            process = subprocess.Popen(
                ["sudo", "tail", "-f", log_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for line in process.stdout:
                # Color code by status
                if " 5" in line:
                    console.print(f"[red]{line.strip()}[/red]")
                elif " 4" in line:
                    console.print(f"[yellow]{line.strip()}[/yellow]")
                else:
                    console.print(line.strip())
        except KeyboardInterrupt:
            process.terminate()
    else:
        lines = questionary.text(
            "Number of lines:",
            default="50",
            validate=lambda x: x.isdigit(),
        ).ask()

        console.print(f"\n[bold]Last {lines} lines of {log_type} log:[/bold]\n")

        code, stdout, stderr = run_command(f"sudo tail -n {lines} {log_path}", check=False)

        if code != 0:
            print_error(f"Failed to read logs: {stderr}")
            # Try generic log
            code, stdout, _ = run_command(
                f"sudo grep '{site}' /var/log/nginx/{log_type}.log | tail -n {lines}",
                check=False
            )

        if stdout:
            for line in stdout.split("\n"):
                if log_type == "error" and "error" in line.lower():
                    console.print(f"[red]{line}[/red]")
                elif " 5" in line:
                    console.print(f"[red]{line}[/red]")
                elif " 4" in line:
                    console.print(f"[yellow]{line}[/yellow]")
                else:
                    console.print(line)

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

def view_site_config():
    """View a site's Nginx configuration."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Manage Sites", "View Config"])

    code, stdout, _ = run_command(f"ls {SITES_AVAILABLE}", check=False)
    sites = [s for s in stdout.split() if s != "default"] if code == 0 else []

    if not sites:
        print_warning("No sites found.")
        questionary.press_any_key_to_continue().ask()
        return

    site = questionary.select(
        "Select site:",
        choices=sites + [questionary.Separator(), {"name": "⬅️ Cancel", "value": None}],
    ).ask()

    if not site:
        return

    code, stdout, _ = run_command(f"sudo cat {SITES_AVAILABLE}/{site}", check=False)

    if code == 0:
        console.print(Panel(stdout, title=f"Configuration: {site}", border_style="cyan"))
    else:
        print_error("Failed to read configuration.")

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

def check_site_health():
    """Check health of a specific site."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Manage Sites", "Health"])

    code, stdout, _ = run_command(f"ls {SITES_ENABLED}", check=False)
    sites = [s for s in stdout.split() if s != "default"] if code == 0 else []

    if not sites:
        print_warning("No sites found.")
        questionary.press_any_key_to_continue().ask()
        return

    site = questionary.select(
        "Select site to check:",
        choices=sites + [questionary.Separator(), {"name": "⬅️ Cancel", "value": None}],
    ).ask()

    if not site:
        return

    console.print(f"\n[bold]🏥 Health Check: {site}[/bold]\n")

    from utils.network import http_check, check_ssl_certificate, verify_domain_points_to_server

    # DNS Check
    dns_ok, dns_msg = verify_domain_points_to_server(site)
    if dns_ok:
        console.print(f"[green]✓[/green] DNS: {dns_msg}")
    else:
        console.print(f"[red]✗[/red] DNS: {dns_msg}")

    # HTTP Check
    http_result = http_check(f"http://{site}", timeout=10)
    if http_result["success"]:
        console.print(f"[green]✓[/green] HTTP: {http_result['status_code']} ({http_result['response_time_ms']}ms)")
    else:
        console.print(f"[yellow]○[/yellow] HTTP: {http_result.get('error', 'Failed')}")

    # HTTPS Check
    https_result = http_check(f"https://{site}", timeout=10)
    if https_result["success"]:
        console.print(f"[green]✓[/green] HTTPS: {https_result['status_code']} ({https_result['response_time_ms']}ms)")
    else:
        console.print(f"[red]✗[/red] HTTPS: {https_result.get('error', 'Failed')}")

    # SSL Certificate
    ssl_info = check_ssl_certificate(site)
    if ssl_info["valid"]:
        console.print(f"[green]✓[/green] SSL: Valid, expires in {ssl_info['days_remaining']} days")
    elif ssl_info["error"]:
        console.print(f"[red]✗[/red] SSL: {ssl_info['error']}")
    else:
        console.print(f"[yellow]○[/yellow] SSL: No certificate")

    # Nginx config test
    code, stdout, stderr = run_command(f"sudo nginx -t 2>&1 | grep -i {site}", check=False)
    if "error" in stderr.lower():
        console.print(f"[red]✗[/red] Nginx Config: Error in configuration")
    else:
        console.print(f"[green]✓[/green] Nginx Config: Valid")

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE SITE
# ═══════════════════════════════════════════════════════════════════════════════

def delete_site():
    """Delete a site."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Manage Sites", "Delete"])

    # Get available sites
    code, stdout, _ = run_command(f"ls {SITES_AVAILABLE}", check=False)
    sites = [s for s in stdout.split() if s != "default"] if code == 0 else []

    if not sites:
        print_warning("No sites to delete.")
        questionary.press_any_key_to_continue().ask()
        return

    site = questionary.select(
        "Select site to delete:",
        choices=sites + [questionary.Separator(), {"name": "⬅️ Cancel", "value": None}],
    ).ask()

    if not site:
        return

    console.print()
    print_warning(f"This will delete the site configuration for {site}")
    print_info("This will NOT delete the document root or SSL certificates.")

    if not confirm_action(f"Are you sure you want to delete {site}?"):
        return

    # Remove from sites-enabled and sites-available
    run_command(f"sudo rm -f {SITES_ENABLED}/{site}", check=False)
    run_command(f"sudo rm -f {SITES_AVAILABLE}/{site}", check=False)
    run_command("sudo systemctl reload nginx", check=False)

    # Remove from state
    delete_site_state(site)

    print_success(f"Site {site} deleted!")
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# TOGGLE SITE
# ═══════════════════════════════════════════════════════════════════════════════

def toggle_site():
    """Enable or disable a site."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Manage Sites", "Toggle"])

    # Get available sites
    code, stdout, _ = run_command(f"ls {SITES_AVAILABLE}", check=False)
    available = [s for s in stdout.split() if s != "default"] if code == 0 else []

    code, stdout, _ = run_command(f"ls {SITES_ENABLED}", check=False)
    enabled = stdout.split() if code == 0 else []

    if not available:
        print_warning("No sites found.")
        questionary.press_any_key_to_continue().ask()
        return

    choices = []
    for site in available:
        status = "🟢" if site in enabled else "⚪"
        choices.append({"name": f"{status} {site}", "value": site})

    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    site = questionary.select(
        "Select site to toggle:",
        choices=choices,
    ).ask()

    if not site:
        return

    if site in enabled:
        # Disable
        run_command(f"sudo rm -f {SITES_ENABLED}/{site}", check=False)
        print_success(f"Site {site} disabled.")
    else:
        # Enable
        run_command(f"sudo ln -sf {SITES_AVAILABLE}/{site} {SITES_ENABLED}/{site}", check=False)
        print_success(f"Site {site} enabled.")

    run_command("sudo systemctl reload nginx", check=False)
    questionary.press_any_key_to_continue().ask()
