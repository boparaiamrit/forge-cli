<p align="center">
  <img src="assets/forge-icon.png" alt="Forge CLI" width="120" height="120">
</p>

<h1 align="center">🔧 Forge CLI</h1>

<p align="center">
  <strong>Server Management CLI for Ubuntu</strong><br>
  <em>Like Laravel Forge, but for your terminal</em>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/boparaiamrit/forge-cli/releases"><img src="https://img.shields.io/badge/version-0.13.0-green.svg" alt="Version"></a>
</p>

<p align="center">
  A comprehensive, production-ready server management CLI for Ubuntu servers.<br>
  Forge CLI simplifies the process of setting up, configuring, and maintaining web servers<br>
  with support for PHP, Node.js, SSL certificates, and more.
</p>

---

## ✨ Features

### 🚀 Core Functionality
- **Interactive CLI** - Beautiful terminal UI with rich formatting and intuitive navigation
- **System Detection** - Automatically detects installed software and versions
- **One-Click Installation** - Install Nginx, PHP, Node.js, databases with optimized configurations

### 🐘 PHP Management
- **Multiple PHP Versions** - Install and manage PHP 8.5, 8.4, 8.3, 8.2, 8.1, 8.0, 7.4
- **Shared PHP Version Parity** - Site creation and provisioning use the same supported PHP version list
- **Extension Bundles** - Pre-configured bundles for Laravel, WordPress, and more
- **40+ Extensions** - Install any PHP extension with descriptions and categories
- **Smart Pool Configuration** - Dynamic FPM settings based on server RAM/swap
- **Custom Pool Settings** - Manual pm.max_children, start_servers configuration
- **Production Optimizations** - One-click production-ready settings
- **Version Switching** - Seamlessly switch between PHP versions

### 🌐 Site Management
- **Multi-Framework Support** - Next.js, Nuxt.js, PHP/Laravel, Static HTML
- **Modern PHP Site Selection** - PHP sites can target 8.5, 8.4, 8.3, 8.2, 8.1, 8.0, or 7.4
- **Hardened Nginx Templates** - Production-ready configurations with security headers
- **WebSocket Proxy** - Dedicated WS location blocks with Upgrade headers and 86400s keepalive
- **Multiple Upstream Proxies** - Route URL prefixes to different backend ports (e.g., `/api/` → `:8000`)
- **HTTP Basic Auth** - Optional password protection with auto-provisioned htpasswd files
- **SSL Status Display** - See certificate status and expiration at a glance
- **Health Checks** - DNS, HTTP, HTTPS, and SSL validation
- **Live Log Viewing** - Real-time log streaming with color-coded output

### 🔒 SSL Certificates
- **Let's Encrypt Integration** - Free SSL via Certbot
- **HTTP & DNS Verification** - Support for both challenge types
- **Auto-Renewal Setup** - Automatic renewal via systemd timer or cron
- **Renewal Tracking** - Table showing last/next renewal dates
- **Expiry Warnings** - Color-coded expiration alerts

### ⚙️ Service Management
- **Service Dashboard** - Overview of all running/stopped services
- **Auto-Detection** - Discovers installed services automatically
- **11 Categories** - Web, PHP, Database, Cache, Queue, Mail, Monitoring, Security, SSL, System, Docker
- **Quick Actions** - Restart all PHP-FPM, restart web servers, reload all
- **Boot Management** - Enable/disable services on boot
- **Memory & Uptime** - See resource usage and uptime per service

### 🗄️ Database Management
- **Multi-Engine Support** - Manage PostgreSQL, MySQL, and MariaDB from the CLI
- **Database CRUD** - List, create, and delete application databases with confirmation
- **User Management** - List, create, reset passwords, and delete database users
- **Access Grants** - Grant users access to application databases without dropping to raw SQL
- **System Filtering** - Hide system databases and users from routine list views

### 📊 Monitoring & Alerts
- **Live Dashboard** - Real-time CPU, memory, disk, and load stats
- **Historical Data** - Track usage over time (1h, 6h, 24h, 7d views)
- **Alert System** - Automatic alerts when thresholds are exceeded
- **Configurable Thresholds** - Set warning/critical levels for each metric
- **Alert History** - View and acknowledge past alerts
- **Cron Integration** - Periodic metric collection (every 5 minutes)
- **Service Health** - Monitor Nginx, PHP-FPM, MySQL, Redis

### 💾 Disk Management
- **Disk Overview** - Filesystem usage, inodes, and warnings
- **Directory Analysis** - Find space hogs in /var, /home, /tmp
- **Quick Cleanup** - APT cache, old kernels, temp files, old logs
- **Deep Cleanup** - Package caches (pip, npm, composer), journals
- **Docker Cleanup** - Unused images, containers, volumes
- **Log Rotation** - Status, manual rotation, large file detection
- **Large File Finder** - Find files > 100MB, 500MB, 1GB
- **Old File Finder** - Files not accessed in 30-365 days
- **Duplicate Finder** - Find duplicate files (using fdupes)
- **Swap Management** - Create, configure, remove swap files
- **Swappiness Control** - Tune swap behavior for production
- **Cleanup Cron** - Automatic weekly/daily cleanup jobs

