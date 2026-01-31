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

    if method == "http":
        # HTTP verification with Nginx
        cmd = f"sudo certbot --nginx {domains} --non-interactive --agree-tos --register-unsafely-without-email"

        console.print("\n[cyan]Provisioning SSL certificate via HTTP verification...[/cyan]")
        code, stdout, stderr = run_command(cmd, check=False)

        if code == 0:
            print_success(f"SSL certificate provisioned for {domain}!")
            console.print("[green]✓ HTTPS is now enabled[/green]")
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
            subprocess.run(cmd.split())

    questionary.press_any_key_to_continue().ask()


def list_certificates():
    """List all installed certificates."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "SSL Certificates", "List"])

    code, stdout, stderr = run_command("sudo certbot certificates", check=False)

    if code != 0:
        print_error(f"Failed to list certificates: {stderr}")
    elif "No certificates found" in stdout or not stdout.strip():
        print_warning("No SSL certificates found.")
    else:
        console.print("\n[bold]Installed Certificates:[/bold]\n")
        console.print(stdout)

    console.print()
    questionary.press_any_key_to_continue().ask()


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
