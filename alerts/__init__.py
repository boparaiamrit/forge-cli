"""
Monitoring & Alerts - System monitoring with historical data, alerts, and thresholds
"""

import os
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
# MONITORING DATA PATHS
# ═══════════════════════════════════════════════════════════════════════════════

MONITOR_DATA_DIR = Path.home() / ".forge" / "monitoring"
ALERTS_FILE = MONITOR_DATA_DIR / "alerts.json"
HISTORY_FILE = MONITOR_DATA_DIR / "history.json"
THRESHOLDS_FILE = MONITOR_DATA_DIR / "thresholds.json"

# Default thresholds
DEFAULT_THRESHOLDS = {
    "cpu_warning": 70,
    "cpu_critical": 90,
    "memory_warning": 75,
    "memory_critical": 90,
    "disk_warning": 80,
    "disk_critical": 95,
    "load_warning": 4.0,  # Per CPU
    "load_critical": 8.0,
    "swap_warning": 50,
    "swap_critical": 80,
}


# ═══════════════════════════════════════════════════════════════════════════════
# ALERTS MENU
# ═══════════════════════════════════════════════════════════════════════════════

ALERTS_MENU_CHOICES = [
    {"name": "📊  Current System Status", "value": "status"},
    {"name": "📈  Resource Usage History", "value": "history"},
    questionary.Separator("─" * 30),
    {"name": "🔔  View Active Alerts", "value": "view_alerts"},
    {"name": "📋  Alert History", "value": "alert_history"},
    {"name": "✅  Acknowledge All Alerts", "value": "ack_alerts"},
    questionary.Separator("─" * 30),
    {"name": "⚙️   Configure Thresholds", "value": "thresholds"},
    {"name": "⏰  Setup Monitoring Cron", "value": "setup_cron"},
    {"name": "📧  Configure Notifications", "value": "notifications"},
    questionary.Separator("─" * 30),
    {"name": "🔄  Record Current Metrics", "value": "record"},
    {"name": "📉  Clear History", "value": "clear_history"},
    questionary.Separator("─" * 30),
    {"name": "⬅️   Back", "value": "back"},
]


def run_alerts_menu():
    """Display the alerts and monitoring menu."""
    MONITOR_DATA_DIR.mkdir(parents=True, exist_ok=True)
    load_thresholds()

    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "Monitoring & Alerts"])

        # Show alert summary
        show_alert_summary()

        choice = questionary.select(
            "Monitoring & Alerts:",
            choices=ALERTS_MENU_CHOICES,
            qmark="📊",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "status":
            show_current_status()
        elif choice == "history":
            show_usage_history()
        elif choice == "view_alerts":
            view_active_alerts()
        elif choice == "alert_history":
            view_alert_history()
        elif choice == "ack_alerts":
            acknowledge_all_alerts()
        elif choice == "thresholds":
            configure_thresholds()
        elif choice == "setup_cron":
            setup_monitoring_cron()
        elif choice == "notifications":
            configure_notifications()
        elif choice == "record":
            record_current_metrics()
        elif choice == "clear_history":
            clear_monitoring_history()


def show_alert_summary():
    """Show a quick alert count."""
    alerts = load_alerts()
    active = [a for a in alerts if not a.get("acknowledged")]
    critical = [a for a in active if a.get("severity") == "critical"]

    if critical:
        console.print(f"[red]🚨 {len(critical)} CRITICAL alerts![/red]")
    elif active:
        console.print(f"[yellow]⚠️ {len(active)} active alerts[/yellow]")
    else:
        console.print("[green]✓ No active alerts[/green]")
    console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load_thresholds() -> Dict:
    """Load thresholds from file or use defaults."""
    if THRESHOLDS_FILE.exists():
        try:
            with open(THRESHOLDS_FILE) as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_THRESHOLDS.copy()


def save_thresholds(thresholds: Dict):
    """Save thresholds to file."""
    with open(THRESHOLDS_FILE, "w") as f:
        json.dump(thresholds, f, indent=2)


def load_alerts() -> List[Dict]:
    """Load alerts from file."""
    if ALERTS_FILE.exists():
        try:
            with open(ALERTS_FILE) as f:
                return json.load(f)
        except:
            pass
    return []


def save_alerts(alerts: List[Dict]):
    """Save alerts to file."""
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=2, default=str)


