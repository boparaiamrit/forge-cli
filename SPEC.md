# Forge CLI — Server Management Tool

## Overview

**Forge** is a Python-based interactive CLI tool for managing Ubuntu servers. It provides Laravel Forge-like functionality including system detection, package installation, site provisioning, and SSL certificate management.

## Status: FINALIZED

---

## Core Features

### 1. System Detection & Status
Detect and display installation status of:
- 🌐 Nginx (version)
- 🐘 PHP (version + extensions)
- 🟢 Node.js via NVM (active version)
- 🔴 Redis
- 🔒 Certbot (Let's Encrypt)
- 📦 Composer
- 🐍 Python
- 🗄️ MySQL/MariaDB
- 🐘 PostgreSQL

### 2. Package Installation
Interactive multi-select menu to install:
- Nginx
- PHP (8.1, 8.2, 8.3 with common extensions)
- Node.js via NVM (LTS or specific version)
- Redis
- Certbot
- Composer
- MySQL/MariaDB
- PostgreSQL

### 3. Site Management
Create and manage web application sites:

#### Site Types:
- **Next.js** → Reverse proxy to Node port
- **Nuxt.js** → Reverse proxy to Node port
- **PHP/Laravel** → PHP-FPM with document root
- **Static HTML** → Direct file serving

#### Site Creation Flow:
1. Select site type
2. Enter domain name
3. Configure type-specific options:
   - Next.js/Nuxt: Port number, PM2 process name
   - PHP: Document root, PHP version
4. Generate Nginx config
5. Enable site
6. Optionally provision SSL

### 4. SSL Certificate Management
- **HTTP Verification** (port 80 challenge)
- **DNS Verification** (wildcard support)
- Auto-renewal setup
- Certificate status check

### 5. Service Management
- Start/Stop/Restart services
- View service status
- Check logs

---

## Technical Stack

- **Language**: Python 3.10+
- **CLI Framework**: `rich` + `questionary` (beautiful prompts)
- **System Interaction**: `subprocess` for shell commands
- **Virtual Environment**: `venv`
- **Package Manager**: `pip` with `requirements.txt`

---

## User Experience

### Navigation
- Arrow keys to navigate menus
- Space to select/deselect in multi-select
- Enter to confirm
- `q` or `Ctrl+C` to go back/exit
- Breadcrumb navigation (Main → Sites → Create)

### Visual Design
- Emoji icons for all menu items
- Color-coded status (🟢 installed, 🔴 missing, 🟡 outdated)
- Rich tables for status display
- Progress spinners for long operations
- Confirmation prompts for destructive actions

---

## Directory Structure

```
forge/
├── forge/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── cli.py                # Main menu & navigation
│   ├── config.py             # Configuration management
│   ├── detectors/
│   │   ├── __init__.py
│   │   ├── nginx.py
│   │   ├── php.py
│   │   ├── node.py
│   │   ├── redis.py
│   │   ├── certbot.py
│   │   └── database.py
│   ├── installers/
│   │   ├── __init__.py
│   │   ├── nginx.py
│   │   ├── php.py
│   │   ├── node.py
│   │   ├── redis.py
│   │   └── certbot.py
│   ├── sites/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── nextjs.py
│   │   ├── nuxt.py
│   │   ├── php.py
│   │   └── static.py
│   ├── ssl/
│   │   ├── __init__.py
│   │   └── certbot.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── systemd.py
│   ├── templates/
│   │   ├── nginx/
│   │   │   ├── nextjs.conf.j2
│   │   │   ├── nuxt.conf.j2
│   │   │   ├── php.conf.j2
│   │   │   └── static.conf.j2
│   │   └── pm2/
│   │       └── ecosystem.config.js.j2
│   └── utils/
│       ├── __init__.py
│       ├── shell.py
│       └── ui.py
├── tests/
├── docs/
│   └── README.md
├── requirements.txt
├── setup.py
├── pyproject.toml
└── README.md
```

---

## Success Criteria

1. ✅ Single command to launch (`forge` or `python -m forge`)
2. ✅ Detect all major server software
3. ✅ Install packages with one menu selection
4. ✅ Create fully functional Nginx sites for Next.js, Nuxt, PHP
5. ✅ Provision SSL certificates with choice of verification
6. ✅ Beautiful, intuitive terminal UI with emoji
7. ✅ Comprehensive documentation

---

## Non-Goals (V1)

- Remote server management (SSH)
- Database management (migrations, backups)
- Deployment automation (Git hooks)
- User management
- Firewall configuration

These can be added in V2.