### 📜 Log Management
- **Centralized Viewing** - Nginx access/error, site-specific, and system logs
- **Real-Time Monitoring** - Live tail with syntax highlighting
- **Search & Filter** - Find by IP, status code, URL, or keyword
- **Error Summary** - Top errors, IPs, and recent issues

### 📋 State Management & Lineage
- **Persistent State** - Track sites, PHP versions, and configurations
- **State Lineage** - Full audit trail of all changes
- **History Viewer** - See what changed and when
- **Resume Operations** - Recover from interrupted tasks

### ⏰ Cron Jobs
- **List Jobs** - View all user, root, and system cron jobs
- **Preset Schedules** - Common schedules (hourly, daily, weekly, monthly)
- **SSL Auto-Renewal** - Setup automatic certificate renewal
- **Cleanup Jobs** - Clear logs, temp files, PHP sessions
- **Backup Jobs** - Scheduled backups for Nginx, MySQL, PostgreSQL, web files

### 🛡️ Security & Antivirus
- **ClamAV Integration** - Install and manage ClamAV antivirus
- **Quick Scan** - Scan common attack locations (/tmp, /var/www)
- **Web File Scan** - Focus on PHP files and web directories
- **Full System Scan** - Complete filesystem scan with exclusions
- **Scan Reports** - JSON reports with threat details
- **File Change Detection** - Baseline and monitor file changes
- **Scheduled Scans** - Automatic daily/weekly scanning
- **Virus Database Updates** - Keep signatures current

### 🔍 Configuration Auditor
- **Full Audit** - Scan all configurations for issues
- **Nginx Site Audit** - Check security headers, gzip, timeouts, buffers
- **PHP Audit** - Check memory limits, OPcache, production settings
- **Service Audit** - Verify critical services running and enabled on boot
- **Security Audit** - Check firewall, fail2ban, SSH hardening
- **Auto-Fix** - Automatically fix detected issues with one click

### 🛡️ CVE Scanner
- **System Package Scanning** - Check Ubuntu packages for known CVEs
- **Application Dependency Scanning** - Scan npm, composer, pip dependencies
- **Multi-Directory Scanning** - Scan /var/www, /home, custom directories
- **Project Detection** - Auto-detect package.json, composer.json, requirements.txt
- **CVE Database Updates** - Keep vulnerability databases current
- **Cron Setup** - Automatic daily/weekly CVE database updates
- **Scan History** - Track and review past scan results
- **Ubuntu 20.04-24.04** - Full support for LTS versions

---

## 📦 Installation

### Quick Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/boparaiamrit/forge-cli/main/install.sh | bash
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/boparaiamrit/forge-cli.git
cd forge-cli

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run Forge CLI
forge
```

### Docker (Development/Testing)

```bash
# Build the Docker image
docker build -t forge-cli .

# Run tests
docker run --rm forge-cli pytest -v tests/

# Run interactively
docker run -it forge-cli forge
```

### Updating

**From the CLI (recommended):**
```bash
forge
# Select "🔄 Check for Updates" from the menu
```

**Manual update:**
```bash
cd ~/.forge/forge-cli
git pull
source venv/bin/activate
pip install -e .
```

**Full reinstall:**
```bash
curl -sSL https://raw.githubusercontent.com/boparaiamrit/forge-cli/main/install.sh | bash
```

---

## 🎯 Quick Start

### Launch the CLI

```bash
forge
```

### Main Menu Options

```
🔧 Forge CLI v0.13.0
─────────────────────────────────

What would you like to do?
▶ 📊  System Status
  📦  Install Packages
  🐘  PHP Management
  🗄️  Database Management
  ─────────────────────────────
  🌐  Manage Sites
  🔒  SSL Certificates
  ⚙️   Services
  ⏰  Cron Jobs
  ─────────────────────────────
  📜  Logs
  📈  Monitor
  🔧  Diagnostics
  🛡️   Security & Antivirus
  🔍  Configuration Auditor
  🛡️   CVE Scanner
  ─────────────────────────────
  💾  Disk Management
  📊  Monitoring & Alerts
  ─────────────────────────────
  📋  State History
  ❌  Exit
```

---

## 🐘 PHP Management

The PHP Management module provides comprehensive control over PHP installations:

### Install PHP Versions

```
📥 Install PHP Version

Select PHP version to install:
▶ 🎯 Install ALL versions
  PHP 8.5
  PHP 8.4
  PHP 8.3 (installed)
  PHP 8.2 (installed)
  PHP 8.1
  PHP 8.0
  PHP 7.4
```

### Extension Bundles

| Bundle | Description | Extensions |
|--------|-------------|------------|
| **Laravel Essentials** | All extensions for Laravel | cli, fpm, mysql, pgsql, redis, mbstring, xml, curl, zip, bcmath, gd, intl, opcache, and more |
| **WordPress Essentials** | All extensions for WordPress | cli, fpm, mysql, curl, gd, mbstring, xml, zip, imagick, exif, opcache |
| **Basic Web Server** | Minimal PHP setup | cli, fpm, mysql, mbstring, xml, curl, zip, gd |
| **Full Stack** | All common extensions | 40+ extensions |

### Individual Extensions

Extensions are organized by category:
- **Database**: mysql, pgsql, sqlite3, redis, memcached, mongodb
- **Web & API**: curl, soap, xml, json
- **Text**: mbstring, intl, iconv, gettext
- **Media**: gd, imagick, exif
- **Security**: openssl, sodium
- **Development**: xdebug, opcache, apcu
- **Framework**: bcmath, pdo, tokenizer, fileinfo

### Check Installed Extensions

```
🔍 Installed PHP Extensions