def add_alert(metric: str, value: float, threshold: float, severity: str, message: str):
    """Add a new alert."""
    alerts = load_alerts()

    # Check if similar alert already exists
    for alert in alerts:
        if (alert.get("metric") == metric and
            alert.get("severity") == severity and
            not alert.get("acknowledged")):
            return  # Don't duplicate

    alert = {
        "id": len(alerts) + 1,
        "timestamp": datetime.now().isoformat(),
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "severity": severity,
        "message": message,
        "acknowledged": False,
    }

    alerts.append(alert)
    save_alerts(alerts)


def load_history() -> List[Dict]:
    """Load monitoring history."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except:
            pass
    return []


def save_history_entry(entry: Dict):
    """Save a history entry."""
    history = load_history()
    history.append(entry)

    # Keep only last 7 days (assuming 5-minute intervals = ~2000 entries)
    if len(history) > 2000:
        history = history[-2000:]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, default=str)


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS COLLECTION
# ═══════════════════════════════════════════════════════════════════════════════

def get_cpu_usage() -> float:
    """Get current CPU usage percentage."""
    code, stdout, _ = run_command(
        "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1",
        check=False
    )
    if code == 0 and stdout:
        try:
            return float(stdout.strip().replace(",", "."))
        except:
            pass

    # Fallback
    code, stdout, _ = run_command(
        "grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}'",
        check=False
    )
    if code == 0 and stdout:
        try:
            return float(stdout.strip())
        except:
            pass
    return 0.0


def get_memory_usage() -> Dict:
    """Get memory usage information."""
    result = {
        "total": 0,
        "used": 0,
        "free": 0,
        "percent": 0.0,
        "available": 0,
    }

    code, stdout, _ = run_command("free -b", check=False)
    if code == 0 and stdout:
        lines = stdout.strip().split("\n")
        for line in lines:
            if line.startswith("Mem:"):
                parts = line.split()
                if len(parts) >= 7:
                    result["total"] = int(parts[1])
                    result["used"] = int(parts[2])
                    result["free"] = int(parts[3])
                    result["available"] = int(parts[6]) if len(parts) > 6 else int(parts[3])
                    if result["total"] > 0:
                        result["percent"] = (result["used"] / result["total"]) * 100

    return result


def get_disk_usage() -> Dict:
    """Get disk usage for main partitions."""
    result = {}

    code, stdout, _ = run_command("df -B1 / /var /home 2>/dev/null", check=False)
    if code == 0 and stdout:
        lines = stdout.strip().split("\n")[1:]
        for line in lines:
            parts = line.split()
            if len(parts) >= 5:
                mount = parts[5]
                pct = parts[4].replace("%", "")
                try:
                    result[mount] = {
                        "total": int(parts[1]),
                        "used": int(parts[2]),
                        "available": int(parts[3]),
                        "percent": float(pct),
                    }
                except:
                    pass

    return result


def get_load_average() -> Tuple:
    """Get system load average."""
    code, stdout, _ = run_command("cat /proc/loadavg", check=False)
    if code == 0 and stdout:
        parts = stdout.strip().split()
        if len(parts) >= 3:
            try:
                return (float(parts[0]), float(parts[1]), float(parts[2]))
            except:
                pass
    return (0.0, 0.0, 0.0)


def get_swap_usage() -> Dict:
    """Get swap usage."""
    result = {
        "total": 0,
        "used": 0,
        "free": 0,
        "percent": 0.0,
    }

    code, stdout, _ = run_command("free -b | grep -i swap", check=False)
    if code == 0 and stdout:
        parts = stdout.split()
        if len(parts) >= 4:
            try:
                result["total"] = int(parts[1])
                result["used"] = int(parts[2])
                result["free"] = int(parts[3])
                if result["total"] > 0:
                    result["percent"] = (result["used"] / result["total"]) * 100
            except:
                pass

    return result


def get_cpu_count() -> int:
    """Get number of CPU cores."""
    code, stdout, _ = run_command("nproc", check=False)
    if code == 0 and stdout:
        try:
            return int(stdout.strip())
        except:
            pass
    return 1


def collect_all_metrics() -> Dict:
    """Collect all system metrics."""
    cpu_count = get_cpu_count()
    load = get_load_average()

    return {
        "timestamp": datetime.now().isoformat(),
        "cpu": get_cpu_usage(),
        "memory": get_memory_usage(),
        "disk": get_disk_usage(),
        "load": {
            "1min": load[0],
            "5min": load[1],
            "15min": load[2],
            "per_cpu": load[0] / cpu_count if cpu_count > 0 else 0,
        },
        "swap": get_swap_usage(),
        "cpu_count": cpu_count,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

def show_current_status():
    """Show current system status with threshold checking."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitoring", "Current Status"])

    console.print("\n[bold]📊 Current System Status[/bold]\n")

    thresholds = load_thresholds()
    metrics = collect_all_metrics()

    # CPU
    cpu = metrics["cpu"]
    cpu_status = get_status_icon(cpu, thresholds["cpu_warning"], thresholds["cpu_critical"])

    # Memory
    mem = metrics["memory"]
    mem_pct = mem["percent"]
    mem_status = get_status_icon(mem_pct, thresholds["memory_warning"], thresholds["memory_critical"])

    # Disk
    disk = metrics["disk"]
    root_pct = disk.get("/", {}).get("percent", 0)
    disk_status = get_status_icon(root_pct, thresholds["disk_warning"], thresholds["disk_critical"])

    # Load
    load = metrics["load"]
    load_per_cpu = load["per_cpu"]
    load_status = get_status_icon(load_per_cpu, thresholds["load_warning"], thresholds["load_critical"])

    # Swap
    swap = metrics["swap"]
    swap_pct = swap["percent"]
    swap_status = get_status_icon(swap_pct, thresholds["swap_warning"], thresholds["swap_critical"])

    # Display table
    table = Table(box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Current")
    table.add_column("Threshold")
    table.add_column("Status")

    table.add_row(
        "CPU Usage",
        f"{cpu:.1f}%",
        f"W: {thresholds['cpu_warning']}% / C: {thresholds['cpu_critical']}%",
        cpu_status,
    )

    table.add_row(
        "Memory Usage",
        f"{mem_pct:.1f}% ({format_bytes(mem['used'])} / {format_bytes(mem['total'])})",
        f"W: {thresholds['memory_warning']}% / C: {thresholds['memory_critical']}%",
        mem_status,
    )

    table.add_row(
        "Disk Usage (/)",
        f"{root_pct:.1f}%",
        f"W: {thresholds['disk_warning']}% / C: {thresholds['disk_critical']}%",
        disk_status,
    )

    table.add_row(
        "Load Average",
        f"{load['1min']:.2f} / {load['5min']:.2f} / {load['15min']:.2f} (per CPU: {load_per_cpu:.2f})",
        f"W: {thresholds['load_warning']} / C: {thresholds['load_critical']}",
        load_status,
    )

    table.add_row(
        "Swap Usage",
        f"{swap_pct:.1f}% ({format_bytes(swap['used'])} / {format_bytes(swap['total'])})",
        f"W: {thresholds['swap_warning']}% / C: {thresholds['swap_critical']}%",
        swap_status,
    )

    console.print(table)

    # Check for alerts
    check_and_generate_alerts(metrics, thresholds)

    # Show disk partitions
    if len(disk) > 1:
        console.print("\n[bold]💾 Disk Partitions:[/bold]\n")
        for mount, info in disk.items():
            pct = info["percent"]
            if pct >= 90:
                status = "[red]CRITICAL[/red]"
            elif pct >= 80:
                status = "[yellow]WARNING[/yellow]"
            else:
                status = "[green]OK[/green]"
            console.print(f"  {mount}: {pct:.1f}% used ({format_bytes(info['available'])} free) - {status}")

    questionary.press_any_key_to_continue().ask()


def get_status_icon(value: float, warning: float, critical: float) -> str:
    """Get status icon based on thresholds."""
    if value >= critical:
        return "[red]🔴 CRITICAL[/red]"
    elif value >= warning:
        return "[yellow]🟡 WARNING[/yellow]"
    else:
        return "[green]🟢 OK[/green]"


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_val) < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"


