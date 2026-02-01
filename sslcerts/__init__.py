"""
SSL Certificate Management - Let's Encrypt via Certbot
"""

import questionary
from rich.console import Console
from rich.table import Table
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, print_warning, print_info, confirm_action
)
from utils.shell import run_command, command_exists, get_command_output

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# SSL MENU
# ═══════════════════════════════════════════════════════════════════════════════

SSL_MENU_CHOICES = [
    {"name": "🔐  Provision SSL Certificate", "value": "provision"},
    {"name": "📋  List Certificates", "value": "list"},
    {"name": "🔄  Renew Certificates", "value": "renew"},
    {"name": "🗑️   Revoke Certificate", "value": "revoke"},
    questionary.Separator("─" * 30),
    {"name": "⬅️   Back", "value": "back"},
]


def run_ssl_menu():
    """Display the SSL management menu."""
    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "SSL Certificates"])

        if not command_exists("certbot"):
            print_error("Certbot is not installed!")
            print_info("Install it from the 'Install Packages' menu.")
            questionary.press_any_key_to_continue().ask()
            return

        choice = questionary.select(
            "SSL Certificate Management:",
            choices=SSL_MENU_CHOICES,
            qmark="🔒",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "provision":
            provision_ssl()
        elif choice == "list":
            list_certificates()
        elif choice == "renew":
            renew_certificates()
        elif choice == "revoke":
            revoke_certificate()


def provision_ssl():
    """Provision a new SSL certificate."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "SSL Certificates", "Provision"])

    # Get domain
    domain = questionary.text(
        "Enter domain name:",
        validate=lambda x: len(x) > 0 and "." in x,
    ).ask()

    if not domain:
        return

    # Include www?
    include_www = questionary.confirm(
        f"Include www.{domain}?",
        default=True,
    ).ask()

    provision_ssl_for_domain(domain, include_www)


def provision_ssl_for_domain(domain: str, include_www: bool = True):
    """Provision SSL for a specific domain."""
    # Select verification method
    method = questionary.select(
        "Select verification method:",
        choices=[
            {"name": "🌐 HTTP (requires port 80 access)", "value": "http"},
            {"name": "📝 DNS (manual DNS record)", "value": "dns"},
        ],
        qmark="🔒",
    ).ask()

    if not method:
        return

    domains = f"-d {domain}"
    if include_www:
        domains += f" -d www.{domain}"

    success = False

    if method == "http":
        # HTTP verification with Nginx
        cmd = f"sudo certbot --nginx {domains} --non-interactive --agree-tos --register-unsafely-without-email"

        console.print("\n[cyan]Provisioning SSL certificate via HTTP verification...[/cyan]")
        code, stdout, stderr = run_command(cmd, check=False)

        if code == 0:
            print_success(f"SSL certificate provisioned for {domain}!")
            console.print("[green]✓ HTTPS is now enabled[/green]")
            success = True
        else:
            print_error(f"Failed to provision certificate: {stderr}")

    else:  # DNS verification
        console.print("\n[bold yellow]DNS Verification Required[/bold yellow]")
        console.print("\nYou will need to add a TXT record to your DNS.\n")

        # Run certbot in manual mode
        cmd = f"sudo certbot certonly --manual --preferred-challenges dns {domains}"

        console.print(f"[dim]Run this command manually:[/dim]")
        console.print(f"[cyan]{cmd}[/cyan]")
        console.print()
        console.print("[yellow]Follow the prompts to add the DNS TXT record.[/yellow]")
        console.print()

        print_info("DNS TXT Record format:")
        console.print(f"  Name:  _acme-challenge.{domain}")
        console.print("  Type:  TXT")
        console.print("  Value: (provided by certbot)")
        console.print()

        if confirm_action("Run certbot now?"):
            import subprocess
            result = subprocess.run(cmd.split())
            success = result.returncode == 0

    # Set up auto-renewal if certificate was provisioned successfully
    if success:
        setup_auto_renewal()

    questionary.press_any_key_to_continue().ask()


def setup_auto_renewal():
    """Set up automatic SSL certificate renewal."""
    console.print("\n[bold]🔄 Setting up auto-renewal...[/bold]")

    # Check if certbot timer is available (systemd)
    code, stdout, _ = run_command("systemctl is-enabled certbot.timer 2>/dev/null", check=False)

    if code == 0 and "enabled" in stdout:
        console.print("[green]✓ Certbot systemd timer is already enabled[/green]")
        return

    # Check if certbot timer exists but not enabled
    code, _, _ = run_command("systemctl list-unit-files certbot.timer 2>/dev/null | grep certbot", check=False)

    if code == 0:
        # Enable the timer
        console.print("[cyan]Enabling certbot systemd timer...[/cyan]")
        code, _, _ = run_command("sudo systemctl enable --now certbot.timer", check=False)

        if code == 0:
            console.print("[green]✓ Certbot timer enabled (renews twice daily)[/green]")
            return

    # Fall back to cron if systemd timer not available
    console.print("[cyan]Setting up cron-based auto-renewal...[/cyan]")

    # Check if cron entry already exists
    code, stdout, _ = run_command("sudo cat /etc/cron.d/certbot 2>/dev/null", check=False)

    if code == 0 and stdout.strip():
        console.print("[green]✓ Certbot cron job already exists[/green]")
        return

    # Create cron entry
    cron_entry = "0 0,12 * * * root test -x /usr/bin/certbot -a \\! -d /run/systemd/system && perl -e 'sleep int(rand(43200))' && certbot -q renew"

    code, _, stderr = run_command(
        f"echo '{cron_entry}' | sudo tee /etc/cron.d/certbot",
        check=False
    )

    if code == 0:
        # Set proper permissions
        run_command("sudo chmod 644 /etc/cron.d/certbot", check=False)
        console.print("[green]✓ Cron-based auto-renewal configured[/green]")
        console.print("[dim]  Certbot will check for renewals twice daily (midnight & noon)[/dim]")
    else:
        print_warning(f"Could not set up auto-renewal: {stderr}")
        console.print("[dim]You can manually set up renewal with:[/dim]")
        console.print("[dim]  sudo certbot renew --dry-run[/dim]")


def list_certificates():
    """List all installed certificates with renewal information."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "SSL Certificates", "List"])

    console.print("\n[bold]🔐 SSL Certificates[/bold]\n")

    code, stdout, stderr = run_command("sudo certbot certificates", check=False)

    if code != 0:
        print_error(f"Failed to list certificates: {stderr}")
        questionary.press_any_key_to_continue().ask()
        return

    if "No certificates found" in stdout or not stdout.strip():
        print_warning("No SSL certificates found.")
        questionary.press_any_key_to_continue().ask()
        return

    # Parse certificate info
    certs = parse_certbot_certificates(stdout)

    if not certs:
        print_warning("No certificates could be parsed.")
        questionary.press_any_key_to_continue().ask()
        return

    # Create renewal tracking table
    table = Table(
        title="📜 Certificate Renewal Tracking",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Domain", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Expiry Date", style="yellow")
    table.add_column("Days Left", justify="right")
    table.add_column("Last Renewed", style="dim")
    table.add_column("Next Renewal", style="green")
    table.add_column("Auto-Renew", justify="center")

    import re
    from datetime import datetime, timedelta

    for cert in certs:
        domain = cert.get("name", "Unknown")
        expiry = cert.get("expiry", "Unknown")
        days_left = cert.get("days_remaining", 0)

        # Status based on days remaining
        if days_left <= 0:
            status = "[red]❌ EXPIRED[/red]"
            days_str = f"[red]{days_left}[/red]"
        elif days_left <= 7:
            status = "[red]⚠️  CRITICAL[/red]"
            days_str = f"[red]{days_left}[/red]"
        elif days_left <= 14:
            status = "[yellow]⚠️  WARNING[/yellow]"
            days_str = f"[yellow]{days_left}[/yellow]"
        elif days_left <= 30:
            status = "[yellow]⏳ RENEW SOON[/yellow]"
            days_str = f"[yellow]{days_left}[/yellow]"
        else:
            status = "[green]✓ VALID[/green]"
            days_str = f"[green]{days_left}[/green]"

        # Last renewed (90 days before current expiry for Let's Encrypt)
        if days_left > 0:
            last_renewed_days = 90 - days_left
            if last_renewed_days >= 0:
                last_renewed = f"{last_renewed_days} days ago"
            else:
                last_renewed = "New cert"
        else:
            last_renewed = "-"

        # Next renewal (Let's Encrypt renews at 30 days before expiry)
        if days_left > 30:
            next_renewal_days = days_left - 30
            next_renewal = f"In {next_renewal_days} days"
        elif days_left > 0:
            next_renewal = "[yellow]Due now[/yellow]"
        else:
            next_renewal = "[red]Expired[/red]"

        # Auto-renew check
        auto_renew = "[green]✓[/green]" if cert.get("auto_renew", True) else "[red]✗[/red]"

        table.add_row(
            domain,
            status,
            expiry,
            days_str,
            last_renewed,
            next_renewal,
            auto_renew,
        )

    console.print(table)

    # Summary
    console.print()
    total = len(certs)
    valid = sum(1 for c in certs if c.get("days_remaining", 0) > 30)
    warning = sum(1 for c in certs if 0 < c.get("days_remaining", 0) <= 30)
    expired = sum(1 for c in certs if c.get("days_remaining", 0) <= 0)

    console.print(f"[dim]Total: {total} | Valid: {valid} | Warning: {warning} | Expired: {expired}[/dim]")

    # Check auto-renewal cron
    code, cron_check, _ = run_command("sudo cat /etc/cron.d/certbot 2>/dev/null || systemctl is-active certbot.timer 2>/dev/null", check=False)
    if code == 0 and cron_check.strip():
        console.print("[green]✓ Auto-renewal is configured[/green]")
    else:
        console.print("[yellow]⚠ Auto-renewal may not be configured[/yellow]")

    console.print()
    questionary.press_any_key_to_continue().ask()


def parse_certbot_certificates(output: str) -> list:
    """Parse certbot certificates output into structured data."""
    import re

    certs = []
    current_cert = {}

    for line in output.split("\n"):
        line = line.strip()

        if line.startswith("Certificate Name:"):
            if current_cert:
                certs.append(current_cert)
            current_cert = {"name": line.split(":")[-1].strip()}

        elif line.startswith("Domains:"):
            current_cert["domains"] = line.split(":")[-1].strip()

        elif line.startswith("Expiry Date:"):
            # Parse: "Expiry Date: 2024-03-15 10:30:45+00:00 (VALID: 89 days)"
            parts = line.split(":", 1)
            if len(parts) >= 2:
                rest = parts[1].strip()
                # Extract date
                date_match = re.match(r"(\d{4}-\d{2}-\d{2})", rest)
                if date_match:
                    current_cert["expiry"] = date_match.group(1)

                # Extract days remaining
                days_match = re.search(r"(\d+)\s*days", rest)
                if days_match:
                    current_cert["days_remaining"] = int(days_match.group(1))

                # Check validity
                current_cert["auto_renew"] = "VALID" in rest

        elif line.startswith("Certificate Path:"):
            current_cert["cert_path"] = line.split(":")[-1].strip()

        elif line.startswith("Private Key Path:"):
            current_cert["key_path"] = line.split(":")[-1].strip()

    if current_cert:
        certs.append(current_cert)

    return certs


def renew_certificates():
    """Renew all certificates."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "SSL Certificates", "Renew"])

    if not confirm_action("Renew all certificates?", default=True):
        return

    console.print("\n[cyan]Renewing certificates...[/cyan]\n")

    code, stdout, stderr = run_command("sudo certbot renew", check=False)

    if code == 0:
        console.print(stdout)
        print_success("Certificate renewal complete!")
    else:
        print_error(f"Renewal failed: {stderr}")

    console.print()
    questionary.press_any_key_to_continue().ask()


def revoke_certificate():
    """Revoke a certificate."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "SSL Certificates", "Revoke"])

    # Get certificate list
    code, stdout, _ = run_command("sudo certbot certificates", check=False)

    if "No certificates found" in stdout or not stdout.strip():
        print_warning("No certificates to revoke.")
        questionary.press_any_key_to_continue().ask()
        return

    console.print("[bold]Current Certificates:[/bold]\n")
    console.print(stdout)
    console.print()

    domain = questionary.text(
        "Enter domain to revoke certificate for:",
        validate=lambda x: len(x) > 0,
    ).ask()

    if not domain:
        return

    if not confirm_action(f"Are you sure you want to revoke the certificate for {domain}?"):
        return

    code, stdout, stderr = run_command(
        f"sudo certbot revoke --cert-name {domain} --delete-after-revoke",
        check=False
    )

    if code == 0:
        print_success(f"Certificate for {domain} revoked and deleted!")
    else:
        print_error(f"Failed to revoke: {stderr}")

    questionary.press_any_key_to_continue().ask()
