"""
PHP Management - Install PHP versions, extensions, and manage configurations
"""

import os
import re
import questionary
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

from utils.ui import (
    clear_screen, print_header, print_breadcrumb,
    print_success, print_error, print_warning, print_info, confirm_action
)
from utils.shell import run_command, get_command_output, command_exists
from state import add_pending_operation, complete_pending_operation, get_pending_operations

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# PHP DATA
# ═══════════════════════════════════════════════════════════════════════════════

# Available PHP versions (from Ondřej PPA)
PHP_VERSIONS = ["8.5", "8.4", "8.3", "8.2", "8.1", "8.0", "7.4"]

# Common PHP extensions with descriptions
PHP_EXTENSIONS = {
    # Database
    "mysql": {"desc": "MySQL/MariaDB support", "category": "database"},
    "pgsql": {"desc": "PostgreSQL support", "category": "database"},
    "sqlite3": {"desc": "SQLite3 support", "category": "database"},
    "redis": {"desc": "Redis support", "category": "database"},
    "memcached": {"desc": "Memcached support", "category": "database"},
    "mongodb": {"desc": "MongoDB support", "category": "database"},

    # Web & API
    "curl": {"desc": "cURL library support", "category": "web"},
    "soap": {"desc": "SOAP protocol support", "category": "web"},
    "xml": {"desc": "XML parsing & manipulation", "category": "web"},
    "xmlrpc": {"desc": "XML-RPC support", "category": "web"},
    "json": {"desc": "JSON encoding/decoding (usually built-in)", "category": "web"},

    # String & Text
    "mbstring": {"desc": "Multibyte string support", "category": "text"},
    "intl": {"desc": "Internationalization functions", "category": "text"},
    "iconv": {"desc": "Character set conversion", "category": "text"},
    "gettext": {"desc": "GNU gettext support", "category": "text"},

    # Image & Media
    "gd": {"desc": "Image manipulation (GD library)", "category": "media"},
    "imagick": {"desc": "ImageMagick support", "category": "media"},
    "exif": {"desc": "EXIF metadata support", "category": "media"},

    # Compression
    "zip": {"desc": "ZIP archive support", "category": "compression"},
    "zlib": {"desc": "ZLIB compression", "category": "compression"},
    "bz2": {"desc": "Bzip2 compression", "category": "compression"},

    # Security & Encryption
    "openssl": {"desc": "OpenSSL cryptographic functions", "category": "security"},
    "sodium": {"desc": "Sodium cryptographic library", "category": "security"},
    "mcrypt": {"desc": "Mcrypt encryption (deprecated)", "category": "security"},

    # Development
    "xdebug": {"desc": "Debugging and profiling", "category": "dev"},
    "opcache": {"desc": "Opcode caching (performance)", "category": "dev"},
    "apcu": {"desc": "APC user cache", "category": "dev"},

    # System
    "fpm": {"desc": "FastCGI Process Manager", "category": "system"},
    "cli": {"desc": "Command line interface", "category": "system"},
    "common": {"desc": "Common PHP files", "category": "system"},
    "dev": {"desc": "Development files & headers", "category": "system"},

    # Laravel/Framework Essentials
    "bcmath": {"desc": "Arbitrary precision math", "category": "framework"},
    "ctype": {"desc": "Character type checking", "category": "framework"},
    "fileinfo": {"desc": "File information functions", "category": "framework"},
    "tokenizer": {"desc": "PHP tokenizer functions", "category": "framework"},
    "pdo": {"desc": "PHP Data Objects (PDO)", "category": "framework"},
    "pdo_mysql": {"desc": "PDO MySQL driver", "category": "framework"},
    "pdo_pgsql": {"desc": "PDO PostgreSQL driver", "category": "framework"},
    "pdo_sqlite": {"desc": "PDO SQLite driver", "category": "framework"},

    # Other
    "ldap": {"desc": "LDAP support", "category": "other"},
    "imap": {"desc": "IMAP email support", "category": "other"},
    "gmp": {"desc": "GNU Multiple Precision", "category": "other"},
    "readline": {"desc": "GNU Readline support", "category": "other"},
    "sockets": {"desc": "Socket functions", "category": "other"},
    "pcntl": {"desc": "Process control", "category": "other"},
    "posix": {"desc": "POSIX functions", "category": "other"},
}