PHP 8.4 Extensions:

DATABASE:
  🟢 mysql - MySQL/MariaDB support
  🟢 pgsql - PostgreSQL support
  🟢 redis - Redis support

FRAMEWORK:
  🟢 mbstring - Multibyte string support
  🟢 bcmath - Arbitrary precision math
  ...
```

### Smart PHP-FPM Pool Configuration

Forge CLI calculates optimal pool settings based on your server's RAM, swap, and CPU:

```
⚡ Smart Pool Configuration

📊 Server Specifications
┌─────────────────────┬──────────────────┐
│ Metric              │ Value            │
├─────────────────────┼──────────────────┤
│ Total RAM           │ 8.0 GB           │
│ Available RAM       │ 6.2 GB           │
│ Total Swap          │ 4.0 GB           │
│ CPU Cores           │ 4                │
└─────────────────────┴──────────────────┘

🎯 Recommended Settings for LARGE server:
┌───────────────────────┬────────┬──────────────────────────────┐
│ Setting               │ Value  │ Explanation                  │
├───────────────────────┼────────┼──────────────────────────────┤
│ pm                    │ dynamic│ ondemand=low RAM, dynamic=prod│
│ pm.max_children       │ 130    │ Max PHP workers (6500MB/50MB)│
│ pm.start_servers      │ 8      │ PHP workers at startup       │
│ pm.min_spare_servers  │ 4      │ Min idle workers             │
│ pm.max_spare_servers  │ 16     │ Max idle workers             │
│ pm.max_requests       │ 500    │ Requests before worker restart│
└───────────────────────┴────────┴──────────────────────────────┘

⚠️  Important: This will modify your PHP-FPM pool configuration!
Apply these recommended settings? (Y/n)
```

### Server Size Recommendations

| Server RAM | Size Class | PM Type | Reserved for System |
|------------|------------|---------|---------------------|
| ≤ 1 GB     | Small      | ondemand | 40% |
| ≤ 4 GB     | Medium     | dynamic  | 30% |
| ≤ 16 GB    | Large      | dynamic  | 25% |
| > 16 GB    | Enterprise | dynamic  | 20% |

### Average Process Memory

| Application Type | Avg Process Memory |
|-----------------|-------------------|
| Simple sites, static content | 30 MB |
| Standard Laravel/WordPress | 50 MB |
| Heavy applications, large models | 80 MB |
| Very heavy applications | 100 MB |
| Memory-intensive apps | 150 MB |

### Example Configurations

**2 GB RAM, 1 CPU (Small VPS):**
```ini
pm = ondemand
pm.max_children = 24
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3
pm.max_requests = 500
```

**4 GB RAM, 2 CPUs (Medium Server):**
```ini
pm = dynamic
pm.max_children = 56
pm.start_servers = 4
pm.min_spare_servers = 2
pm.max_spare_servers = 8
pm.max_requests = 500
```

**8 GB RAM, 4 CPUs (Large Server):**
```ini
pm = dynamic
pm.max_children = 130
pm.start_servers = 8
pm.min_spare_servers = 4
pm.max_spare_servers = 16
pm.max_requests = 500
```

**32 GB RAM, 8 CPUs (Enterprise):**
```ini
pm = dynamic
pm.max_children = 500
pm.start_servers = 16
pm.min_spare_servers = 8
pm.max_spare_servers = 32
pm.max_requests = 500
```

---

## 🌐 Site Management

### Create a Site

```
🆕 Create New Site

Domain: myapp.example.com
Include www? Yes
Site type: Next.js
Port: 3000

── Proxy Upstreams ──
Add a reverse-proxy path? Yes
  URL path: /api/
  Upstream port: 8000
  Description: REST API
  ✓ Added: /api/ → :8000

── WebSocket Proxy ──
Add a WebSocket proxy path? Yes
  Public WS path: /ws
  Upstream port: 8000
  Upstream path: /ws
  ✓ Added WS: /ws → :8000/ws

── Access Control ──
Enable HTTP Basic Auth? Yes
  Username: admin
  Password: ********
  Auth realm: Restricted Access

