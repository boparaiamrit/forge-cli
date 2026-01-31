# Forge CLI — Implementation Roadmap

## Phase 1: Project Scaffolding ⏳
**Goal**: Set up Python project structure with virtual environment

### Tasks:
- [ ] Create directory structure
- [ ] Initialize virtual environment
- [ ] Create `requirements.txt` with dependencies
- [ ] Create `pyproject.toml` for package metadata
- [ ] Create entry point (`__main__.py`)
- [ ] Verify `python -m forge` runs

### Success Criteria:
- Running `python -m forge` shows a placeholder message

---

## Phase 2: UI Framework & Navigation ⏳
**Goal**: Build the interactive menu system

### Tasks:
- [ ] Implement main menu with Rich console
- [ ] Implement sub-menu navigation (back/exit)
- [ ] Implement multi-select prompts with Questionary
- [ ] Add emoji icons and color theming
- [ ] Create breadcrumb navigation
- [ ] Add keyboard shortcuts (q to quit)

### Success Criteria:
- Navigate through menus fluidly
- Multi-select works with space/enter

---

## Phase 3: System Detectors ⏳
**Goal**: Detect installed software and versions

### Tasks:
- [ ] Nginx detector (version, running status)
- [ ] PHP detector (version, extensions)
- [ ] Node.js/NVM detector (active version)
- [ ] Redis detector
- [ ] Certbot detector
- [ ] MySQL/MariaDB detector
- [ ] PostgreSQL detector
- [ ] Composer detector
- [ ] Create unified status dashboard

### Success Criteria:
- Status table shows all software with versions
- Color-coded installed/missing indicators

---

## Phase 4: Package Installers ⏳
**Goal**: Install software via apt/scripts

### Tasks:
- [ ] Nginx installer
- [ ] PHP installer (version selection, extensions)
- [ ] Node.js installer via NVM
- [ ] Redis installer
- [ ] Certbot installer
- [ ] MySQL/MariaDB installer
- [ ] PostgreSQL installer
- [ ] Composer installer
- [ ] Add progress indicators
- [ ] Add error handling

### Success Criteria:
- Select packages from menu → installed successfully
- Handles already-installed gracefully

---

## Phase 5: Site Management — Nginx Configs ⏳
**Goal**: Create and manage Nginx site configurations

### Tasks:
- [ ] Site type selector (Next.js, Nuxt, PHP, Static)
- [ ] Domain name input with validation
- [ ] Port input for Node.js apps
- [ ] Document root input for PHP apps
- [ ] Jinja2 template engine for configs
- [ ] Create Nginx config templates
- [ ] Enable/disable site commands
- [ ] Test Nginx config before reload
- [ ] List existing sites

### Success Criteria:
- Create a Next.js site → Nginx config created and enabled
- Create a PHP site → Nginx config with PHP-FPM

---

## Phase 6: SSL Certificate Management ⏳
**Goal**: Provision Let's Encrypt SSL certificates

### Tasks:
- [ ] HTTP verification flow
- [ ] DNS verification flow (show required records)
- [ ] Certificate provisioning with Certbot
- [ ] Auto-renewal verification
- [ ] Certificate status check
- [ ] Revoke certificate option

### Success Criteria:
- Provision SSL for a domain via HTTP or DNS
- Certificate auto-renews

---

## Phase 7: Service Management ⏳
**Goal**: Control systemd services

### Tasks:
- [ ] List services (nginx, php-fpm, redis, mysql, etc.)
- [ ] Start/Stop/Restart service
- [ ] View service status
- [ ] View recent logs (journalctl)

### Success Criteria:
- Restart Nginx from menu
- View last 50 lines of Nginx error log

---

## Phase 8: Documentation & Polish ⏳
**Goal**: Complete documentation and final polish

### Tasks:
- [ ] Write README.md with full usage guide
- [ ] Add installation instructions
- [ ] Add troubleshooting guide
- [ ] Add screenshots/GIFs
- [ ] Final code cleanup
- [ ] Add --help flags

### Success Criteria:
- New user can install and use Forge from README alone
