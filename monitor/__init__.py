"""
System & Site Monitoring - Real-time stats and health checks
"""

import time
import questionary
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, print_warning, print_info
)
from utils.shell import run_command, get_command_output
from utils.network import (
    get_local_ips, get_public_ip, http_check, check_ssl_certificate,
    get_listening_ports, check_port_open
)

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# MONITOR MENU
# ═══════════════════════════════════════════════════════════════════════════════

MONITOR_MENU_CHOICES = [
    {"name": "💻  System Overview", "value": "system"},
    {"name": "🌐  Network & IPs", "value": "network"},
    {"name": "🔌  Listening Ports", "value": "ports"},
    {"name": "🏥  Site Health Check", "value": "health"},
    {"name": "🔒  SSL Certificate Check", "value": "ssl"},
    {"name": "📊  Live Dashboard", "value": "live"},
    questionary.Separator("─" * 30),
    {"name": "⬅️   Back", "value": "back"},
]


def run_monitor_menu():
    """Display the monitoring menu."""
    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "Monitor"])

        choice = questionary.select(
            "System Monitoring:",
            choices=MONITOR_MENU_CHOICES,
            qmark="📊",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "system":
            show_system_overview()
        elif choice == "network":
            show_network_info()
        elif choice == "ports":
            show_listening_ports()
        elif choice == "health":
            run_health_checks()
        elif choice == "ssl":
            check_ssl_certificates()
        elif choice == "live":
            live_dashboard()


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

def show_system_overview():
    """Show system resource usage."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitor", "System"])

    console.print("\n[bold]💻 System Overview[/bold]\n")

    # CPU Usage
    cpu_usage = get_cpu_usage()
    cpu_bar = create_progress_bar(cpu_usage, 100)
    console.print(f"[cyan]CPU:[/cyan]      {cpu_bar} {cpu_usage:.1f}%")

    # Memory Usage
    mem_info = get_memory_usage()
    mem_bar = create_progress_bar(mem_info["percent"], 100)
    console.print(f"[cyan]Memory:[/cyan]   {mem_bar} {mem_info['percent']:.1f}% ({mem_info['used']}/{mem_info['total']})")

    # Disk Usage
    disk_info = get_disk_usage()
    disk_bar = create_progress_bar(disk_info["percent"], 100)
    console.print(f"[cyan]Disk:[/cyan]     {disk_bar} {disk_info['percent']:.1f}% ({disk_info['used']}/{disk_info['total']})")

    console.print()

    # Load Average
    load = get_load_average()
    if load:
        console.print(f"[cyan]Load Avg:[/cyan]  {load['1min']:.2f} / {load['5min']:.2f} / {load['15min']:.2f}")

    # Uptime
    uptime = get_uptime()
    if uptime:
        console.print(f"[cyan]Uptime:[/cyan]    {uptime}")

    console.print()

    # Service Status Summary
    console.print("[bold]⚙️ Service Status[/bold]\n")

    services = [
        ("nginx", "Nginx"),
        ("php8.3-fpm", "PHP 8.3 FPM"),
        ("php8.2-fpm", "PHP 8.2 FPM"),
        ("redis-server", "Redis"),
        ("mysql", "MySQL"),
        ("postgresql", "PostgreSQL"),
    ]

    for service, name in services:
        code, stdout, _ = run_command(f"systemctl is-active {service}", check=False)
        if stdout.strip() == "active":
            console.print(f"  🟢 {name}")
        elif stdout.strip() == "inactive":
            console.print(f"  ⚪ {name} [dim](stopped)[/dim]")
        else:
            console.print(f"  ❌ {name} [dim](not installed)[/dim]")

    console.print()
    questionary.press_any_key_to_continue().ask()


def get_cpu_usage() -> float:
    """Get CPU usage percentage."""
    try:
        output = get_command_output("grep 'cpu ' /proc/stat")
        if output:
            parts = output.split()
            idle = float(parts[4])
            total = sum(float(p) for p in parts[1:8])
            return 100 * (1 - idle / total)
    except Exception:
        pass
    return 0.0


def get_memory_usage() -> Dict[str, any]:
    """Get memory usage info."""
    try:
        output = get_command_output("free -h")
        if output:
            lines = output.split("\n")
            mem_line = lines[1].split()
            return {
                "total": mem_line[1],
                "used": mem_line[2],
                "percent": float(get_command_output("free | awk 'NR==2{print $3/$2*100}'") or 0),
            }
    except Exception:
        pass
    return {"total": "?", "used": "?", "percent": 0}


def get_disk_usage() -> Dict[str, any]:
    """Get disk usage for root partition."""
    try:
        output = get_command_output("df -h /")
        if output:
            lines = output.split("\n")
            parts = lines[1].split()
            return {
                "total": parts[1],
                "used": parts[2],
                "percent": float(parts[4].rstrip("%")),
            }
    except Exception:
        pass
    return {"total": "?", "used": "?", "percent": 0}


def get_load_average() -> Dict[str, float]:
    """Get system load average."""
    try:
        output = get_command_output("cat /proc/loadavg")
        if output:
            parts = output.split()
            return {
                "1min": float(parts[0]),
                "5min": float(parts[1]),
                "15min": float(parts[2]),
            }
    except Exception:
        pass
    return None


def get_uptime() -> str:
    """Get system uptime."""
    return get_command_output("uptime -p") or ""


def create_progress_bar(value: float, max_value: float, width: int = 20) -> str:
    """Create a text-based progress bar."""
    filled = int(width * value / max_value)
    empty = width - filled

    if value < 50:
        color = "green"
    elif value < 80:
        color = "yellow"
    else:
        color = "red"

    return f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"


# ═══════════════════════════════════════════════════════════════════════════════
# NETWORK INFO
# ═══════════════════════════════════════════════════════════════════════════════

def show_network_info():
    """Show network interfaces and IPs."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitor", "Network"])

    console.print("\n[bold]🌐 Network Information[/bold]\n")

    # Public IP
    console.print("[cyan]Fetching public IP...[/cyan]")
    public_ip = get_public_ip()
    if public_ip:
        console.print(f"\n[bold]Public IP:[/bold] [green]{public_ip}[/green]")
    else:
        console.print("\n[bold]Public IP:[/bold] [dim]Unable to detect[/dim]")

    # Local IPs
    console.print("\n[bold]Local IP Addresses:[/bold]\n")

    local_ips = get_local_ips()
    if local_ips:
        table = Table(box=box.SIMPLE)
        table.add_column("Interface", style="cyan")
        table.add_column("IP Address", style="green")
        table.add_column("Type")

        for ip_info in local_ips:
            table.add_row(
                ip_info["interface"],
                ip_info["ip"],
                ip_info["type"].upper()
            )

        console.print(table)
    else:
        print_warning("No local IPs detected.")

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# LISTENING PORTS
# ═══════════════════════════════════════════════════════════════════════════════