┌──────────── ✅ Site Created ────────────┐
│ Domain:    myapp.example.com            │
│ Primary:   :3000                        │
│ Proxy:     /api/ → :8000                │
│ WebSocket: /ws → :8000/ws               │
│ Basic Auth: admin                       │
└─────────────────────────────────────────┘
```

### Site Listing

```
🌐 Nginx Sites
┌────────────────────┬──────────────┬─────────┬────────────────────┐
│ Site               │ SSL          │ Type    │ Details            │
├────────────────────┼──────────────┼─────────┼────────────────────┤
│ example.com        │ 🔒 45 days   │ nextjs  │ Port: 3000         │
│ api.example.com    │ 🔒 12 days   │ php     │ /var/www/api       │
│ blog.example.com   │ ⚠️ 5 days    │ static  │ /var/www/blog      │
│ dev.example.com    │ 🔓 No SSL    │ nuxtjs  │ Port: 3001         │
└────────────────────┴──────────────┴─────────┴────────────────────┘
```

### Site Actions

- **View/Edit Configuration** - Open Nginx config in editor
- **View Logs** - Site-specific access and error logs
- **Health Check** - DNS, HTTP, HTTPS, SSL verification
- **Provision SSL** - Quick SSL setup with Let's Encrypt
- **Enable/Disable** - Toggle site availability
- **Delete Site** - Remove configuration and state

---

## 🔐 Hardened Nginx Templates

All site configurations use production-hardened templates with:

### Security Headers
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### Optimized Timeouts
```nginx
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
client_max_body_size 100M;
```

### Buffer Settings
```nginx
proxy_buffer_size 128k;
proxy_buffers 4 256k;
proxy_busy_buffers_size 256k;
```

### Gzip Compression
```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript ...;
```

---

## ⚙️ Service Management

Comprehensive dashboard for managing all server services:

### Service Dashboard

```
📊 Service Dashboard

Services Overview
─────────────────────
● Running: 12
○ Stopped: 3
✗ Failed: 0
Total: 15

🌐 Web Servers
  ● Nginx* (enabled)
  ○ Apache2 (disabled)

🐘 PHP-FPM
  ● PHP 8.3-FPM* (enabled)
  ● PHP 8.2-FPM* (enabled)

🗄️ Databases
  ● MySQL* (enabled)
  ● PostgreSQL* (enabled)

⚡ Caching
  ● Redis* (enabled)

🔒 Security
  ● UFW (Firewall)* (enabled)
  ● Fail2ban* (enabled)

* = critical service
```

### Service Categories

| Category | Services |
|----------|----------|
| **Web Servers** | Nginx, Apache2, Caddy |
| **PHP-FPM** | PHP 8.3, 8.2, 8.1, 8.0, 7.4 |
| **Databases** | MySQL, MariaDB, PostgreSQL, MongoDB |
| **Caching** | Redis, Memcached |
| **Queue/Workers** | Supervisor, RabbitMQ, Beanstalkd |
| **Mail** | Postfix, Dovecot |
| **Monitoring** | Prometheus, Grafana, Node Exporter |
| **Security** | UFW, Fail2ban, ClamAV, Freshclam |
| **SSL/TLS** | Certbot Timer |
| **System** | Cron, SSH, Rsyslog, NTP |
| **Containers** | Docker, Containerd |

### Service Actions

| Action | Description |
|--------|-------------|
| **Start** | Start a stopped service |
| **Stop** | Stop a running service (with confirmation for critical) |
| **Restart** | Restart a service (recommended for config changes) |
| **Reload** | Reload config without downtime (if supported) |
| **Enable** | Start service automatically on boot |
| **Disable** | Don't start on boot |

### Quick Actions

- **Restart All PHP-FPM** - Restart all PHP-FPM versions
- **Restart Web Server** - Restart Nginx/Apache
- **Restart Databases** - Restart MySQL/PostgreSQL
- **Reload All Services** - Reload all running services

### Service Status Table

```
┌──────────────────┬────────────┬─────────┬──────┬─────────┬──────────┐
│ Service          │ Status     │ State   │ Boot │ Memory  │ Uptime   │
├──────────────────┼────────────┼─────────┼──────┼─────────┼──────────┤
│ Nginx            │ ● Running  │ running │ ✓    │ 15.2 MB │ 5d 12h   │
│ PHP 8.3-FPM      │ ● Running  │ running │ ✓    │ 128.5 MB│ 2d 8h    │
│ MySQL            │ ● Running  │ running │ ✓    │ 512.3 MB│ 5d 12h   │
│ Redis            │ ● Running  │ running │ ✓    │ 8.2 MB  │ 5d 12h   │
│ Fail2ban         │ ● Running  │ running │ ✓    │ 24.1 MB │ 5d 12h   │
│ ClamAV           │ ○ Stopped  │ dead    │ ✗    │ -       │ -        │
└──────────────────┴────────────┴─────────┴──────┴─────────┴──────────┘
```

---

## 📊 Monitoring

### Live Dashboard

```
📊 System Dashboard (Live)
──────────────────────────────

CPU Usage:    ████████░░░░░░░░  45%
Memory Usage: ██████████░░░░░░  62%
Disk Usage:   ██████████████░░  89%

Load Average: 0.45, 0.52, 0.48
Uptime: 45 days, 12:34:56