def check_and_generate_alerts(metrics: Dict, thresholds: Dict):
    """Check metrics against thresholds and generate alerts."""
    # CPU
    cpu = metrics["cpu"]
    if cpu >= thresholds["cpu_critical"]:
        add_alert("cpu", cpu, thresholds["cpu_critical"], "critical",
                  f"CPU usage is {cpu:.1f}% (threshold: {thresholds['cpu_critical']}%)")
    elif cpu >= thresholds["cpu_warning"]:
        add_alert("cpu", cpu, thresholds["cpu_warning"], "warning",
                  f"CPU usage is {cpu:.1f}% (threshold: {thresholds['cpu_warning']}%)")

    # Memory
    mem_pct = metrics["memory"]["percent"]
    if mem_pct >= thresholds["memory_critical"]:
        add_alert("memory", mem_pct, thresholds["memory_critical"], "critical",
                  f"Memory usage is {mem_pct:.1f}% (threshold: {thresholds['memory_critical']}%)")
    elif mem_pct >= thresholds["memory_warning"]:
        add_alert("memory", mem_pct, thresholds["memory_warning"], "warning",
                  f"Memory usage is {mem_pct:.1f}% (threshold: {thresholds['memory_warning']}%)")

    # Disk
    for mount, info in metrics["disk"].items():
        pct = info["percent"]
        if pct >= thresholds["disk_critical"]:
            add_alert(f"disk_{mount}", pct, thresholds["disk_critical"], "critical",
                      f"Disk {mount} is {pct:.1f}% full (threshold: {thresholds['disk_critical']}%)")
        elif pct >= thresholds["disk_warning"]:
            add_alert(f"disk_{mount}", pct, thresholds["disk_warning"], "warning",
                      f"Disk {mount} is {pct:.1f}% full (threshold: {thresholds['disk_warning']}%)")

    # Load
    load_per_cpu = metrics["load"]["per_cpu"]
    if load_per_cpu >= thresholds["load_critical"]:
        add_alert("load", load_per_cpu, thresholds["load_critical"], "critical",
                  f"Load per CPU is {load_per_cpu:.2f} (threshold: {thresholds['load_critical']})")
    elif load_per_cpu >= thresholds["load_warning"]:
        add_alert("load", load_per_cpu, thresholds["load_warning"], "warning",
                  f"Load per CPU is {load_per_cpu:.2f} (threshold: {thresholds['load_warning']})")

    # Swap
    swap_pct = metrics["swap"]["percent"]
    if swap_pct >= thresholds["swap_critical"]:
        add_alert("swap", swap_pct, thresholds["swap_critical"], "critical",
                  f"Swap usage is {swap_pct:.1f}% (threshold: {thresholds['swap_critical']}%)")
    elif swap_pct >= thresholds["swap_warning"]:
        add_alert("swap", swap_pct, thresholds["swap_warning"], "warning",
                  f"Swap usage is {swap_pct:.1f}% (threshold: {thresholds['swap_warning']}%)")


