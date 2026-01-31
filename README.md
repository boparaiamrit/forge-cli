# 🔧 Forge CLI

<p align="center">
  <strong>Server Management CLI — Like Laravel Forge, but for your terminal.</strong>
</p>

<p align="center">
  A beautiful, interactive command-line tool for provisioning and managing Ubuntu servers.<br>
  Install packages, create Nginx sites, provision SSL certificates, harden security, and manage services — all from a single unified interface.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Ubuntu-20.04%20|%2022.04+-orange?logo=ubuntu&logoColor=white" alt="Ubuntu">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

## 📖 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
  - [System Status](#-system-status)
  - [Package Installation](#-package-installation)
  - [Site Management](#-site-management)
  - [SSL Certificates](#-ssl-certificates)
  - [Service Management](#️-service-management)
  - [Server Hardening](#️-server-hardening)
- [Keyboard Shortcuts](#-keyboard-shortcuts)
- [Project Structure](#-project-structure)
- [Development & Testing](#-development--testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 **System Status** | Real-time detection of installed software with versions and status |
| 📦 **Package Installer** | Interactive multi-select installation of server packages |
| 🌐 **Site Management** | Create Nginx configs for Next.js, Nuxt, PHP/Laravel, and static sites |
| 🔒 **SSL Certificates** | Provision Let's Encrypt SSL via HTTP or DNS verification |
| ⚙️ **Service Control** | Start, stop, restart services and view logs |
| 🛡️ **Server Hardening** | SSH hardening, UFW firewall, Fail2Ban, kernel hardening |

### Supported Software

| Category | Packages |
|----------|----------|
| **Web Servers** | Nginx |
| **Languages** | PHP 8.1, 8.2, 8.3 (with 30+ extensions), Node.js (via NVM) |
| **Databases** | MySQL 8, PostgreSQL |
| **Caching** | Redis |
| **Tools** | Composer, PM2, Certbot |

---

## 📋 Prerequisites

- **Operating System**: Ubuntu 20.04 LTS or 22.04 LTS
- **Python**: 3.10 or higher
- **Access**: Root or sudo privileges

---

## 🚀 Installation

### Method 1: Clone & Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/forge-cli.git
cd forge-cli

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Forge CLI in development mode
pip install -e .
```

### Method 2: One-Line Installer

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/forge-cli/main/install.sh | bash
```

### Method 3: Docker (For Testing)

```bash
cd forge-cli
docker compose up --build
```

---

## 🎯 Quick Start

After installation, simply run:

```bash
forge
```

Or run directly without installation:

```bash
python cli.py
```

You'll see the main menu:

```
╔═══════════════════════════════════════════════════════════════╗
║                        🔧 FORGE CLI                           ║
║              Server Management Made Beautiful                  ║
╚═══════════════════════════════════════════════════════════════╝

📍 Main

? What would you like to do?
  ▶ 📊  System Status
    📦  Install Packages
    🌐  Manage Sites
    🔒  SSL Certificates
    ⚙️   Services
    ──────────────────────────────
    ❌  Exit
```

---

## 📚 Usage Guide

### 📊 System Status

View the installation status of all server software at a glance.

**Navigate to:** `Main → System Status`

```
🖥️  Server Software Status
┌──────────────┬─────────────┬─────────┬──────────────┐
│ Software     │ Status      │ Version │ Details      │
├──────────────┼─────────────┼─────────┼──────────────┤
│ 🌐 Nginx     │ 🟢 Installed│ 1.24.0  │ Running      │
│ 🐘 PHP       │ 🟢 Installed│ 8.3.1   │ 45 extensions│
│ 🟢 Node.js   │ 🟢 Installed│ 20.11.0 │ via NVM      │
│ ⚡ PM2       │ 🟢 Installed│ 5.3.0   │ 3 processes  │
│ 🔴 Redis     │ 🟢 Installed│ 7.2.3   │ Running      │
│ 🔒 Certbot   │ 🟢 Installed│ 2.8.0   │ Let's Encrypt│
│ 🗄️  MySQL    │ 🔴 Not Found│ -       │              │
│ 🐘 PostgreSQL│ 🟢 Installed│ 15.4    │              │
│ 📦 Composer  │ 🟢 Installed│ 2.6.5   │              │
└──────────────┴─────────────┴─────────┴──────────────┘
```

**Status Indicators:**
- 🟢 **Installed** - Software is installed and detected
- 🔴 **Not Found** - Software is not installed
- **Running/Stopped** - Service status (for services)

---

### 📦 Package Installation

Install multiple packages with a single command using interactive checkboxes.

**Navigate to:** `Main → Install Packages`

```
📍 Main › Install Packages

📦 Select packages to install (Space to select, Enter to confirm):
  ◯ 🌐 Nginx
  ◉ 🐘 PHP 8.3
  ◉ 🐘 PHP 8.2
  ◉ 🟢 Node.js (via NVM)
  ◯ ⚡ PM2 Process Manager
  ◉ 🔴 Redis
  ◉ 🔒 Certbot (Let's Encrypt)
  ◯ 📦 Composer
  ◯ 🗄️  MySQL 8
  ◯ 🐘 PostgreSQL
```

**Installation Details:**

| Package | What Gets Installed |
|---------|---------------------|
| **Nginx** | nginx, enabled & started |
| **PHP 8.x** | php-fpm, cli, mysql, pgsql, redis, mbstring, xml, curl, zip, bcmath, gd, intl, readline, opcache |
| **Node.js** | NVM (Node Version Manager), latest LTS version |
| **PM2** | Global npm package for process management |
| **Redis** | redis-server, enabled & started |
| **Certbot** | certbot, python3-certbot-nginx |
| **Composer** | Latest Composer in /usr/local/bin |
| **MySQL 8** | mysql-server, enabled & started |
| **PostgreSQL** | postgresql, postgresql-contrib, enabled & started |

---

### 🌐 Site Management

Create and manage Nginx virtual host configurations for different application types.

**Navigate to:** `Main → Manage Sites`

```
📍 Main › Manage Sites

🌐 Site Management:
  ▶ 📋  List Sites
    ➕  Create Site
    🗑️   Delete Site
    🔄  Enable/Disable Site
    ──────────────────────────────
    ⬅️   Back
```

#### Creating a New Site

**Step 1: Choose Site Type**

```
🌐 Select site type:
  ▶ ⚡ Next.js         → Reverse proxy to Node port
    🟢 Nuxt.js         → Reverse proxy to Node port
    🐘 PHP / Laravel   → PHP-FPM with document root
    📄 Static HTML     → Direct file serving
```

**Step 2: Configure Domain**

```
? Enter domain name (e.g., example.com): myapp.com
? Include www.myapp.com? Yes
```

**Step 3: Type-Specific Configuration**

For **Next.js/Nuxt.js**:
```
? Enter application port: 3000
```

For **PHP/Laravel**:
```
? Enter document root path: /var/www/myapp.com/public
? Select PHP version: 8.3
```

For **Static HTML**:
```
? Enter document root path: /var/www/myapp.com
```

**Step 4: Review & Confirm**

```
Generated Configuration:
─────────────────────────
# myapp.com - Next.js Application
# Generated by Forge CLI

server {
    listen 80;
    listen [::]:80;
    server_name myapp.com www.myapp.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

? Create this site? Yes
✓ Site myapp.com created and enabled!
? Would you like to set up SSL? Yes
```

#### Site Templates

| Type | Configuration |
|------|---------------|
| **Next.js** | Reverse proxy with WebSocket support, headers for real IP |
| **Nuxt.js** | Reverse proxy with WebSocket support, headers for real IP |
| **PHP/Laravel** | PHP-FPM socket, try_files for pretty URLs, hidden file protection |
| **Static** | Direct serving with try_files, hidden file protection |

---

### 🔒 SSL Certificates

Provision free SSL certificates from Let's Encrypt using Certbot.

**Navigate to:** `Main → SSL Certificates`

```
📍 Main › SSL Certificates

🔒 SSL Certificate Management:
  ▶ 🔐  Provision SSL Certificate
    📋  List Certificates
    🔄  Renew Certificates
    🗑️   Revoke Certificate
    ──────────────────────────────
    ⬅️   Back
```

#### Provisioning a Certificate

**HTTP Verification (Recommended for most cases)**

```
? Enter domain name: myapp.com
? Include www.myapp.com? Yes
? Select verification method:
  ▶ 🌐 HTTP (requires port 80 access)
    📝 DNS (manual DNS record)

Provisioning SSL certificate via HTTP verification...
✓ SSL certificate provisioned for myapp.com!
✓ HTTPS is now enabled
```

**DNS Verification (For wildcards or when port 80 is blocked)**

```
? Select verification method: DNS

DNS Verification Required
─────────────────────────
You will need to add a TXT record to your DNS.

Run this command manually:
sudo certbot certonly --manual --preferred-challenges dns -d myapp.com

DNS TXT Record format:
  Name:  _acme-challenge.myapp.com
  Type:  TXT
  Value: (provided by certbot)

? Run certbot now? Yes
```

#### Certificate Management

| Action | Description |
|--------|-------------|
| **List** | View all installed certificates with expiry dates |
| **Renew** | Force renewal of all certificates |
| **Revoke** | Permanently revoke and delete a certificate |

---

### ⚙️ Service Management

Control systemd services directly from the CLI.

**Navigate to:** `Main → Services`

```
📍 Main › Services

⚙️ Service Management:
  ▶ 📋  Service Status
    ▶️   Start Service
    ⏹️   Stop Service
    🔄  Restart Service
    📜  View Logs
    ──────────────────────────────
    ⬅️   Back
```

#### Service Status

```
⚙️ Service Status
┌─────────────────┬───────────┬────────┐
│ Service         │ Status    │ Active │
├─────────────────┼───────────┼────────┤
│ 🌐 Nginx        │ 🟢 Running│ Yes    │
│ 🐘 PHP-FPM 8.3  │ 🟢 Running│ Yes    │
│ 🐘 PHP-FPM 8.2  │ ⚪ Stopped│ No     │
│ 🔴 Redis        │ 🟢 Running│ Yes    │
│ 🗄️  MySQL       │ ⚪ Stopped│ No     │
│ 🐘 PostgreSQL   │ 🟢 Running│ Yes    │
└─────────────────┴───────────┴────────┘
```

#### Viewing Logs

```
? Select service to view logs: 🌐 Nginx
? Number of lines to show: 50

Last 50 log entries for nginx:
[journalctl output appears here]
```

---

### 🛡️ Server Hardening

**Note:** Server hardening features are available via the Python API. Interactive menu coming soon!

```python
from provisioning.hardening import run_full_hardening

# Run all hardening steps
results = run_full_hardening()
```

#### Hardening Features

| Feature | What It Does |
|---------|--------------|
| **SSH Hardening** | Disable root login, disable password auth, limit auth attempts, Protocol 2 only |
| **UFW Firewall** | Default deny incoming, allow SSH/HTTP/HTTPS only |
| **Fail2Ban** | Brute-force protection for SSH and Nginx |
| **Auto Updates** | Enable unattended security updates |
| **Kernel Hardening** | sysctl settings for IP spoofing, SYN flood protection, etc. |
| **Shared Memory** | Secure /run/shm with noexec,nosuid |
| **Logwatch** | Install log monitoring |

#### Individual Hardening Functions

```python
from provisioning.hardening import (
    harden_ssh,           # Secure SSH configuration
    setup_firewall,       # Configure UFW
    setup_fail2ban,       # Install & configure Fail2Ban
    disable_unused_services,  # Stop unnecessary services
    setup_automatic_updates,  # Enable unattended-upgrades
    secure_shared_memory,     # Secure /run/shm
    setup_sysctl_hardening,   # Kernel-level security
    create_deploy_user,       # Create non-root deploy user
)

# Example: Create a deploy user with sudo access
create_deploy_user("deploy")

# Example: Harden SSH
harden_ssh()
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate menu options |
| `Enter` | Select/confirm option |
| `Space` | Toggle checkbox (in multi-select) |
| `q` | Go back / Quit |
| `Ctrl+C` | Force quit |

---

## 📁 Project Structure

```
forge-cli/
├── cli.py                  # Main menu & navigation logic
├── __init__.py             # Package version
├── __main__.py             # Entry point (python -m forge)
│
├── detectors/              # System software detection
│   └── __init__.py         # detect_nginx(), detect_php(), etc.
│
├── installers/             # Package installation
│   └── __init__.py         # install_nginx(), install_php(), etc.
│
├── sites/                  # Nginx site management
│   └── __init__.py         # Templates & create_site(), delete_site()
│
├── sslcerts/               # SSL certificate management
│   └── __init__.py         # provision_ssl(), renew_certificates()
│
├── services/               # Systemd service control
│   └── __init__.py         # manage_service(), view_logs()
│
├── provisioning/           # Server provisioning & hardening
│   ├── config.py           # PHP versions, extensions, defaults
│   └── hardening.py        # Security hardening functions
│
├── utils/                  # Shared utilities
│   ├── __init__.py         # Re-exports
│   ├── ui.py               # print_success(), print_error(), etc.
│   └── shell.py            # run_command(), command_exists()
│
├── tests/                  # Test suite
│   ├── test_detectors.py
│   ├── test_installers.py
│   ├── test_sites.py
│   ├── test_ssl.py
│   ├── test_services.py
│   ├── test_hardening.py
│   └── test_shell.py
│
├── Dockerfile              # Docker test environment
├── docker-compose.yml      # Docker Compose config
├── pyproject.toml          # Package configuration
├── requirements.txt        # Python dependencies
├── pytest.ini              # Pytest configuration
├── install.sh              # One-line installer script
└── README.md               # This file
```

---

## 🧪 Development & Testing

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/forge-cli.git
cd forge-cli

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-mock

# Install in editable mode
pip install -e .
```

### Running Tests

**Using Docker (Recommended):**
```bash
docker compose up --build
```

**Locally:**
```bash
pytest -v tests/
```

**With Coverage:**
```bash
pip install pytest-cov
pytest --cov=. --cov-report=html tests/
```

### Test Categories

| Test File | What It Tests |
|-----------|---------------|
| `test_detectors.py` | Software detection (Nginx, PHP, Node, etc.) |
| `test_installers.py` | Package installation commands |
| `test_sites.py` | Nginx template rendering & validation |
| `test_ssl.py` | SSL provisioning functions |
| `test_services.py` | Service management |
| `test_hardening.py` | Server hardening functions |
| `test_shell.py` | Shell utilities (run_command, etc.) |

---

## ❓ Troubleshooting

### Common Issues

**"Command not found: forge"**
```bash
# Ensure the virtual environment is activated
source venv/bin/activate

# Or use the full path
./venv/bin/forge
```

**"Permission denied"**
```bash
# Many commands require sudo - run Forge with sudo if needed
sudo forge

# Or ensure your user has sudo privileges
sudo usermod -aG sudo $USER
```

**"Port 80 already in use"**
```bash
# Check what's using port 80
sudo lsof -i :80

# Stop Apache if it's running
sudo systemctl stop apache2
sudo systemctl disable apache2
```

**"SSL verification failed"**
- Ensure port 80 is open and accessible from the internet
- Check that your domain's DNS points to this server
- Try DNS verification instead if HTTP is blocked

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest -v tests/`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions
- Write tests for new features

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Inspired by [Laravel Forge](https://forge.laravel.com/) and [Laravel Settler](https://github.com/laravel/settler)
- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Built with [Questionary](https://github.com/tmbo/questionary) for interactive prompts

---

<p align="center">
  Made with ❤️ for the developer community
</p>
