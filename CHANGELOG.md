# Changelog

All notable changes to Forge CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.0] - 2026-02-01

### Added
- **Self-Update Module** - Check for and install updates from within the CLI
  - Check latest version from GitHub
  - Compare semantic versions
  - Update via git pull (for source installs) or pip upgrade
  - Shows changelog link after update
  - Startup update check (silent, non-blocking)

## [0.9.0] - 2026-02-01

### Added
- **Smart PHP-FPM Pool Configuration** - Dynamic pool settings calculator
  - Analyzes server RAM, swap, and CPU cores
  - Recommends optimal pm.max_children, start_servers, spare servers
  - Server size classification (small, medium, large, enterprise)
  - Interactive confirmation before applying settings
  - Average process memory selection (30-150MB)
- **Disk Management Module** - Comprehensive disk and space management
  - Disk space overview with filesystem usage and inodes
  - Directory size analysis for /var, /home, /tmp
  - Quick cleanup (APT cache, old kernels, temp files, old logs)
  - Deep cleanup (pip/npm/composer cache, systemd journals, PHP sessions)
  - Docker cleanup (unused images, containers, volumes)
  - Log rotation status and manual rotation
  - Large file finder (100MB, 500MB, 1GB, 5GB thresholds)
  - Old file finder (30-365 days not accessed)
  - Duplicate file finder using fdupes
  - Swap management (create, adjust swappiness, remove)
  - Swappiness tuning recommendations
  - Automatic cleanup cron jobs
- **Monitoring & Alerts Module** - System resource monitoring with history
  - Real-time CPU, memory, disk, load, and swap monitoring
  - Historical data tracking (1h, 6h, 24h, 7d views)
  - Configurable warning and critical thresholds
  - Automatic alert generation when thresholds exceeded
  - Alert acknowledgment and history
  - Statistics with min/max/average calculations
  - Cron integration for periodic collection
  - 7-day data retention

### Changed
- Updated main menu with new module entries (Disk Management, Monitoring & Alerts)
- Enhanced README with comprehensive documentation for all new features
- Improved PHP-FPM configuration menu with Smart Pool and Custom Pool options

## [0.8.0] - 2026-02-01

### Added
- **Disk Management Module** - Comprehensive disk cleanup, log rotation, and space analysis
- **Monitoring & Alerts Module** - CPU/Memory/Disk tracking with historical data and alerts
- **Swap Management** - Configure and optimize swap for server hardening
- **Dynamic PHP-FPM Configuration** - Smart pool settings based on RAM/swap with user confirmation

### Changed
- Enhanced PHP-FPM configuration with server-size-aware recommendations
- Improved system monitoring with persistent data storage

## [0.7.0] - 2026-02-01

### Added
- **CVE Scanner Module** - Vulnerability scanning for system packages and application dependencies
  - System package CVE scanning with ubuntu-security-status
  - npm audit for Node.js projects
  - composer audit for PHP projects
  - pip-audit for Python projects
  - Multi-directory scanning (/var/www, /home, custom)
  - Project auto-detection (package.json, composer.json, requirements.txt)
  - CVE database update management
  - Cron setup for automatic updates
  - Scan history and reporting
- Support for Ubuntu 20.04, 22.04, and 24.04

## [0.6.0] - 2026-02-01

### Added
- **Configuration Auditor Module** - Analyze and optimize server configurations
  - Nginx site audit (security headers, gzip, buffers, timeouts)
  - PHP configuration audit (memory, OPcache, production settings)
  - Service audit (critical services, boot enablement)
  - Security audit (firewall, fail2ban, SSH hardening)
  - Auto-fix capability for all detected issues

## [0.5.0] - 2026-02-01

### Added
- **Security & Antivirus Module** - ClamAV integration for malware scanning
  - Quick scan, directory scan, web file scan, full system scan
  - Scan reports in JSON format
  - File change detection with baseline and monitoring
  - Scheduled scans via cron
  - Virus database updates
- **Cron Job Management Module** - Comprehensive cron job management
  - List, add, remove cron jobs
  - Preset schedules (hourly, daily, weekly, monthly)
  - SSL auto-renewal setup
  - Cleanup jobs (logs, cache, temp files)
  - Backup jobs (Nginx, MySQL, PostgreSQL, web files)

## [0.4.0] - 2026-02-01

### Added
- **Service Management Dashboard** - Comprehensive service management
  - Auto-detection of installed services
  - 11 service categories (Web, PHP, Database, Cache, Queue, Mail, Monitoring, Security, SSL, System, Docker)
  - Start/stop/restart/reload services
  - Enable/disable on boot
  - Memory usage and uptime tracking
  - Quick actions (restart all PHP-FPM, web servers, databases)
  - Service log viewing
- PHP 8.4 and PHP 8.5 support

### Changed
- Enhanced SSL certificate management with auto-renewal setup
- Improved certificate renewal tracking table

## [0.3.0] - 2026-01-31

### Added
- **SSL Certificate Management** with Let's Encrypt
  - HTTP and DNS verification support
  - Certificate provisioning for sites
  - Expiry warnings with color coding
  - Renewal tracking table
- **Diagnostics Module** - Error troubleshooting
  - Auto-detection of common errors (419, 500, 502, 504)
  - Auto-fix capabilities
  - Permission and cache clearing

## [0.2.0] - 2026-01-30

### Added
- **Site Management** - Create and manage Nginx sites
  - Multi-framework support (Next.js, Nuxt.js, PHP/Laravel, Static HTML)
  - Hardened Nginx templates with security headers
  - SSL integration
- **Log Management** - Centralized log viewing
  - Nginx access/error logs
  - Site-specific logs
  - Real-time monitoring with tail
  - Search and filter capabilities
- **Monitor Module** - System monitoring dashboard
  - CPU, memory, disk, load statistics
  - Service health checks
  - Port monitoring

## [0.1.0] - 2026-01-29

### Added
- Initial release of Forge CLI
- **System Status** - Overview of installed software
- **Package Installation** - One-click installation for:
  - Nginx with optimized configuration
  - PHP (7.4, 8.0, 8.1, 8.2, 8.3, 8.4, 8.5) with extensions
  - MySQL/MariaDB
  - PostgreSQL
  - Redis
  - Node.js with NVM
- **PHP Management** - Install versions, extensions, bundles
- **State Management** - Persistent state and lineage tracking
- Docker-based testing environment
- Comprehensive test suite
