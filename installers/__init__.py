"""
Package Installers - Install server software
"""

import questionary
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from utils.ui import clear_screen, print_header, print_breadcrumb, print_success, print_error
from utils.shell import run_command, command_exists

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# INSTALLER MENU
# ═══════════════════════════════════════════════════════════════════════════════

def check_php_installed(version: str) -> bool:
    """Check if a specific PHP version is installed."""
    code, _, _ = run_command(f"dpkg -l php{version} 2>/dev/null | grep -q '^ii'", check=False)
    return code == 0


def get_packages():
    """Build package list with current installation status."""
    return [
        {"name": "🌐 Nginx", "value": "nginx", "installed": command_exists("nginx")},
        questionary.Separator("─" * 20 + " PHP Versions " + "─" * 20),
        {"name": "🐘 PHP 8.5", "value": "php85", "installed": check_php_installed("8.5")},
        {"name": "🐘 PHP 8.4", "value": "php84", "installed": check_php_installed("8.4")},
        {"name": "🐘 PHP 8.3", "value": "php83", "installed": check_php_installed("8.3")},
        {"name": "🐘 PHP 8.2", "value": "php82", "installed": check_php_installed("8.2")},
        {"name": "🐘 PHP 8.1", "value": "php81", "installed": check_php_installed("8.1")},
        {"name": "🐘 PHP 8.0", "value": "php80", "installed": check_php_installed("8.0")},
        {"name": "🐘 PHP 7.4", "value": "php74", "installed": check_php_installed("7.4")},
        questionary.Separator("─" * 20 + " Databases " + "─" * 20),
        {"name": "🗄️  MySQL 8", "value": "mysql", "installed": command_exists("mysql")},
        {"name": "🗄️  MariaDB", "value": "mariadb", "installed": command_exists("mariadb")},
        {"name": "🐘 PostgreSQL", "value": "postgresql", "installed": command_exists("psql")},
        {"name": "🔴 Redis", "value": "redis", "installed": command_exists("redis-cli")},
        {"name": "💾 Memcached", "value": "memcached", "installed": command_exists("memcached")},
        questionary.Separator("─" * 20 + " Node.js & Tools " + "─" * 20),
        {"name": "🟢 Node.js (via NVM)", "value": "node", "installed": command_exists("node")},
        {"name": "⚡ PM2 Process Manager", "value": "pm2", "installed": command_exists("pm2")},
        {"name": "🔧 Supervisor", "value": "supervisor", "installed": command_exists("supervisorctl")},
        questionary.Separator("─" * 20 + " Web Tools " + "─" * 20),
        {"name": "🔒 Certbot (Let's Encrypt)", "value": "certbot", "installed": command_exists("certbot")},
        {"name": "📦 Composer", "value": "composer", "installed": command_exists("composer")},
        {"name": "🐳 Docker", "value": "docker", "installed": command_exists("docker")},
        {"name": "🐳 Docker Compose", "value": "docker-compose", "installed": command_exists("docker-compose")},
    ]