# Extension bundles for quick installation
EXTENSION_BUNDLES = {
    "laravel": {
        "name": "🔷 Laravel Essentials",
        "desc": "All extensions required for Laravel",
        "extensions": [
            "cli", "fpm", "common", "mysql", "pgsql", "sqlite3", "redis",
            "mbstring", "xml", "curl", "zip", "bcmath", "ctype", "fileinfo",
            "tokenizer", "pdo", "pdo_mysql", "pdo_pgsql", "gd", "intl", "opcache"
        ],
    },
    "wordpress": {
        "name": "📝 WordPress Essentials",
        "desc": "All extensions required for WordPress",
        "extensions": [
            "cli", "fpm", "common", "mysql", "curl", "gd", "mbstring",
            "xml", "zip", "intl", "imagick", "exif", "opcache"
        ],
    },
    "basic": {
        "name": "📦 Basic Web Server",
        "desc": "Minimal extensions for PHP web apps",
        "extensions": [
            "cli", "fpm", "common", "mysql", "mbstring", "xml", "curl", "zip", "gd"
        ],
    },
    "full": {
        "name": "🎯 Full Stack",
        "desc": "All commonly used extensions",
        "extensions": list(PHP_EXTENSIONS.keys()),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# PHP MENU
# ═══════════════════════════════════════════════════════════════════════════════

PHP_MENU_CHOICES = [
    {"name": "📋  View Installed PHP", "value": "status"},
    {"name": "📥  Install PHP Version", "value": "install_version"},
    {"name": "🔌  Install Extensions", "value": "install_ext"},
    {"name": "📦  Install Bundle", "value": "install_bundle"},
    {"name": "🔍  Check Extensions", "value": "check_ext"},
    questionary.Separator("─" * 30),
    {"name": "⚙️   Configure PHP-FPM", "value": "configure"},
    {"name": "🔄  Switch Default PHP", "value": "switch"},
    questionary.Separator("─" * 30),
    {"name": "⬅️   Back", "value": "back"},
]


def run_php_menu():
    """Display the PHP management menu."""
    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "PHP Management"])

        choice = questionary.select(
            "PHP Management:",
            choices=PHP_MENU_CHOICES,
            qmark="🐘",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        if choice == "status":
            show_php_status()
        elif choice == "install_version":
            install_php_version()
        elif choice == "install_ext":
            install_php_extensions()
        elif choice == "install_bundle":
            install_extension_bundle()
        elif choice == "check_ext":
            check_installed_extensions()
        elif choice == "configure":
            configure_php_fpm()
        elif choice == "switch":
            switch_default_php()


# ═══════════════════════════════════════════════════════════════════════════════
# PHP STATUS
# ═══════════════════════════════════════════════════════════════════════════════

def show_php_status():
    """Show detailed PHP installation status."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "PHP Management", "Status"])

    console.print("\n[bold]🐘 PHP Installation Status[/bold]\n")

    # Get installed PHP versions
    installed = get_installed_php_versions()

    if not installed:
        print_warning("No PHP versions detected.")
        print_info("Use 'Install PHP Version' to install PHP.")
        questionary.press_any_key_to_continue().ask()
        return

    # Create table
    table = Table(
        title="Installed PHP Versions",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Version", style="cyan")
    table.add_column("CLI", justify="center")
    table.add_column("FPM", justify="center")
    table.add_column("FPM Status", justify="center")
    table.add_column("Default", justify="center")

    default_version = get_default_php_version()

    for version in installed:
        # Check CLI
        cli_installed = check_package_installed(f"php{version}-cli")
        cli_status = "🟢" if cli_installed else "⚪"

        # Check FPM
        fpm_installed = check_package_installed(f"php{version}-fpm")
        fpm_status = "🟢" if fpm_installed else "⚪"

        # Check FPM service status
        if fpm_installed:
            code, stdout, _ = run_command(f"systemctl is-active php{version}-fpm", check=False)
            if stdout.strip() == "active":
                fpm_service = "[green]Running[/green]"
            else:
                fpm_service = "[dim]Stopped[/dim]"
        else:
            fpm_service = "-"

        # Check if default
        is_default = "⭐" if version == default_version else ""

        table.add_row(f"PHP {version}", cli_status, fpm_status, fpm_service, is_default)

    console.print(table)

    # Show default version info
    if default_version:
        console.print(f"\n[dim]Default PHP: {default_version}[/dim]")

        # Show binary path
        code, stdout, _ = run_command("which php", check=False)
        if code == 0:
            console.print(f"[dim]Binary: {stdout.strip()}[/dim]")

    console.print()
    questionary.press_any_key_to_continue().ask()


def get_installed_php_versions() -> List[str]:
    """Get list of installed PHP versions."""
    installed = []
    for version in PHP_VERSIONS:
        if check_package_installed(f"php{version}-cli") or check_package_installed(f"php{version}-fpm"):
            installed.append(version)
    return installed


def get_default_php_version() -> Optional[str]:
    """Get the default PHP version."""
    code, stdout, _ = run_command("php -v 2>/dev/null | head -1", check=False)
    if code == 0 and stdout:
        match = re.search(r"PHP (\d+\.\d+)", stdout)
        if match:
            return match.group(1)
    return None


def check_package_installed(package: str) -> bool:
    """Check if a package is installed."""
    code, _, _ = run_command(f"dpkg -s {package} 2>/dev/null | grep -q 'Status: install ok installed'", check=False)
    return code == 0


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALL PHP VERSION
# ═══════════════════════════════════════════════════════════════════════════════

def install_php_version():
    """Install a specific PHP version."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "PHP Management", "Install Version"])

    console.print("\n[bold]📥 Install PHP Version[/bold]\n")

    # Get currently installed versions
    installed = get_installed_php_versions()

    # Build choices
    choices = []
    for version in PHP_VERSIONS:
        if version in installed:
            choices.append({"name": f"PHP {version} [dim](installed)[/dim]", "value": version, "disabled": "Already installed"})
        else:
            choices.append({"name": f"PHP {version}", "value": version})

    # Add "install all" option
    choices.insert(0, {"name": "🎯 Install ALL versions", "value": "all"})
    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    selection = questionary.select(
        "Select PHP version to install:",
        choices=choices,
    ).ask()

    if not selection:
        return

    versions_to_install = PHP_VERSIONS if selection == "all" else [selection]
    versions_to_install = [v for v in versions_to_install if v not in installed]

    if not versions_to_install:
        print_info("All selected versions are already installed.")
        questionary.press_any_key_to_continue().ask()
        return

    # Select extensions to install with the version
    console.print("\n[bold]Select extensions to install:[/bold]")

    bundle_choice = questionary.select(
        "Choose extension bundle:",
        choices=[
            {"name": "🔷 Laravel Essentials (recommended)", "value": "laravel"},
            {"name": "📦 Basic Web Server", "value": "basic"},
            {"name": "🎯 Full Stack (all extensions)", "value": "full"},
            {"name": "⚙️  Minimal (CLI + FPM only)", "value": "minimal"},
            {"name": "🔧 Custom selection", "value": "custom"},
        ],
    ).ask()

    if bundle_choice == "minimal":
        extensions = ["cli", "fpm", "common"]
    elif bundle_choice == "custom":
        extensions = select_extensions_interactive()
        if not extensions:
            return
    else:
        extensions = EXTENSION_BUNDLES.get(bundle_choice, {}).get("extensions", ["cli", "fpm"])

    # Confirm installation
    console.print(f"\n[bold]Will install:[/bold]")
    for v in versions_to_install:
        console.print(f"  • PHP {v}")
    console.print(f"\n[bold]Extensions:[/bold] {', '.join(extensions)}")
    console.print()

    if not confirm_action("Proceed with installation?"):
        return

    # Ensure Ondřej PPA is added
    ensure_php_ppa()

    # Install each version
    for version in versions_to_install:
        console.print(f"\n[bold cyan]Installing PHP {version}...[/bold cyan]\n")

        # Build package list
        packages = [f"php{version}-{ext}" for ext in extensions]
        package_str = " ".join(packages)

        # Track operation
        op_id = add_pending_operation("php_install", {
            "version": version,
            "extensions": extensions,
            "started_at": datetime.now().isoformat(),
        })

        # Run installation
        code, stdout, stderr = run_command(
            f"sudo apt-get install -y {package_str}",
            check=False
        )

        if code == 0:
            print_success(f"PHP {version} installed successfully!")
            complete_pending_operation(op_id)
        else:
            print_error(f"Failed to install PHP {version}: {stderr}")
            # Try individual packages
            console.print("[dim]Trying individual packages...[/dim]")
            for pkg in packages:
                run_command(f"sudo apt-get install -y {pkg}", check=False)

    console.print()
    questionary.press_any_key_to_continue().ask()


def ensure_php_ppa():
    """Ensure Ondřej PHP PPA is installed."""
    code, _, _ = run_command("grep -q ondrej/php /etc/apt/sources.list.d/*", check=False)
    if code != 0:
        console.print("[cyan]Adding Ondřej PHP PPA...[/cyan]")
        run_command("sudo add-apt-repository -y ppa:ondrej/php", check=False)
        run_command("sudo apt-get update", check=False)


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALL EXTENSIONS
# ═══════════════════════════════════════════════════════════════════════════════

def install_php_extensions():
    """Install PHP extensions for a specific version."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "PHP Management", "Extensions"])

    console.print("\n[bold]🔌 Install PHP Extensions[/bold]\n")

    # Get installed versions
    installed = get_installed_php_versions()

    if not installed:
        print_warning("No PHP versions installed.")
        print_info("Install a PHP version first.")
        questionary.press_any_key_to_continue().ask()
        return

    # Select PHP version
    version = questionary.select(
        "Select PHP version:",
        choices=[{"name": f"PHP {v}", "value": v} for v in installed] +
                [questionary.Separator(), {"name": "⬅️ Cancel", "value": None}],
    ).ask()

    if not version:
        return

    # Get currently installed extensions
    current_extensions = get_installed_extensions(version)

    # Select extensions to install
    extensions = select_extensions_interactive(version, current_extensions)

    if not extensions:
        return

    # Confirm
    console.print(f"\n[bold]Installing for PHP {version}:[/bold]")
    for ext in extensions:
        desc = PHP_EXTENSIONS.get(ext, {}).get("desc", "")
        console.print(f"  • {ext} [dim]- {desc}[/dim]")

    console.print()
    if not confirm_action("Proceed with installation?"):
        return

    # Install extensions
    install_extensions_for_version(version, extensions)

    questionary.press_any_key_to_continue().ask()


def select_extensions_interactive(version: str = None, installed: List[str] = None) -> List[str]:
    """Interactive extension selection."""
    installed = installed or []

    # Group by category
    categories = {}
    for ext, info in PHP_EXTENSIONS.items():
        cat = info.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ext)

    # Build checkbox choices
    choices = []
    for category, exts in sorted(categories.items()):
        choices.append(questionary.Separator(f"\n── {category.upper()} ──"))
        for ext in sorted(exts):
            info = PHP_EXTENSIONS[ext]
            status = " [dim](installed)[/dim]" if ext in installed else ""
            name = f"{ext} - {info['desc']}{status}"
            choices.append({"name": name, "value": ext, "checked": ext not in installed and ext in ["cli", "fpm", "common"]})

    selected = questionary.checkbox(
        "Select extensions to install:",
        choices=choices,
    ).ask()

    return selected or []


def install_extensions_for_version(version: str, extensions: List[str]):
    """Install extensions for a specific PHP version."""
    packages = [f"php{version}-{ext}" for ext in extensions]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Installing extensions...", total=len(packages))

        for pkg in packages:
            progress.update(task, description=f"Installing {pkg}...")
            code, _, stderr = run_command(f"sudo apt-get install -y {pkg}", check=False)

            if code != 0:
                console.print(f"[yellow]⚠ Failed to install {pkg}[/yellow]")

            progress.advance(task)

    # Restart PHP-FPM if running
    code, stdout, _ = run_command(f"systemctl is-active php{version}-fpm", check=False)
    if stdout.strip() == "active":
        run_command(f"sudo systemctl restart php{version}-fpm", check=False)
        print_info(f"Restarted PHP {version} FPM")

    print_success("Extension installation complete!")


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALL BUNDLE
# ═══════════════════════════════════════════════════════════════════════════════

def install_extension_bundle():
    """Install a predefined extension bundle."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "PHP Management", "Bundles"])

    console.print("\n[bold]📦 Install Extension Bundle[/bold]\n")

    # Get installed versions
    installed = get_installed_php_versions()

    if not installed:
        print_warning("No PHP versions installed.")
        questionary.press_any_key_to_continue().ask()
        return

    # Select PHP version
    version = questionary.select(
        "Select PHP version:",
        choices=[{"name": f"PHP {v}", "value": v} for v in installed] +
                [questionary.Separator(), {"name": "⬅️ Cancel", "value": None}],
    ).ask()

    if not version:
        return

    # Select bundle
    bundle_choices = []
    for key, bundle in EXTENSION_BUNDLES.items():
        bundle_choices.append({
            "name": f"{bundle['name']} - {bundle['desc']}",
            "value": key,
        })
    bundle_choices.append(questionary.Separator())
    bundle_choices.append({"name": "⬅️ Cancel", "value": None})

    bundle_key = questionary.select(
        "Select bundle:",
        choices=bundle_choices,
    ).ask()

    if not bundle_key:
        return

    bundle = EXTENSION_BUNDLES[bundle_key]
    extensions = bundle["extensions"]

    # Show what will be installed
    console.print(f"\n[bold]{bundle['name']}[/bold]")
    console.print(f"[dim]{bundle['desc']}[/dim]\n")
    console.print("[bold]Extensions:[/bold]")
    for ext in extensions:
        desc = PHP_EXTENSIONS.get(ext, {}).get("desc", "")
        console.print(f"  • {ext} [dim]- {desc}[/dim]")

    console.print()
    if not confirm_action("Install this bundle?"):
        return

    install_extensions_for_version(version, extensions)
    questionary.press_any_key_to_continue().ask()


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK INSTALLED EXTENSIONS
# ═══════════════════════════════════════════════════════════════════════════════

def check_installed_extensions():
    """Check which extensions are installed for each PHP version."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "PHP Management", "Check Extensions"])

    console.print("\n[bold]🔍 Installed PHP Extensions[/bold]\n")

    # Get installed versions
    installed_versions = get_installed_php_versions()

    if not installed_versions:
        print_warning("No PHP versions installed.")
        questionary.press_any_key_to_continue().ask()
        return

    # Select version or show all
    choices = [{"name": "📋 Show all versions", "value": "all"}]
    choices.extend([{"name": f"PHP {v}", "value": v} for v in installed_versions])
    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    selection = questionary.select(
        "Select PHP version:",
        choices=choices,
    ).ask()

    if not selection:
        return

    versions_to_check = installed_versions if selection == "all" else [selection]

    for version in versions_to_check:
        console.print(f"\n[bold cyan]PHP {version} Extensions:[/bold cyan]\n")

        extensions = get_installed_extensions(version)

        if extensions:
            # Group by category
            categorized = {}
            for ext in extensions:
                cat = PHP_EXTENSIONS.get(ext, {}).get("category", "other")
                if cat not in categorized:
                    categorized[cat] = []
                categorized[cat].append(ext)

            for category in sorted(categorized.keys()):
                exts = sorted(categorized[category])
                console.print(f"[bold]{category.upper()}:[/bold]")
                for ext in exts:
                    desc = PHP_EXTENSIONS.get(ext, {}).get("desc", "")
                    console.print(f"  🟢 {ext} [dim]- {desc}[/dim]")
                console.print()
        else:
            print_warning("No extensions found or unable to detect.")

    # Also show PHP modules via php -m
    if len(versions_to_check) == 1:
        version = versions_to_check[0]
        console.print(f"\n[bold]Loaded modules (php{version} -m):[/bold]\n")
        code, stdout, _ = run_command(f"php{version} -m 2>/dev/null", check=False)
        if code == 0:
            modules = [m for m in stdout.split("\n") if m and not m.startswith("[")]
            console.print("[dim]" + ", ".join(sorted(modules)) + "[/dim]")

    console.print()
    questionary.press_any_key_to_continue().ask()


def get_installed_extensions(version: str) -> List[str]:
    """Get list of installed extensions for a PHP version."""
    extensions = []

    # Check via dpkg
    code, stdout, _ = run_command(f"dpkg -l | grep php{version}- | awk '{{print $2}}'", check=False)
    if code == 0 and stdout:
        for line in stdout.split("\n"):
            if line.startswith(f"php{version}-"):
                ext = line.replace(f"php{version}-", "")
                if ext:
                    extensions.append(ext)

    return list(set(extensions))


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURE PHP-FPM
# ═══════════════════════════════════════════════════════════════════════════════

def get_server_specs() -> Dict:
    """Get server specifications for pool calculation."""
    specs = {
        "ram_total": 0,       # in bytes
        "ram_available": 0,
        "swap_total": 0,
        "swap_available": 0,
        "cpu_count": 1,
    }

    # Get RAM
    code, stdout, _ = run_command("grep MemTotal /proc/meminfo | awk '{print $2}'", check=False)
    if code == 0 and stdout:
        specs["ram_total"] = int(stdout.strip()) * 1024  # KB to bytes

    code, stdout, _ = run_command("grep MemAvailable /proc/meminfo | awk '{print $2}'", check=False)
    if code == 0 and stdout:
        specs["ram_available"] = int(stdout.strip()) * 1024

    # Get Swap
    code, stdout, _ = run_command("grep SwapTotal /proc/meminfo | awk '{print $2}'", check=False)
    if code == 0 and stdout:
        specs["swap_total"] = int(stdout.strip()) * 1024

    code, stdout, _ = run_command("grep SwapFree /proc/meminfo | awk '{print $2}'", check=False)
    if code == 0 and stdout:
        specs["swap_available"] = int(stdout.strip()) * 1024

    # Get CPU count
    code, stdout, _ = run_command("nproc", check=False)
    if code == 0 and stdout:
        specs["cpu_count"] = int(stdout.strip())

    return specs


def calculate_fpm_pool_settings(specs: Dict, avg_process_mb: int = 50) -> Dict:
    """
    Calculate optimal PHP-FPM pool settings based on server specs.

    Args:
        specs: Server specifications from get_server_specs()
        avg_process_mb: Average memory per PHP-FPM process (default 50MB)

    Returns:
        Dict with recommended pool settings
    """
    ram_mb = specs["ram_total"] / 1024 / 1024
    swap_mb = specs["swap_total"] / 1024 / 1024
    cpu_count = specs["cpu_count"]

    # Reserve memory for system (OS, MySQL, Nginx, etc.)
    # Small server: 30%, Medium: 25%, Large: 20%
    if ram_mb <= 1024:
        reserved_pct = 0.40  # 40% reserved for small servers
        server_size = "small"
    elif ram_mb <= 4096:
        reserved_pct = 0.30  # 30% reserved
        server_size = "medium"
    elif ram_mb <= 16384:
        reserved_pct = 0.25  # 25% reserved
        server_size = "large"
    else:
        reserved_pct = 0.20  # 20% reserved for big servers
        server_size = "enterprise"

    available_for_php = ram_mb * (1 - reserved_pct)

    # Add portion of swap (25% as emergency buffer)
    if swap_mb > 0:
        available_for_php += swap_mb * 0.25

    # Calculate max_children
    max_children = int(available_for_php / avg_process_mb)
    max_children = max(2, min(max_children, 500))  # Clamp between 2 and 500

    # Calculate other values based on max_children and CPU
    if server_size == "small":
        pm_type = "ondemand"
        start_servers = 2
        min_spare = 1
        max_spare = 3
    elif server_size == "medium":
        pm_type = "dynamic"
        start_servers = max(2, cpu_count)
        min_spare = max(1, cpu_count // 2)
        max_spare = max(3, cpu_count * 2)
    else:
        pm_type = "dynamic"
        start_servers = max(4, cpu_count * 2)
        min_spare = max(2, cpu_count)
        max_spare = max(6, cpu_count * 4)

    # Ensure values are sane
    start_servers = min(start_servers, max_children // 2)
    min_spare = min(min_spare, start_servers)
    max_spare = min(max_spare, max_children // 2)

    return {
        "pm": pm_type,
        "pm.max_children": max_children,
        "pm.start_servers": start_servers,
        "pm.min_spare_servers": min_spare,
        "pm.max_spare_servers": max_spare,
        "pm.max_requests": 500,
        "pm.process_idle_timeout": "10s",
        "server_size": server_size,
        "ram_mb": int(ram_mb),
        "swap_mb": int(swap_mb),
        "cpu_count": cpu_count,
        "available_for_php_mb": int(available_for_php),
        "avg_process_mb": avg_process_mb,
    }


def configure_php_fpm():
    """Configure PHP-FPM settings with smart recommendations."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "PHP Management", "Configure"])

    console.print("\n[bold]⚙️ Configure PHP-FPM[/bold]\n")

    # Get installed versions
    installed = get_installed_php_versions()
    installed = [v for v in installed if check_package_installed(f"php{v}-fpm")]

    if not installed:
        print_warning("No PHP-FPM versions installed.")
        questionary.press_any_key_to_continue().ask()
        return

    # Select version
    version = questionary.select(
        "Select PHP version:",
        choices=[{"name": f"PHP {v}-fpm", "value": v} for v in installed] +
                [questionary.Separator(), {"name": "⬅️ Cancel", "value": None}],
    ).ask()

    if not version:
        return

    # Show current config
    console.print(f"\n[bold]Current PHP {version} settings:[/bold]\n")

    settings = {
        "memory_limit": get_php_ini_value(version, "memory_limit"),
        "upload_max_filesize": get_php_ini_value(version, "upload_max_filesize"),
        "post_max_size": get_php_ini_value(version, "post_max_size"),
        "max_execution_time": get_php_ini_value(version, "max_execution_time"),
        "max_input_vars": get_php_ini_value(version, "max_input_vars"),
    }

    for key, value in settings.items():
        console.print(f"  {key}: [cyan]{value}[/cyan]")

    # Select what to configure
    console.print("\n[bold]Configuration options:[/bold]")

    config_choice = questionary.select(
        "Select configuration:",
        choices=[
            {"name": "🔧 Increase memory limit", "value": "memory"},
            {"name": "📤 Increase upload size", "value": "upload"},
            {"name": "⏱️  Increase execution time", "value": "time"},
            {"name": "🚀 Apply production optimizations", "value": "production"},
            {"name": "⚡ Smart Pool Configuration", "value": "smart_pool"},
            {"name": "🔧 Custom Pool Configuration", "value": "custom_pool"},
            {"name": "⬅️  Cancel", "value": None},
        ],
    ).ask()

    if not config_choice:
        return

    if config_choice == "memory":
        new_value = questionary.text("New memory_limit:", default="512M").ask()
        set_php_ini_value(version, "memory_limit", new_value)
    elif config_choice == "upload":
        new_value = questionary.text("New upload_max_filesize:", default="100M").ask()
        set_php_ini_value(version, "upload_max_filesize", new_value)
        set_php_ini_value(version, "post_max_size", new_value)
    elif config_choice == "time":
        new_value = questionary.text("New max_execution_time (seconds):", default="300").ask()
        set_php_ini_value(version, "max_execution_time", new_value)
    elif config_choice == "production":
        apply_production_php_config(version)
    elif config_choice == "smart_pool":
        configure_smart_pool(version)
    elif config_choice == "custom_pool":
        configure_custom_pool(version)
        return  # Custom pool handles restart

    # Restart PHP-FPM
    run_command(f"sudo systemctl restart php{version}-fpm", check=False)
    print_success(f"PHP {version}-fpm restarted with new configuration!")

    questionary.press_any_key_to_continue().ask()


def configure_smart_pool(version: str):
    """Configure PHP-FPM pool with smart recommendations based on server specs."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "PHP Management", "Smart Pool"])

    console.print("\n[bold]⚡ Smart Pool Configuration[/bold]\n")
    console.print("[cyan]Analyzing server specifications...[/cyan]\n")

    # Get server specs
    specs = get_server_specs()

    # Display server info
    ram_gb = specs["ram_total"] / 1024 / 1024 / 1024
    swap_gb = specs["swap_total"] / 1024 / 1024 / 1024

    table = Table(title="📊 Server Specifications", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value")

    table.add_row("Total RAM", f"{ram_gb:.1f} GB")
    table.add_row("Available RAM", f"{specs['ram_available'] / 1024 / 1024 / 1024:.1f} GB")
    table.add_row("Total Swap", f"{swap_gb:.1f} GB" if swap_gb > 0 else "[yellow]No swap configured[/yellow]")
    table.add_row("CPU Cores", str(specs["cpu_count"]))

    console.print(table)

    # Warning if no swap
    if specs["swap_total"] == 0:
        console.print("\n[yellow]⚠️  Warning: No swap configured. Consider adding swap for stability.[/yellow]")
        console.print("[dim]Use: Disk Management → Swap Management[/dim]\n")

    # Ask for average process memory
    avg_process = questionary.select(
        "Average PHP process memory:",
        choices=[
            {"name": "30 MB (Simple sites, static content)", "value": 30},
            {"name": "50 MB (Standard Laravel/WordPress)", "value": 50},
            {"name": "80 MB (Heavy applications, large models)", "value": 80},
            {"name": "100 MB (Very heavy applications)", "value": 100},
            {"name": "150 MB (Memory-intensive apps)", "value": 150},
        ],
    ).ask()

    if not avg_process:
        return

    # Calculate recommendations
    pool_settings = calculate_fpm_pool_settings(specs, avg_process)

    # Display recommendations
    console.print(f"\n[bold]🎯 Recommended Settings for {pool_settings['server_size'].upper()} server:[/bold]\n")

    rec_table = Table(box=box.ROUNDED, header_style="bold green")
    rec_table.add_column("Setting", style="cyan")
    rec_table.add_column("Value")
    rec_table.add_column("Explanation", style="dim")

    rec_table.add_row(
        "pm",
        pool_settings["pm"],
        "ondemand=low RAM, dynamic=production"
    )
    rec_table.add_row(
        "pm.max_children",
        str(pool_settings["pm.max_children"]),
        f"Max PHP workers ({pool_settings['available_for_php_mb']}MB/{avg_process}MB)"
    )
    rec_table.add_row(
        "pm.start_servers",
        str(pool_settings["pm.start_servers"]),
        "PHP workers at startup"
    )
    rec_table.add_row(
        "pm.min_spare_servers",
        str(pool_settings["pm.min_spare_servers"]),
        "Min idle workers"
    )
    rec_table.add_row(
        "pm.max_spare_servers",
        str(pool_settings["pm.max_spare_servers"]),
        "Max idle workers"
    )
    rec_table.add_row(
        "pm.max_requests",
        str(pool_settings["pm.max_requests"]),
        "Requests before worker restart"
    )

    console.print(rec_table)

    # Display summary
    console.print(Panel(
        f"[bold]Summary:[/bold]\n\n"
        f"• Server: {pool_settings['ram_mb']} MB RAM, {pool_settings['swap_mb']} MB Swap, {pool_settings['cpu_count']} CPUs\n"
        f"• Reserved for system: {int(pool_settings['ram_mb'] * (1 - pool_settings['available_for_php_mb']/pool_settings['ram_mb']))} MB\n"
        f"• Available for PHP: {pool_settings['available_for_php_mb']} MB\n"
        f"• Max concurrent requests: {pool_settings['pm.max_children']}\n",
        title="📋 Configuration Summary",
        border_style="green",
    ))

    # Confirm with user
    console.print("[yellow]⚠️  Important: This will modify your PHP-FPM pool configuration![/yellow]\n")

    if not confirm_action("Apply these recommended settings?"):
        return

    # Apply settings
    apply_pool_settings(version, pool_settings)

    # Restart PHP-FPM
    console.print("\n[cyan]Restarting PHP-FPM...[/cyan]")
    run_command(f"sudo systemctl restart php{version}-fpm", check=False)

    print_success(f"PHP {version}-fpm pool configured and restarted!")

    questionary.press_any_key_to_continue().ask()


def configure_custom_pool(version: str):
    """Configure PHP-FPM pool with custom values."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "PHP Management", "Custom Pool"])

    console.print("\n[bold]🔧 Custom Pool Configuration[/bold]\n")

    # Read current pool settings
    pool_file = f"/etc/php/{version}/fpm/pool.d/www.conf"

    console.print(f"[dim]Pool file: {pool_file}[/dim]\n")

    # Get current values
    current = {
        "pm": read_pool_setting(version, "pm"),
        "pm.max_children": read_pool_setting(version, "pm.max_children"),
        "pm.start_servers": read_pool_setting(version, "pm.start_servers"),
        "pm.min_spare_servers": read_pool_setting(version, "pm.min_spare_servers"),
        "pm.max_spare_servers": read_pool_setting(version, "pm.max_spare_servers"),
    }

    console.print("[bold]Current settings:[/bold]")
    for key, value in current.items():
        console.print(f"  {key}: [cyan]{value}[/cyan]")

    console.print()

    # Get new values
    pm_type = questionary.select(
        "Process Manager type (pm):",
        choices=[
            {"name": "dynamic - Maintains pool based on load", "value": "dynamic"},
            {"name": "ondemand - Spawns processes on demand (low memory)", "value": "ondemand"},
            {"name": "static - Fixed number of processes", "value": "static"},
        ],
        default=current.get("pm", "dynamic"),
    ).ask()

    if not pm_type:
        return

    max_children = questionary.text(
        "pm.max_children (max PHP workers):",
        default=current.get("pm.max_children", "50"),
    ).ask()

    new_settings = {"pm": pm_type, "pm.max_children": int(max_children)}

    if pm_type != "ondemand":
        start_servers = questionary.text(
            "pm.start_servers:",
            default=current.get("pm.start_servers", "5"),
        ).ask()
        new_settings["pm.start_servers"] = int(start_servers)

    if pm_type == "dynamic":
        min_spare = questionary.text(
            "pm.min_spare_servers:",
            default=current.get("pm.min_spare_servers", "2"),
        ).ask()
        max_spare = questionary.text(
            "pm.max_spare_servers:",
            default=current.get("pm.max_spare_servers", "10"),
        ).ask()
        new_settings["pm.min_spare_servers"] = int(min_spare)
        new_settings["pm.max_spare_servers"] = int(max_spare)

    new_settings["pm.max_requests"] = 500

    # Confirm
    console.print("\n[bold]New settings:[/bold]")
    for key, value in new_settings.items():
        console.print(f"  {key}: [green]{value}[/green]")

    if not confirm_action("Apply these settings?"):
        return

    # Apply
    apply_pool_settings(version, new_settings)

    # Restart
    console.print("\n[cyan]Restarting PHP-FPM...[/cyan]")
    run_command(f"sudo systemctl restart php{version}-fpm", check=False)

    print_success(f"PHP {version}-fpm pool configured!")

    questionary.press_any_key_to_continue().ask()


def read_pool_setting(version: str, key: str) -> str:
    """Read a setting from the PHP-FPM pool config."""
    pool_file = f"/etc/php/{version}/fpm/pool.d/www.conf"
    code, stdout, _ = run_command(f"grep '^{key} =' {pool_file} 2>/dev/null | head -1", check=False)

    if code == 0 and stdout:
        parts = stdout.split("=")
        if len(parts) >= 2:
            return parts[1].strip()
    return ""


def apply_pool_settings(version: str, settings: Dict):
    """Apply PHP-FPM pool settings."""
    pool_file = f"/etc/php/{version}/fpm/pool.d/www.conf"

    for key, value in settings.items():
        if key in ["server_size", "ram_mb", "swap_mb", "cpu_count", "available_for_php_mb", "avg_process_mb"]:
            continue  # Skip metadata

        # Use sed to update the value
        run_command(
            f"sudo sed -i 's/^{key} = .*/{key} = {value}/' {pool_file}",
            check=False
        )

        # Also try commented version
        run_command(
            f"sudo sed -i 's/^;{key} = .*/{key} = {value}/' {pool_file}",
            check=False
        )

        console.print(f"  [green]✓[/green] Set {key} = {value}")

    # Add emergency restart settings
    run_command(
        f"sudo sed -i 's/^;emergency_restart_threshold.*/emergency_restart_threshold = 10/' /etc/php/{version}/fpm/php-fpm.conf",
        check=False
    )
    run_command(
        f"sudo sed -i 's/^;emergency_restart_interval.*/emergency_restart_interval = 1m/' /etc/php/{version}/fpm/php-fpm.conf",
        check=False
    )


def get_php_ini_value(version: str, key: str) -> str:
    """Get a PHP ini value."""
    code, stdout, _ = run_command(f"php{version} -i 2>/dev/null | grep '^{key}' | head -1", check=False)
    if code == 0 and stdout:
        parts = stdout.split("=>")
        if len(parts) >= 2:
            return parts[-1].strip()
    return "unknown"


def set_php_ini_value(version: str, key: str, value: str):
    """Set a PHP ini value."""
    ini_file = f"/etc/php/{version}/fpm/php.ini"

    # Use sed to replace or add the value
    code, _, _ = run_command(f"sudo sed -i 's/^{key} = .*/{key} = {value}/' {ini_file}", check=False)

    if code != 0:
        # Try to add if not exists
        run_command(f"echo '{key} = {value}' | sudo tee -a {ini_file}", check=False)

    print_info(f"Set {key} = {value}")


def apply_production_php_config(version: str):
    """Apply production-optimized PHP configuration."""
    settings = {
        "memory_limit": "512M",
        "upload_max_filesize": "100M",
        "post_max_size": "100M",
        "max_execution_time": "300",
        "max_input_vars": "3000",
        "opcache.enable": "1",
        "opcache.memory_consumption": "256",
        "opcache.max_accelerated_files": "20000",
        "opcache.validate_timestamps": "0",
    }

    for key, value in settings.items():
        set_php_ini_value(version, key, value)

    print_success("Applied production optimizations!")


# ═══════════════════════════════════════════════════════════════════════════════
# SWITCH DEFAULT PHP
# ═══════════════════════════════════════════════════════════════════════════════

def switch_default_php():
    """Switch the default PHP version."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "PHP Management", "Switch Version"])

    console.print("\n[bold]🔄 Switch Default PHP Version[/bold]\n")

    # Get installed versions
    installed = get_installed_php_versions()

    if len(installed) < 2:
        print_warning("Need at least 2 PHP versions installed to switch.")
        questionary.press_any_key_to_continue().ask()
        return

    current = get_default_php_version()
    console.print(f"[dim]Current default: PHP {current}[/dim]\n")

    # Select new version
    choices = []
    for v in installed:
        if v == current:
            choices.append({"name": f"PHP {v} [dim](current)[/dim]", "value": v})
        else:
            choices.append({"name": f"PHP {v}", "value": v})

    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    new_version = questionary.select(
        "Select new default version:",
        choices=choices,
    ).ask()

    if not new_version or new_version == current:
        return

    console.print(f"\n[cyan]Switching to PHP {new_version}...[/cyan]")

    # Use update-alternatives
    run_command(f"sudo update-alternatives --set php /usr/bin/php{new_version}", check=False)
    run_command(f"sudo update-alternatives --set phar /usr/bin/phar{new_version}", check=False)
    run_command(f"sudo update-alternatives --set phar.phar /usr/bin/phar.phar{new_version}", check=False)

    # Verify
    new_default = get_default_php_version()
    if new_default == new_version:
        print_success(f"Default PHP switched to {new_version}!")
    else:
        print_warning("Switch may not have worked. Check with 'php -v'")

    questionary.press_any_key_to_continue().ask()