Press Ctrl+C to exit...
```

### Health Checks

- **HTTP/HTTPS Response** - Check site accessibility
- **SSL Certificate** - Validate certificate and expiry
- **DNS Resolution** - Verify A/AAAA records
- **Service Status** - Check Nginx, PHP-FPM, MySQL

---

## 🔧 Diagnostics

### Error Troubleshooting

The diagnostics module helps troubleshoot common HTTP errors:

| Error | Common Causes | Auto-Fix |
|-------|--------------|----------|
| **419** | CSRF token issues, session driver | Check Laravel config |
| **500** | PHP errors, permissions | View logs, fix permissions |
| **502** | Upstream service down | Restart Node/PHP-FPM |
| **504** | Timeout | Increase timeouts |
| **403** | Permission denied | Fix file permissions |
| **404** | Missing files/routes | Check document root |

### Auto-Fix Capabilities

- Restart Nginx, PHP-FPM, MySQL
- Fix file permissions
- Regenerate Nginx configuration
- Clear PHP OPcache

---

## 📋 State Lineage

Track all changes to your server configuration:

```
📋 State Change History

┌─────────────────────┬──────────┬─────────────────┬───────────┐
│ Timestamp           │ Type     │ Entity          │ Action    │
├─────────────────────┼──────────┼─────────────────┼───────────┤
│ 2026-02-01 00:30:15 │ site     │ example.com     │ + create  │
│ 2026-02-01 00:32:45 │ site     │ example.com     │ ~ update  │
│ 2026-02-01 00:35:00 │ php      │ 8.3             │ + install │
│ 2026-02-01 00:40:22 │ site     │ api.example.com │ + create  │
│ 2026-02-01 00:45:00 │ site     │ example.com     │ ~ ssl     │
└─────────────────────┴──────────┴─────────────────┴───────────┘
```

### State Files

State is persisted in `~/.forge/`:
- `state.json` - Current state (sites, PHP versions, pending operations)
- `lineage.json` - Audit trail of all changes (last 1000 entries)

---

## ⏰ Cron Jobs

Manage scheduled tasks and automate server maintenance:

### Preset Schedules

| Schedule | Cron Expression | Description |
|----------|-----------------|-------------|
| Every minute | `* * * * *` | Run every minute |
| Hourly | `0 * * * *` | Run at the start of each hour |
| Daily (midnight) | `0 0 * * *` | Run at midnight |
| Daily (3 AM) | `0 3 * * *` | Run at 3:00 AM |
| Weekly (Sunday) | `0 0 * * 0` | Run Sunday at midnight |
| Monthly | `0 0 1 * *` | Run on the 1st at midnight |

### SSL Auto-Renewal

```
🔒 SSL Certificate Auto-Renewal

✓ Certbot auto-renewal is already configured
  (runs twice daily at 0:00 and 12:00)

📜 Certificate Renewal Status
┌─────────────────┬────────┬────────────┬──────────┬──────────────┬──────────────┐
│ Domain          │ Status │ Expiry     │ Days Left│ Last Renewed │ Next Renewal │
├─────────────────┼────────┼────────────┼──────────┼──────────────┼──────────────┤
│ example.com     │ ✓ VALID│ 2026-04-15 │ 73       │ 17 days ago  │ In 43 days   │
│ api.example.com │ ⚠️ SOON│ 2026-03-01 │ 28       │ 62 days ago  │ Due now      │
└─────────────────┴────────┴────────────┴──────────┴──────────────┴──────────────┘
```

### Cleanup & Backup Jobs

**Cleanup Jobs:**
- Clear old logs (> 30 days)
- Clear apt cache weekly
- Clear temp files
- Clear old PHP sessions
- Restart PHP-FPM weekly

**Backup Jobs:**
- Backup Nginx configs
- Backup MySQL databases
- Backup PostgreSQL databases
- Backup web files

---

## 🛡️ Security & Antivirus

### ClamAV Integration

```
🛡️ ClamAV Antivirus Status

✓ ClamAV Installed: ClamAV 1.0.0
✓ Freshclam Service: Active (auto-updating)
✓ ClamAV Daemon: Active

Virus Database:
  Build time: 2026-02-01
  Signatures: 8,645,521
```

### Scanning Options

| Scan Type | Description | Typical Time |
|-----------|-------------|--------------|
| **Quick Scan** | /tmp, /var/tmp, /dev/shm, /var/www | 1-5 min |
| **Web Files** | Focus on PHP files in web directories | 2-10 min |
| **Directory** | Scan any specified directory | Varies |
| **Full System** | Scan entire filesystem (excluding /proc, /sys) | 30+ min |

### Scan Reports

```
📊 Scan Results

✓ No threats detected

Files scanned: 12,456
Data scanned: 1.23 GB
Duration: 45.2 seconds
Report saved: ~/.forge/security/scan_20260201_030000.json
```

### File Change Detection

- **Generate Baseline** - Create checksums of all files in a directory
- **Check Baseline** - Compare current files against baseline
- **Live Monitoring** - Real-time filesystem change alerts with inotify

### Malware Signatures

```
Virus Databases:
┌──────────────┬─────────┬────────────────┬────────────────────┐
│ Database     │ Version │ Signatures     │ Build Time         │
├──────────────┼─────────┼────────────────┼────────────────────┤
│ main.cvd     │ 62      │ 6,631,589      │ 2026-02-01 10:30   │
│ daily.cld    │ 27150   │ 2,013,932      │ 2026-02-01 12:00   │
│ bytecode.cvd │ 334     │ 95             │ 2026-02-01 10:00   │
└──────────────┴─────────┴────────────────┴────────────────────┘