# ═══════════════════════════════════════════════════════════════════════════════
# HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

def show_usage_history():
    """Show resource usage history."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitoring", "History"])

    console.print("\n[bold]📈 Resource Usage History[/bold]\n")

    history = load_history()

    if not history:
        print_info("No history data. Run 'Record Current Metrics' or setup monitoring cron.")
        questionary.press_any_key_to_continue().ask()
        return

    # Select time range
    range_choice = questionary.select(
        "View history for:",
        choices=[
            {"name": "Last 1 hour", "value": 1},
            {"name": "Last 6 hours", "value": 6},
            {"name": "Last 24 hours", "value": 24},
            {"name": "Last 7 days", "value": 168},
        ],
    ).ask()

    if not range_choice:
        return

    # Filter by time
    cutoff = datetime.now() - timedelta(hours=range_choice)
    filtered = []
    for entry in history:
        try:
            ts = datetime.fromisoformat(entry["timestamp"])
            if ts >= cutoff:
                filtered.append(entry)
        except:
            pass

    if not filtered:
        print_info(f"No data for the last {range_choice} hours.")
        questionary.press_any_key_to_continue().ask()
        return

    # Calculate statistics
    cpu_values = [e.get("cpu", 0) for e in filtered]
    mem_values = [e.get("memory", {}).get("percent", 0) for e in filtered]

    root_disk_values = []
    for e in filtered:
        disk = e.get("disk", {})
        if "/" in disk:
            root_disk_values.append(disk["/"].get("percent", 0))

    table = Table(title=f"📊 Statistics (Last {range_choice}h)", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Min")
    table.add_column("Max")
    table.add_column("Average")
    table.add_column("Current")

    if cpu_values:
        table.add_row(
            "CPU Usage",
            f"{min(cpu_values):.1f}%",
            f"{max(cpu_values):.1f}%",
            f"{sum(cpu_values)/len(cpu_values):.1f}%",
            f"{cpu_values[-1]:.1f}%",
        )

    if mem_values:
        table.add_row(
            "Memory Usage",
            f"{min(mem_values):.1f}%",
            f"{max(mem_values):.1f}%",
            f"{sum(mem_values)/len(mem_values):.1f}%",
            f"{mem_values[-1]:.1f}%",
        )

    if root_disk_values:
        table.add_row(
            "Disk Usage (/)",
            f"{min(root_disk_values):.1f}%",
            f"{max(root_disk_values):.1f}%",
            f"{sum(root_disk_values)/len(root_disk_values):.1f}%",
            f"{root_disk_values[-1]:.1f}%",
        )

    console.print(table)

    console.print(f"\n[dim]Data points: {len(filtered)}[/dim]")
    console.print(f"[dim]First: {filtered[0].get('timestamp', 'N/A')[:19]}[/dim]")
    console.print(f"[dim]Last: {filtered[-1].get('timestamp', 'N/A')[:19]}[/dim]")

    # Show recent entries
    console.print("\n[bold]Recent Entries:[/bold]\n")

    recent_table = Table(box=box.SIMPLE)
    recent_table.add_column("Time")
    recent_table.add_column("CPU")
    recent_table.add_column("Memory")
    recent_table.add_column("Disk")
    recent_table.add_column("Load")

    for entry in filtered[-10:]:
        ts = entry.get("timestamp", "")[:16]
        cpu = f"{entry.get('cpu', 0):.1f}%"
        mem = f"{entry.get('memory', {}).get('percent', 0):.1f}%"
        disk = f"{entry.get('disk', {}).get('/', {}).get('percent', 0):.1f}%"
        load = f"{entry.get('load', {}).get('1min', 0):.2f}"

        recent_table.add_row(ts, cpu, mem, disk, load)

    console.print(recent_table)

    questionary.press_any_key_to_continue().ask()


def record_current_metrics():
    """Record current metrics to history."""
    console.print("[cyan]Recording current metrics...[/cyan]")

    metrics = collect_all_metrics()
    thresholds = load_thresholds()

    # Check for alerts
    check_and_generate_alerts(metrics, thresholds)

    # Save to history
    save_history_entry(metrics)

    print_success("Metrics recorded!")
    console.print(f"[dim]CPU: {metrics['cpu']:.1f}% | Memory: {metrics['memory']['percent']:.1f}% | "
                  f"Disk: {metrics['disk'].get('/', {}).get('percent', 0):.1f}%[/dim]")

    questionary.press_any_key_to_continue().ask()


def clear_monitoring_history():
    """Clear monitoring history."""
    if confirm_action("Clear all monitoring history?"):
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
        print_success("History cleared!")

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# ALERTS
# ═══════════════════════════════════════════════════════════════════════════════

def view_active_alerts():
    """View active (unacknowledged) alerts."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitoring", "Active Alerts"])

    console.print("\n[bold]🔔 Active Alerts[/bold]\n")

    alerts = load_alerts()
    active = [a for a in alerts if not a.get("acknowledged")]

    if not active:
        console.print(Panel(
            "[green]✓ No active alerts![/green]\n\n"
            "All systems are operating within normal thresholds.",
            title="✅ All Clear",
            border_style="green",
        ))
        questionary.press_any_key_to_continue().ask()
        return

    # Sort by severity (critical first)
    active.sort(key=lambda x: (0 if x.get("severity") == "critical" else 1, x.get("timestamp")))

    table = Table(box=box.ROUNDED, header_style="bold red")
    table.add_column("ID", style="dim")
    table.add_column("Time")
    table.add_column("Metric", style="cyan")
    table.add_column("Value")
    table.add_column("Severity")
    table.add_column("Message")

    for alert in active:
        severity = alert.get("severity", "unknown")
        if severity == "critical":
            sev_display = "[red]🔴 CRITICAL[/red]"
        else:
            sev_display = "[yellow]🟡 WARNING[/yellow]"

        table.add_row(
            str(alert.get("id", "")),
            alert.get("timestamp", "")[:16],
            alert.get("metric", ""),
            f"{alert.get('value', 0):.1f}",
            sev_display,
            alert.get("message", "")[:40],
        )

    console.print(table)

    console.print(f"\n[bold]Total active alerts: {len(active)}[/bold]")

    questionary.press_any_key_to_continue().ask()


