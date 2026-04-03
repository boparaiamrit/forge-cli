# PHP And Database Parity Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PHP 8.4/8.5 site parity and a new database management module for PostgreSQL, MySQL, and MariaDB.

**Architecture:** Centralize supported PHP versions in a shared config source and add a dedicated `databases` module with shared menu flows plus engine-specific helpers. Keep engine differences in command-construction helpers so the terminal UI remains consistent.

**Tech Stack:** Python, questionary, rich, pytest

---

### Task 1: Centralize PHP versions and update site selection

**Files:**
- Create: `config/php_versions.py`
- Modify: `sites/__init__.py`
- Modify: `provisioning/config.py`
- Test: `tests/test_sites.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run site-focused tests to verify the new PHP-version expectations fail**
- [ ] **Step 3: Add the shared PHP version source and wire site selection to it**
- [ ] **Step 4: Run the focused tests to verify they pass**

### Task 2: Add database management menu entry

**Files:**
- Create: `databases/__init__.py`
- Modify: `cli.py`
- Test: `tests/test_imports.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for importability and main-menu routing**
- [ ] **Step 2: Run those tests to verify failure**
- [ ] **Step 3: Add the new module skeleton and CLI routing**
- [ ] **Step 4: Re-run focused tests to verify pass**

### Task 3: Add engine helpers and CRUD/password flows

**Files:**
- Modify: `databases/__init__.py`
- Test: `tests/test_databases.py`

- [ ] **Step 1: Write failing tests for PostgreSQL and MySQL/MariaDB command generation and system filtering**
- [ ] **Step 2: Run the new database tests to verify failure**
- [ ] **Step 3: Implement minimal helpers and action handlers to satisfy the tests**
- [ ] **Step 4: Re-run focused database tests to verify pass**

### Task 4: End-to-end focused verification

**Files:**
- Modify: `pyproject.toml`
- Modify: `updater/__init__.py`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update semantic version files for the new user-facing module/feature**
- [ ] **Step 2: Run focused regression tests for sites, CLI, and database flows**
- [ ] **Step 3: Fix any regressions until the focused suite passes**