def show_listening_ports():
    """Show all listening ports."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitor", "Ports"])

    console.print("\n[bold]🔌 Listening Ports[/bold]\n")

    ports = get_listening_ports()

    if ports:
        table = Table(box=box.ROUNDED, header_style="bold")
        table.add_column("Port", style="cyan", justify="right")
        table.add_column("IP", style="dim")
        table.add_column("Service")

        # Common port mappings
        port_services = {
            22: "SSH",
            80: "HTTP",
            443: "HTTPS",
            3000: "Node.js",
            3306: "MySQL",
            5432: "PostgreSQL",
            6379: "Redis",
            9000: "PHP-FPM",
        }

        seen_ports = set()
        for port_info in ports:
            port = port_info["port"]
            if port not in seen_ports:
                seen_ports.add(port)
                service = port_services.get(port, "")
                table.add_row(
                    str(port),
                    port_info["ip"],
                    service
                )

        console.print(table)
    else:
        print_warning("Unable to detect listening ports.")

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

def run_health_checks():
    """Run health checks on configured sites."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitor", "Health"])

    console.print("\n[bold]🏥 Site Health Checks[/bold]\n")

    # Get sites from nginx
    code, stdout, _ = run_command("ls /etc/nginx/sites-enabled", check=False)
    sites = [s for s in stdout.split() if s != "default"] if code == 0 else []

    if not sites:
        print_warning("No sites configured.")
        questionary.press_any_key_to_continue().ask()
        return

    table = Table(box=box.ROUNDED, header_style="bold")
    table.add_column("Site", style="cyan")
    table.add_column("HTTP", justify="center")
    table.add_column("HTTPS", justify="center")
    table.add_column("Response", justify="right")
    table.add_column("Status")

    with console.status("[bold cyan]Checking sites..."):
        for site in sites:
            # HTTP check
            http_result = http_check(f"http://{site}", timeout=5)

            # HTTPS check
            https_result = http_check(f"https://{site}", timeout=5)

            # Determine status
            http_status = "🟢" if http_result["success"] else "🔴" if http_result["status_code"] else "⚪"
            https_status = "🟢" if https_result["success"] else "🔴" if https_result["status_code"] else "⚪"

            response_time = ""
            if http_result["response_time_ms"]:
                response_time = f"{http_result['response_time_ms']}ms"
            elif https_result["response_time_ms"]:
                response_time = f"{https_result['response_time_ms']}ms"

            # Overall status
            if https_result["success"]:
                status = "[green]Healthy[/green]"
            elif http_result["success"]:
                status = "[yellow]HTTP Only[/yellow]"
            else:
                error = http_result.get("error") or https_result.get("error") or "Unreachable"
                status = f"[red]{error[:20]}[/red]"

            table.add_row(site, http_status, https_status, response_time, status)

    console.print(table)
    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# SSL CERTIFICATES