Total Signatures: 8,645,616
```

---

## 🔍 Configuration Auditor

Analyze and optimize your server configurations with automated issue detection and fixing:

### Full Audit

```
🔍 Full Configuration Audit

Analyzing configurations...

🔍 Issues Found
┌───────────┬─────────────────────────────────────────┬──────────┬─────────┐
│ Category  │ Issue                                   │ Severity │ Fixable │
├───────────┼─────────────────────────────────────────┼──────────┼─────────┤
│ Nginx     │ Missing X-Frame-Options header          │ HIGH     │ ✓       │
│ Nginx     │ Missing X-Content-Type-Options header   │ HIGH     │ ✓       │
│ PHP       │ memory_limit: 128M (recommended: 512M)  │ MEDIUM   │ ✓       │
│ PHP       │ opcache.enable: 0 (recommended: 1)      │ HIGH     │ ✓       │
│ Security  │ UFW firewall is inactive                │ HIGH     │ ✓       │
│ Security  │ Fail2ban is not running                 │ HIGH     │ ✓       │
└───────────┴─────────────────────────────────────────┴──────────┴─────────┘

Total issues found: 6
6 issues can be automatically fixed

Fix all 6 fixable issues? (Y/n)
```

### Nginx Site Audit

Checks each enabled site for:

| Check | Description | Severity |
|-------|-------------|----------|
| **X-Frame-Options** | Prevents clickjacking attacks | HIGH |
| **X-Content-Type-Options** | Prevents MIME-type sniffing | HIGH |
| **X-XSS-Protection** | Enables XSS filtering | MEDIUM |
| **Referrer-Policy** | Controls referrer information | MEDIUM |
| **Content-Security-Policy** | Defines content loading policy | MEDIUM |
| **Gzip Compression** | Enable compression for faster loading | MEDIUM |
| **Buffer Settings** | Optimize proxy buffering | LOW |
| **Timeout Settings** | Proper timeout configuration | LOW |

### PHP Configuration Audit

Checks PHP settings against production recommendations:

| Setting | Recommended | Description |
|---------|-------------|-------------|
| `memory_limit` | 512M | PHP memory limit |
| `upload_max_filesize` | 100M | Maximum upload file size |
| `max_execution_time` | 300 | Script timeout |
| `opcache.enable` | 1 | Enable OPcache |
| `opcache.memory_consumption` | 256 | OPcache memory |
| `display_errors` | Off | Hide errors in production |
| `expose_php` | Off | Hide PHP version |

### Security Audit

| Check | Description |
|-------|-------------|
| **UFW Firewall** | Ensure firewall is installed and active |
| **Fail2ban** | Intrusion prevention running |
| **SSH Root Login** | Disable direct root SSH access |
| **SSH Password Auth** | Recommend key-based authentication |

### Auto-Fix

All fixable issues can be resolved with one click:
- Adds missing Nginx security headers
- Updates PHP configuration values
- Enables/starts required services
- Configures firewall with safe defaults

---

## 🛡️ CVE Scanner

Comprehensive vulnerability scanning for system packages and application dependencies:

### System Package Scanning

```
💻 System Package CVE Scan

Ubuntu 24.04 (noble)

Checking for security updates...

💻 System Package Vulnerabilities
┌─────────────────────┬───────────────────┬──────────┬─────────────────────┐
│ Package             │ CVEs              │ Severity │ Description         │
├─────────────────────┼───────────────────┼──────────┼─────────────────────┤
│ openssl             │ CVE-2024-1234     │ SECURITY │ Security update     │
│ libcurl4            │ CVE-2024-5678     │ SECURITY │ Buffer overflow fix │
└─────────────────────┴───────────────────┴──────────┴─────────────────────┘

Total issues: 2
Run system update to fix vulnerabilities? (Y/n)
```

### Application Dependency Scanning

Automatically detects and scans projects in `/var/www`, `/home`, or custom directories:

| File | Ecosystem | Scanner |
|------|-----------|---------|
| `package.json` | Node.js | npm audit |
| `package-lock.json` | Node.js | npm audit |
| `composer.json` | PHP | composer audit |
| `composer.lock` | PHP | composer audit |
| `requirements.txt` | Python | pip-audit |
| `Pipfile.lock` | Python | pip-audit |
| `Gemfile.lock` | Ruby | bundler audit |
| `go.mod` | Go | govulncheck |
| `Cargo.lock` | Rust | cargo audit |

### Scan Results

```
📁 Projects Found
┌─────────────────────┬───────────┬─────────────────────────────────┐
│ Project             │ Ecosystem │ Path                            │
├─────────────────────┼───────────┼─────────────────────────────────┤
│ my-laravel-app      │ php       │ /var/www/my-laravel-app         │
│ api-service         │ nodejs    │ /var/www/api-service            │
│ python-worker       │ python    │ /home/deploy/python-worker      │
└─────────────────────┴───────────┴─────────────────────────────────┘

📊 Summary
Total Vulnerabilities: 12
Critical/High: 3
With CVE IDs: 8
Projects affected: 3
```

### CVE Database Management

| Component | Description |
|-----------|-------------|
| **Ubuntu Security Status** | System package CVE tracking |
| **npm audit** | Node.js vulnerability database |
| **composer audit** | PHP security advisories |
| **pip-audit** | Python vulnerability scanner |

### Automatic Updates

Setup daily or weekly CVE database updates via cron:

```
⏰ Setup CVE Update Cron

