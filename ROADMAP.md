# Forge CLI — Roadmap

## ✅ Completed Features

### Phase 1: Core Framework
- ✅ Project scaffolding with Python 3.10+
- ✅ Virtual environment and dependencies
- ✅ Entry point and package structure
- ✅ Docker support for development

### Phase 2: UI Framework & Navigation
- ✅ Interactive menu system with Rich console
- ✅ Sub-menu navigation (back/exit)
- ✅ Multi-select prompts with Questionary
- ✅ Emoji icons and color theming
- ✅ Breadcrumb navigation

### Phase 3: System Detectors
- ✅ Nginx, PHP, Node.js, Redis detection
- ✅ MySQL/MariaDB/PostgreSQL detection
- ✅ Certbot, Composer detection
- ✅ Unified status dashboard

### Phase 4: Package Installers
- ✅ Nginx, PHP 7.4-8.5, Node.js, Redis
- ✅ MySQL, MariaDB, PostgreSQL
- ✅ Certbot, Composer, PM2, Supervisor
- ✅ Docker & Docker Compose
- ✅ Memcached

### Phase 5: Site Management
- ✅ Next.js, Nuxt.js, PHP/Laravel, Static templates
- ✅ Hardened Nginx configurations
- ✅ Enable/disable sites
- ✅ Health checks (DNS, HTTP, HTTPS, SSL)
- ✅ Live log viewing

### Phase 6: SSL Certificates
- ✅ Let's Encrypt via Certbot
- ✅ HTTP & DNS verification
- ✅ Auto-renewal setup
- ✅ Certificate status & expiry warnings

### Phase 7: Service Management
- ✅ Service dashboard with 11 categories
- ✅ Start/Stop/Restart/Reload
- ✅ Enable/disable on boot
- ✅ Quick actions (restart PHP, web servers)

### Phase 8: Advanced Features
- ✅ PHP-FPM smart pool configuration
- ✅ Disk management & cleanup
- ✅ Monitoring & alerts system
- ✅ Security & ClamAV integration
- ✅ Configuration auditor
- ✅ CVE scanner
- ✅ Cron job management
- ✅ State tracking & lineage
- ✅ Self-update system

---

## 🚧 In Progress

### v0.11.0 - Stability & Testing
- [ ] Comprehensive integration tests
- [ ] Error handling improvements
- [ ] Edge case fixes

---

## 📋 Planned Features

### v0.12.0 - Database Management
- [ ] MySQL/MariaDB database creation
- [ ] PostgreSQL database creation
- [ ] User management
- [ ] Backup & restore

### v0.13.0 - Backup System
- [ ] Scheduled site backups
- [ ] Database backups
- [ ] S3/remote storage support
- [ ] Backup rotation

### v1.0.0 - Production Release
- [ ] Comprehensive documentation
- [ ] Video tutorials
- [ ] Community feedback integration
- [ ] Performance optimization
- [ ] Multi-server support (future)

---

## 💡 Future Ideas

- **Web Dashboard** - Optional web UI for remote management
- **Notifications** - Slack/Discord/Email alerts
- **Load Balancing** - Multi-server configuration
- **Ansible Integration** - Export configurations as Ansible playbooks
- **Terraform Support** - Infrastructure as code generation

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.