def run_installer_menu():
    """Display the package installer menu."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Install Packages"])

    # Build choices with installed indicators (checked dynamically)
    packages = get_packages()
    choices = []
    for pkg in packages:
        if isinstance(pkg, questionary.Separator):
            choices.append(pkg)
        else:
            status = " [green]✓[/green]" if pkg.get("installed") else ""
            choices.append({
                "name": f"{pkg['name']}{status}",
                "value": pkg["value"],
                "checked": False,
            })

    selected = questionary.checkbox(
        "Select packages to install (Space to select, Enter to confirm):",
        choices=choices,
        qmark="📦",
    ).ask()

    if not selected:
        return

    console.print()

    for package in selected:
        install_package(package)

    console.print()
    questionary.press_any_key_to_continue(
        message="Press any key to return to main menu..."
    ).ask()


def install_package(package: str):
    """Install a specific package."""
    installers = {
        "nginx": install_nginx,
        "php85": lambda: install_php("8.5"),
        "php84": lambda: install_php("8.4"),
        "php83": lambda: install_php("8.3"),
        "php82": lambda: install_php("8.2"),
        "php81": lambda: install_php("8.1"),
        "php80": lambda: install_php("8.0"),
        "php74": lambda: install_php("7.4"),
        "node": install_node,
        "pm2": install_pm2,
        "redis": install_redis,
        "memcached": install_memcached,
        "certbot": install_certbot,
        "composer": install_composer,
        "mysql": install_mysql,
        "mariadb": install_mariadb,
        "postgresql": install_postgresql,
        "supervisor": install_supervisor,
        "docker": install_docker,
        "docker-compose": install_docker_compose,
    }

    if package in installers:
        installers[package]()


# ═══════════════════════════════════════════════════════════════════════════════
# INDIVIDUAL INSTALLERS
# ═══════════════════════════════════════════════════════════════════════════════

def install_nginx():
    """Install Nginx web server."""
    console.print("[cyan]Installing Nginx...[/cyan]")

    commands = [
        "sudo apt update",
        "sudo apt install -y nginx",
        "sudo systemctl enable nginx",
        "sudo systemctl start nginx",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    print_success("Nginx installed and started!")


def install_php(version: str):
    """Install PHP with common extensions."""
    console.print(f"[cyan]Installing PHP {version}...[/cyan]")

    extensions = [
        "cli", "fpm", "mysql", "pgsql", "sqlite3", "redis",
        "mbstring", "xml", "curl", "zip", "bcmath", "gd",
        "intl", "readline", "opcache",
    ]

    ext_packages = " ".join([f"php{version}-{ext}" for ext in extensions])

    commands = [
        "sudo apt update",
        "sudo add-apt-repository -y ppa:ondrej/php",
        "sudo apt update",
        f"sudo apt install -y php{version} {ext_packages}",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    print_success(f"PHP {version} installed with extensions!")


def install_node():
    """Install Node.js via NVM."""
    console.print("[cyan]Installing Node.js via NVM...[/cyan]")

    # Install NVM
    commands = [
        'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash',
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    console.print("[yellow]NVM installed. Please run:[/yellow]")
    console.print("  source ~/.bashrc")
    console.print("  nvm install --lts")
    print_success("NVM installation complete!")


def install_pm2():
    """Install PM2 process manager."""
    console.print("[cyan]Installing PM2...[/cyan]")

    code, _, stderr = run_command("sudo npm install -g pm2", check=False)
    if code != 0:
        print_error(f"Failed: {stderr}")
        return

    print_success("PM2 installed!")


def install_redis():
    """Install Redis server."""
    console.print("[cyan]Installing Redis...[/cyan]")

    commands = [
        "sudo apt update",
        "sudo apt install -y redis-server",
        "sudo systemctl enable redis-server",
        "sudo systemctl start redis-server",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    print_success("Redis installed and started!")


def install_certbot():
    """Install Certbot for Let's Encrypt."""
    console.print("[cyan]Installing Certbot...[/cyan]")

    commands = [
        "sudo apt update",
        "sudo apt install -y certbot python3-certbot-nginx",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    print_success("Certbot installed!")


def install_composer():
    """Install Composer PHP package manager."""
    console.print("[cyan]Installing Composer...[/cyan]")

    commands = [
        "curl -sS https://getcomposer.org/installer | php",
        "sudo mv composer.phar /usr/local/bin/composer",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    print_success("Composer installed!")


def install_mysql():
    """Install MySQL 8 server."""
    console.print("[cyan]Installing MySQL 8...[/cyan]")

    commands = [
        "sudo apt update",
        "sudo apt install -y mysql-server",
        "sudo systemctl enable mysql",
        "sudo systemctl start mysql",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    console.print("[yellow]Run 'sudo mysql_secure_installation' to secure MySQL[/yellow]")
    print_success("MySQL 8 installed!")


def install_postgresql():
    """Install PostgreSQL server."""
    console.print("[cyan]Installing PostgreSQL...[/cyan]")

    commands = [
        "sudo apt update",
        "sudo apt install -y postgresql postgresql-contrib",
        "sudo systemctl enable postgresql",
        "sudo systemctl start postgresql",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    print_success("PostgreSQL installed!")


def install_mariadb():
    """Install MariaDB server."""
    console.print("[cyan]Installing MariaDB...[/cyan]")

    commands = [
        "sudo apt update",
        "sudo apt install -y mariadb-server",
        "sudo systemctl enable mariadb",
        "sudo systemctl start mariadb",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    console.print("[yellow]Run 'sudo mysql_secure_installation' to secure MariaDB[/yellow]")
    print_success("MariaDB installed!")


def install_memcached():
    """Install Memcached server."""
    console.print("[cyan]Installing Memcached...[/cyan]")

    commands = [
        "sudo apt update",
        "sudo apt install -y memcached libmemcached-tools",
        "sudo systemctl enable memcached",
        "sudo systemctl start memcached",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    print_success("Memcached installed!")


def install_supervisor():
    """Install Supervisor process manager."""
    console.print("[cyan]Installing Supervisor...[/cyan]")

    commands = [
        "sudo apt update",
        "sudo apt install -y supervisor",
        "sudo systemctl enable supervisor",
        "sudo systemctl start supervisor",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    print_success("Supervisor installed!")


def install_docker():
    """Install Docker."""
    console.print("[cyan]Installing Docker...[/cyan]")

    commands = [
        "sudo apt update",
        "sudo apt install -y ca-certificates curl gnupg",
        "sudo install -m 0755 -d /etc/apt/keyrings",
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
        "sudo chmod a+r /etc/apt/keyrings/docker.gpg",
        'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null',
        "sudo apt update",
        "sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
        "sudo systemctl enable docker",
        "sudo systemctl start docker",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    # Add current user to docker group
    run_command("sudo usermod -aG docker $USER", check=False)

    console.print("[yellow]Log out and back in for docker group to take effect[/yellow]")
    print_success("Docker installed!")


def install_docker_compose():
    """Install Docker Compose (standalone)."""
    console.print("[cyan]Installing Docker Compose...[/cyan]")

    # Check if docker compose plugin is already installed
    code, _, _ = run_command("docker compose version", check=False)
    if code == 0:
        print_success("Docker Compose (plugin) is already available via 'docker compose'")
        return

    # Install standalone docker-compose
    commands = [
        'sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" -o /usr/local/bin/docker-compose',
        "sudo chmod +x /usr/local/bin/docker-compose",
    ]

    for cmd in commands:
        code, _, stderr = run_command(cmd, check=False)
        if code != 0:
            print_error(f"Failed: {stderr}")
            return

    print_success("Docker Compose installed!")