How often should CVE databases be updated?
▶ 📅 Daily (recommended)
  📅 Weekly
  📅 Twice daily

Setting up cron: 0 3 * * *
✓ CVE update cron job configured!
```

### Supported Ubuntu Versions

| Version | Codename | Status |
|---------|----------|--------|
| Ubuntu 24.04 | Noble | ✓ Supported |
| Ubuntu 22.04 | Jammy | ✓ Supported |
| Ubuntu 20.04 | Focal | ✓ Supported |

---

## 💾 Disk Management

Comprehensive disk cleanup, log rotation, space analysis, and swap management:

### Disk Space Overview

```
📊 Disk Space Overview

💾 Filesystem Usage
┌──────────────────┬───────┬───────┬───────────┬──────┬─────────────┐
│ Filesystem       │ Size  │ Used  │ Available │ Use% │ Mount Point │
├──────────────────┼───────┼───────┼───────────┼──────┼─────────────┤
│ /dev/sda1        │ 100G  │ 45G   │ 50G       │ 47%  │ /           │
│ /dev/sdb1        │ 500G  │ 320G  │ 155G      │ 67%  │ /var        │
└──────────────────┴───────┴───────┴───────────┴──────┴─────────────┘

⚠️ Warnings
  • [yellow]WARNING: /var is 67% full[/yellow]
```

### Cleanup Features

| Feature | Description |
|---------|-------------|
| **Quick Cleanup** | APT cache, old kernels, temp files, old logs |
| **Deep Cleanup** | + systemd journal, pip/npm/composer cache, PHP sessions |
| **APT Cleanup** | Clean package cache and remove unused packages |
| **Docker Cleanup** | Unused images, containers, networks, volumes |

### Log Management

| Feature | Description |
|---------|-------------|
| **Log Rotation Status** | Check logrotate configuration |
| **Force Rotation** | Manually rotate all logs |
| **Large Log Finder** | Find logs > 100MB |
| **Truncate Large Logs** | Clear logs > 500MB |

### File Finding

| Feature | Description |
|---------|-------------|
| **Large Files** | Find files > 100MB, 500MB, 1GB, 5GB |
| **Old Files** | Files not accessed in 30-365 days |
| **Duplicate Files** | Find duplicate files using fdupes |

### Swap Management

```
💾 Swap Management

Memory Information:
              total        used        free      shared  buff/cache   available
Mem:           8Gi       3.2Gi       1.5Gi       512Mi       3.3Gi       4.1Gi
Swap:          4Gi       256Mi       3.8Gi

System RAM: 8.0 GB
Recommended Swap: 4G

What would you like to do?
▶ ➕ Create swap file (4G recommended)
  🔧 Adjust swappiness
  🗑️  Remove swap
```

### Swap Recommendations

| RAM | Recommended Swap |
|-----|------------------|
| ≤ 2 GB | 2 GB |
| ≤ 8 GB | Equal to RAM |
| ≤ 64 GB | Half of RAM |
| > 64 GB | 32 GB |

### Swappiness Settings

| Value | Description |
|-------|-------------|
| 10 | Production server (recommended) |
| 30 | Moderate swapping |
| 60 | Default (desktop) |
| 100 | Aggressive swapping |

---

## 📊 Monitoring & Alerts

System resource monitoring with historical data, alerts, and configurable thresholds:

### Current System Status

```
📊 Current System Status

┌───────────────┬───────────────────────────────────────────┬─────────────────────────┬────────────┐
│ Metric        │ Current                                   │ Threshold               │ Status     │
├───────────────┼───────────────────────────────────────────┼─────────────────────────┼────────────┤
│ CPU Usage     │ 23.5%                                     │ W: 70% / C: 90%         │ 🟢 OK      │
│ Memory Usage  │ 45.2% (3.6 GB / 8.0 GB)                   │ W: 75% / C: 90%         │ 🟢 OK      │
│ Disk Usage (/)│ 67.3%                                     │ W: 80% / C: 95%         │ 🟢 OK      │
│ Load Average  │ 0.85 / 1.12 / 0.95 (per CPU: 0.21)        │ W: 4.0 / C: 8.0         │ 🟢 OK      │
│ Swap Usage    │ 12.5% (512 MB / 4.0 GB)                   │ W: 50% / C: 80%         │ 🟢 OK      │
└───────────────┴───────────────────────────────────────────┴─────────────────────────┴────────────┘
```

### Default Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Usage | 70% | 90% |
| Memory Usage | 75% | 90% |
| Disk Usage | 80% | 95% |
| Load (per CPU) | 4.0 | 8.0 |
| Swap Usage | 50% | 80% |

### Alert System

```
🔔 Active Alerts