# ═══════════════════════════════════════════════════════════════════════════════

def check_ssl_certificates():
    """Check SSL certificate status for all sites."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitor", "SSL"])

    console.print("\n[bold]🔒 SSL Certificate Status[/bold]\n")

    # Get sites
    code, stdout, _ = run_command("ls /etc/nginx/sites-enabled", check=False)
    sites = [s for s in stdout.split() if s != "default"] if code == 0 else []

    if not sites:
        print_warning("No sites configured.")
        questionary.press_any_key_to_continue().ask()
        return

    table = Table(box=box.ROUNDED, header_style="bold")
    table.add_column("Domain", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Issuer")
    table.add_column("Expires")
    table.add_column("Days Left", justify="right")

    with console.status("[bold cyan]Checking certificates..."):
        for site in sites:
            cert_info = check_ssl_certificate(site)

            if cert_info["valid"]:
                status = "🟢 Valid"
                days = cert_info["days_remaining"]

                if days < 7:
                    days_str = f"[red bold]{days}[/red bold]"
                elif days < 30:
                    days_str = f"[yellow]{days}[/yellow]"
                else:
                    days_str = f"[green]{days}[/green]"

                issuer = cert_info.get("issuer") or "Unknown"
                expires = cert_info.get("expires", "")[:10] if cert_info.get("expires") else ""
            elif cert_info["error"]:
                status = "🔴 Error"
                days_str = "-"
                issuer = cert_info["error"][:30]
                expires = "-"
            else:
                status = "⚪ None"
                days_str = "-"
                issuer = "No certificate"
                expires = "-"

            table.add_row(site, status, issuer, expires, days_str)

    console.print(table)

    # Show warning for expiring certs
    console.print()
    print_info("Tip: Use 'certbot renew' to renew expiring certificates.")

    console.print()
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def live_dashboard():
    """Show a live updating dashboard."""
    console.print("\n[bold cyan]📊 Live Dashboard[/bold cyan]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")

    try:
        while True:
            # Clear and rebuild
            output = []

            # CPU
            cpu = get_cpu_usage()
            output.append(f"CPU:    {create_progress_bar(cpu, 100)} {cpu:.1f}%")

            # Memory
            mem = get_memory_usage()
            output.append(f"Memory: {create_progress_bar(mem['percent'], 100)} {mem['percent']:.1f}%")

            # Disk
            disk = get_disk_usage()
            output.append(f"Disk:   {create_progress_bar(disk['percent'], 100)} {disk['percent']:.1f}%")

            # Load
            load = get_load_average()
            if load:
                output.append(f"Load:   {load['1min']:.2f} / {load['5min']:.2f} / {load['15min']:.2f}")

            # Time
            from datetime import datetime
            output.append(f"\nUpdated: {datetime.now().strftime('%H:%M:%S')}")

            # Print with carriage return to overwrite
            console.print("\033[H\033[J", end="")  # Clear screen
            console.print("[bold]📊 Live System Monitor[/bold]\n")
            for line in output:
                console.print(line)
            console.print("\n[dim]Press Ctrl+C to exit[/dim]")

            time.sleep(2)

    except KeyboardInterrupt:
        pass

    console.print("\n[dim]Dashboard stopped.[/dim]")
    questionary.press_any_key_to_continue().ask()