def view_alert_history():
    """View all alerts including acknowledged."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitoring", "Alert History"])

    console.print("\n[bold]📋 Alert History[/bold]\n")

    alerts = load_alerts()

    if not alerts:
        print_info("No alert history.")
        questionary.press_any_key_to_continue().ask()
        return

    # Show last 30 alerts
    table = Table(box=box.SIMPLE)
    table.add_column("Time")
    table.add_column("Metric")
    table.add_column("Severity")
    table.add_column("Value")
    table.add_column("Status")

    for alert in reversed(alerts[-30:]):
        severity = alert.get("severity", "unknown")
        if severity == "critical":
            sev_display = "[red]CRITICAL[/red]"
        else:
            sev_display = "[yellow]WARNING[/yellow]"

        ack = "[green]✓ Ack[/green]" if alert.get("acknowledged") else "[dim]Active[/dim]"

        table.add_row(
            alert.get("timestamp", "")[:16],
            alert.get("metric", ""),
            sev_display,
            f"{alert.get('value', 0):.1f}",
            ack,
        )

    console.print(table)

    console.print(f"\n[dim]Total alerts: {len(alerts)}[/dim]")

    questionary.press_any_key_to_continue().ask()


def acknowledge_all_alerts():
    """Acknowledge all active alerts."""
    alerts = load_alerts()
    active = [a for a in alerts if not a.get("acknowledged")]

    if not active:
        print_info("No active alerts to acknowledge.")
        questionary.press_any_key_to_continue().ask()
        return

    if confirm_action(f"Acknowledge {len(active)} alerts?"):
        for alert in alerts:
            alert["acknowledged"] = True
        save_alerts(alerts)
        print_success(f"Acknowledged {len(active)} alerts!")

    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

def configure_thresholds():
    """Configure alert thresholds."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitoring", "Thresholds"])

    console.print("\n[bold]⚙️ Configure Alert Thresholds[/bold]\n")

    thresholds = load_thresholds()

    table = Table(title="Current Thresholds", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Warning", style="yellow")
    table.add_column("Critical", style="red")

    table.add_row("CPU Usage", f"{thresholds['cpu_warning']}%", f"{thresholds['cpu_critical']}%")
    table.add_row("Memory Usage", f"{thresholds['memory_warning']}%", f"{thresholds['memory_critical']}%")
    table.add_row("Disk Usage", f"{thresholds['disk_warning']}%", f"{thresholds['disk_critical']}%")
    table.add_row("Load (per CPU)", str(thresholds['load_warning']), str(thresholds['load_critical']))
    table.add_row("Swap Usage", f"{thresholds['swap_warning']}%", f"{thresholds['swap_critical']}%")

    console.print(table)

    if not confirm_action("Modify thresholds?"):
        return

    # CPU
    cpu_warning = questionary.text(
        "CPU Warning threshold (%):",
        default=str(thresholds["cpu_warning"]),
    ).ask()
    if cpu_warning:
        thresholds["cpu_warning"] = int(cpu_warning)

    cpu_critical = questionary.text(
        "CPU Critical threshold (%):",
        default=str(thresholds["cpu_critical"]),
    ).ask()
    if cpu_critical:
        thresholds["cpu_critical"] = int(cpu_critical)

    # Memory
    mem_warning = questionary.text(
        "Memory Warning threshold (%):",
        default=str(thresholds["memory_warning"]),
    ).ask()
    if mem_warning:
        thresholds["memory_warning"] = int(mem_warning)

    mem_critical = questionary.text(
        "Memory Critical threshold (%):",
        default=str(thresholds["memory_critical"]),
    ).ask()
    if mem_critical:
        thresholds["memory_critical"] = int(mem_critical)

    # Disk
    disk_warning = questionary.text(
        "Disk Warning threshold (%):",
        default=str(thresholds["disk_warning"]),
    ).ask()
    if disk_warning:
        thresholds["disk_warning"] = int(disk_warning)

    disk_critical = questionary.text(
        "Disk Critical threshold (%):",
        default=str(thresholds["disk_critical"]),
    ).ask()
    if disk_critical:
        thresholds["disk_critical"] = int(disk_critical)

    save_thresholds(thresholds)
    print_success("Thresholds updated!")

    questionary.press_any_key_to_continue().ask()


def setup_monitoring_cron():
    """Setup cron for periodic monitoring."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitoring", "Setup Cron"])

    console.print("\n[bold]⏰ Setup Monitoring Cron[/bold]\n")

    interval = questionary.select(
        "Monitoring interval:",
        choices=[
            {"name": "Every 5 minutes (recommended)", "value": "*/5"},
            {"name": "Every 15 minutes", "value": "*/15"},
            {"name": "Every 30 minutes", "value": "*/30"},
            {"name": "Every hour", "value": "0"},
        ],
    ).ask()

    if not interval:
        return

    if interval == "0":
        cron_expr = "0 * * * *"
    else:
        cron_expr = f"{interval} * * * *"

    # Create monitoring script
    script_path = Path.home() / ".forge" / "scripts" / "monitor.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)

    script_content = """#!/bin/bash
# Forge CLI Monitoring Script
cd "$(dirname "$0")"
forge monitor record 2>/dev/null || python3 -c "
from monitoring import collect_all_metrics, save_history_entry, check_and_generate_alerts, load_thresholds
metrics = collect_all_metrics()
check_and_generate_alerts(metrics, load_thresholds())
save_history_entry(metrics)
" 2>/dev/null
"""

    with open(script_path, "w") as f:
        f.write(script_content)
    run_command(f"chmod +x {script_path}", check=False)

    cron_line = f"{cron_expr} /usr/local/bin/forge monitor record 2>/dev/null"

    # Add to crontab
    code, existing, _ = run_command("crontab -l 2>/dev/null", check=False)
    existing = existing if code == 0 else ""

    new_lines = [l for l in existing.split("\n") if "forge monitor" not in l.lower()]
    new_lines.append("# Forge system monitoring")
    new_lines.append(cron_line)

    new_crontab = "\n".join(new_lines).strip() + "\n"
    run_command(f"echo '{new_crontab}' | crontab -", check=False)

    print_success(f"Monitoring cron configured ({cron_expr})!")
    questionary.press_any_key_to_continue().ask()


def configure_notifications():
    """Configure notification settings."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Monitoring", "Notifications"])

    console.print("\n[bold]📧 Configure Notifications[/bold]\n")

    console.print("[dim]Coming soon: Email, Slack, Discord, and webhook notifications![/dim]")
    console.print("\n[dim]For now, alerts are stored locally and can be viewed in the menu.[/dim]")

    questionary.press_any_key_to_continue().ask()


# Import for typing
from typing import Tuple
