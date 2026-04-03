# PHP And Database Parity Phase 1 Design

**Goal**

Bring Forge CLI closer to Laravel Forge parity by fixing PHP site-version drift and adding first-class relational database management for PostgreSQL, MySQL, and MariaDB.

**Approved Scope**

- Add PHP `8.4` and `8.5` to site creation and remove duplicated PHP-version drift.
- Add a new top-level database-management capability.
- Support PostgreSQL, MySQL, and MariaDB in Phase 1.
- Include database CRUD-oriented operations needed for day-one management:
  - list databases
  - list users
  - create database
  - create user
  - grant user access to a database
  - reset user password
  - delete database
  - delete user

**Architecture**

Use a dedicated `databases` module with a shared terminal UI and engine-specific command helpers. Keep PHP-version parity separate by moving supported version data to a shared source that `sites`, `php`, and `provisioning` can all consume.

**User Flow**

- Main menu gets `Database Management`.
- Database actions first select an engine, then run a shared flow.
- Destructive actions require confirmation.
- Passwords are entered explicitly and never echoed back after entry.

**Engine Model**

- PostgreSQL commands run through `sudo -u postgres psql -c "..."`.
- MySQL and MariaDB commands run through `sudo mysql -e "..."`.
- MariaDB reuses the MySQL flow unless later differences require a split.

**Safety Rules**

- Validate database and user identifiers before execution.
- Exclude system databases from list views where practical.
- Show command failures clearly.
- Block management actions when an engine is not installed.

**Phase Boundary**

Phase 1 does not include:

- backup management
- external client launch helpers
- Forge `root` or `forge` password lifecycle parity
- sync/import of externally created databases
- advanced per-database permission editing beyond create/grant/reset/delete flows

**Verification**

- Add tests for shared PHP version sourcing.
- Add tests for new database menu routing.
- Add tests for engine-specific command generation and confirmation flows.