┌────┬───────────────────┬─────────┬────────┬────────────┬────────────────────────────────────┐
│ ID │ Time              │ Metric  │ Value  │ Severity   │ Message                            │
├────┼───────────────────┼─────────┼────────┼────────────┼────────────────────────────────────┤
│ 1  │ 2026-02-01 09:15  │ disk_/  │ 82.5   │ 🟡 WARNING │ Disk / is 82.5% full               │
│ 2  │ 2026-02-01 09:10  │ memory  │ 91.2   │ 🔴 CRITICAL│ Memory usage is 91.2%              │
└────┴───────────────────┴─────────┴────────┴────────────┴────────────────────────────────────┘
```

### Historical Data

```
📈 Statistics (Last 24h)

┌───────────────┬────────┬────────┬─────────┬─────────┐
│ Metric        │ Min    │ Max    │ Average │ Current │
├───────────────┼────────┼────────┼─────────┼─────────┤
│ CPU Usage     │ 5.2%   │ 67.8%  │ 23.4%   │ 18.5%   │
│ Memory Usage  │ 42.1%  │ 78.3%  │ 55.2%   │ 52.8%   │
│ Disk Usage (/)│ 65.0%  │ 67.3%  │ 66.1%   │ 67.3%   │
└───────────────┴────────┴────────┴─────────┴─────────┘

Data points: 288
First: 2026-01-31 09:00
Last: 2026-02-01 09:00
```

### Features

| Feature | Description |
|---------|-------------|
| **Live Metrics** | Real-time CPU, memory, disk, load, swap |
| **History Views** | 1 hour, 6 hours, 24 hours, 7 days |
| **Alert Thresholds** | Customizable warning and critical levels |
| **Alert History** | View and acknowledge past alerts |
| **Cron Integration** | Automatic collection every 5 minutes |
| **Data Retention** | Last 7 days of metrics |

### Monitoring Cron

```
⏰ Setup Monitoring Cron

Monitoring interval:
▶ Every 5 minutes (recommended)
  Every 15 minutes
  Every 30 minutes
  Every hour

Cron configured: */5 * * * *
✓ Monitoring cron configured!
```

---

## 📁 Project Structure

```
forge-cli/
├── cli.py                 # Main CLI entry point
├── php/
│   └── __init__.py        # PHP version & extension management
├── sites/
│   └── __init__.py        # Site management with hardened templates
├── nginx/
│   ├── __init__.py        # Nginx utilities
│   └── templates.py       # Production nginx templates
├── sslcerts/
│   └── __init__.py        # SSL certificate management with renewal tracking
├── services/
│   └── __init__.py        # Service management (nginx, php-fpm, etc.)
├── cron/
│   └── __init__.py        # Cron job management & scheduling
├── security/
│   └── __init__.py        # ClamAV antivirus & file change detection
├── auditor/
│   └── __init__.py        # Configuration auditor & optimizer
├── cve/
│   └── __init__.py        # CVE vulnerability scanner
├── disk/
│   └── __init__.py        # Disk management, cleanup & swap
├── alerts/
│   └── __init__.py        # Monitoring & alerts with historical data
├── logs/
│   └── __init__.py        # Log viewing & monitoring
├── monitor/
│   └── __init__.py        # System monitoring & health checks
├── diagnostics/
│   └── __init__.py        # Error troubleshooting & auto-fix
├── state/
│   └── __init__.py        # State persistence & lineage tracking
├── utils/
│   ├── shell.py           # Command execution utilities
│   ├── ui.py              # Terminal UI helpers
│   └── network.py         # Network utilities (IP, DNS, SSL)
├── tests/
│   └── test_*.py          # Test suites
├── CHANGELOG.md           # Version history
├── Dockerfile             # Docker testing environment
└── requirements.txt       # Python dependencies
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest -v tests/

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest -v tests/test_new_modules.py
```

### Docker Testing

```bash
# Build and run tests in Docker
docker build -t forge-cli-test .
docker run --rm forge-cli-test

# Run specific tests
docker run --rm forge-cli-test pytest -v tests/test_state.py
```

---

## 🔒 Security

- **Hardened Nginx configs** with security headers
- **No plaintext secrets** - Uses environment variables
- **Sudo only when needed** - Minimal privilege escalation
- **Input validation** - Sanitized user inputs
- **SSL best practices** - TLS 1.2+, strong ciphers

---

## 📋 Requirements

- **OS**: Ubuntu 20.04, 22.04, 24.04
- **Python**: 3.10+
- **Privileges**: sudo access for system operations

### Python Dependencies

- `rich` - Beautiful terminal formatting
- `questionary` - Interactive prompts
- `click` - CLI framework
- `jinja2` - Template rendering
- `pydantic` - Data validation

---

## 🗺️ Roadmap

### v1.1 (Planned)
- [ ] Database management (MySQL, PostgreSQL)
- [ ] PM2/Supervisor process management
- [ ] Backup & restore functionality

### v1.2 (Planned)
- [ ] Multi-server support
- [ ] Remote server management via SSH
- [ ] Deployment pipelines

### v2.0 (Future)
- [ ] Web dashboard
- [ ] API server mode
- [ ] Kubernetes integration

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Questionary](https://github.com/tmbo/questionary) for interactive prompts
- [Certbot](https://certbot.eff.org/) for SSL automation
- [Ondřej Surý](https://launchpad.net/~ondrej/+archive/ubuntu/php) for PHP packages

---

Made with ❤️ by [Amritpal Singh](https://github.com/boparaiamrit)
