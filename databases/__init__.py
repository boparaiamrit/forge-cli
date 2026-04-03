"""Database management for PostgreSQL, MySQL, and MariaDB."""

import re
from typing import Optional

import questionary
from rich.console import Console
from rich.table import Table
from rich import box

from utils.shell import command_exists, run_command
from utils.ui import (
    clear_screen,
    confirm_action,
    print_breadcrumb,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
)

console = Console()

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MYSQL_FAMILY = {"mysql", "mariadb"}
SYSTEM_DATABASES = {
    "postgresql": {"postgres", "template0", "template1"},
    "mysql": {"information_schema", "mysql", "performance_schema", "sys"},
    "mariadb": {"information_schema", "mysql", "performance_schema", "sys"},
}
SYSTEM_USERS = {
    "postgresql": {"postgres"},
    "mysql": {"mysql.session", "mysql.sys", "mysql.infoschema", "root"},
    "mariadb": {"mariadb.sys", "mysql", "root"},
}

DATABASE_ENGINES = [
    {"name": "PostgreSQL", "value": "postgresql", "command": "psql"},
    {"name": "MySQL", "value": "mysql", "command": "mysql"},
    {"name": "MariaDB", "value": "mariadb", "command": "mariadb"},
]

DATABASE_MENU_CHOICES = [
    {"name": "📋 Status", "value": "status"},
    {"name": "🗄️ List Databases", "value": "list_databases"},
    {"name": "👤 List Users", "value": "list_users"},
    {"name": "➕ Create Database", "value": "create_database"},
    {"name": "➕ Create User", "value": "create_user"},
    {"name": "🔐 Grant User Access", "value": "grant_access"},
    {"name": "🔑 Reset User Password", "value": "reset_password"},
    {"name": "🗑️ Delete Database", "value": "delete_database"},
    {"name": "🗑️ Delete User", "value": "delete_user"},
    questionary.Separator("─" * 30),
    {"name": "⬅️ Back", "value": "back"},
]


def run_databases_menu():
    """Display the database management menu."""
    handlers = {
        "status": show_database_status,
        "list_databases": prompt_list_databases,
        "list_users": prompt_list_users,
        "create_database": prompt_create_database,
        "create_user": prompt_create_user,
        "grant_access": prompt_grant_access,
        "reset_password": prompt_reset_password,
        "delete_database": prompt_delete_database,
        "delete_user": prompt_delete_user,
    }

    while True:
        clear_screen()
        print_header()
        print_breadcrumb(["Main", "Database Management"])

        choice = questionary.select(
            "Database Management:",
            choices=DATABASE_MENU_CHOICES,
            qmark="🗄️",
            pointer="▶",
        ).ask()

        if choice is None or choice == "back":
            return

        handlers[choice]()


def get_installed_engines() -> list[dict]:
    """Return engine metadata with installation state."""
    installed = []
    for engine in DATABASE_ENGINES:
        command = engine["command"]
        is_installed = command_exists(command)
        if engine["value"] == "mariadb" and not is_installed:
            is_installed = command_exists("mysql")

        installed.append({**engine, "installed": is_installed})
    return installed


def choose_engine() -> Optional[str]:
    """Prompt for an installed database engine."""
    choices = []
    for engine in get_installed_engines():
        if engine["installed"]:
            choices.append({"name": engine["name"], "value": engine["value"]})
        else:
            choices.append(
                {
                    "name": f"{engine['name']} [dim](not installed)[/dim]",
                    "value": engine["value"],
                    "disabled": "Install first",
                }
            )

    choices.append(questionary.Separator())
    choices.append({"name": "⬅️ Cancel", "value": None})

    return questionary.select(
        "Select database engine:",
        choices=choices,
        qmark="🗄️",
        pointer="▶",
    ).ask()


def show_database_status():
    """Show installed relational database engines."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Database Management", "Status"])

    table = Table(title="Installed Database Engines", box=box.ROUNDED, header_style="bold magenta")
    table.add_column("Engine", style="cyan")
    table.add_column("Installed", justify="center")

    for engine in get_installed_engines():
        table.add_row(engine["name"], "🟢" if engine["installed"] else "⚪")

    console.print()
    console.print(table)
    console.print()
    questionary.press_any_key_to_continue().ask()


def build_admin_command(engine: str, sql: str) -> str:
    """Build a display-friendly admin command for the selected engine."""
    if engine == "postgresql":
        return f'sudo -u postgres psql -tAc "{sql}"'
    if engine in MYSQL_FAMILY:
        return f'sudo mysql -Nse "{sql}"'
    raise ValueError(f"Unsupported engine: {engine}")


def build_admin_argv(engine: str, sql: str) -> list[str]:
    """Build a safe argv command for the selected engine."""
    if engine == "postgresql":
        return ["sudo", "-u", "postgres", "psql", "-tAc", sql]
    if engine in MYSQL_FAMILY:
        return ["sudo", "mysql", "-Nse", sql]
    raise ValueError(f"Unsupported engine: {engine}")


def validate_identifier(name: str) -> bool:
    """Allow only safe database and username identifiers."""
    return bool(IDENTIFIER_PATTERN.fullmatch(name))


def sql_string(value: str) -> str:
    """Escape a SQL string literal."""
    return value.replace("'", "''")


def pg_identifier(name: str) -> str:
    """Quote a PostgreSQL identifier."""
    return f'"{name}"'


def mysql_identifier(name: str) -> str:
    """Quote a MySQL-family identifier."""
    return f"`{name}`"


def build_create_database_sql(engine: str, database: str) -> str:
    """Build SQL to create a database."""
    if engine == "postgresql":
        return f"CREATE DATABASE {pg_identifier(database)};"
    return f"CREATE DATABASE {mysql_identifier(database)};"


def build_create_user_sql(engine: str, username: str, password: str, host: str = "%") -> str:
    """Build SQL to create a database user."""
    escaped_password = sql_string(password)
    if engine == "postgresql":
        return f"CREATE USER {pg_identifier(username)} WITH PASSWORD '{escaped_password}';"
    return f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{escaped_password}';"


def build_grant_access_sql(engine: str, username: str, database: str, host: str = "%") -> str:
    """Build SQL to grant a user full database access."""
    if engine == "postgresql":
        return f"GRANT ALL PRIVILEGES ON DATABASE {pg_identifier(database)} TO {pg_identifier(username)};"
    return f"GRANT ALL PRIVILEGES ON {mysql_identifier(database)}.* TO '{username}'@'{host}'; FLUSH PRIVILEGES;"


def build_reset_password_sql(engine: str, username: str, password: str, host: str = "%") -> str:
    """Build SQL to reset a user's password."""
    escaped_password = sql_string(password)
    if engine == "postgresql":
        return f"ALTER USER {pg_identifier(username)} WITH PASSWORD '{escaped_password}';"
    return f"ALTER USER '{username}'@'{host}' IDENTIFIED BY '{escaped_password}';"


def build_delete_database_sql(engine: str, database: str) -> str:
    """Build SQL to delete a database."""
    if engine == "postgresql":
        return f"DROP DATABASE {pg_identifier(database)};"
    return f"DROP DATABASE {mysql_identifier(database)};"


def build_delete_user_sql(engine: str, username: str, host: str = "%") -> str:
    """Build SQL to delete a database user."""
    if engine == "postgresql":
        return f"DROP USER {pg_identifier(username)};"
    return f"DROP USER '{username}'@'{host}';"


def run_database_sql(engine: str, sql: str) -> tuple[int, str, str]:
    """Execute a SQL statement for the selected engine."""
    return run_command(build_admin_argv(engine, sql), check=False)


def filter_system_databases(engine: str, names: list[str]) -> list[str]:
    """Remove system databases from list views."""
    hidden = SYSTEM_DATABASES.get(engine, set())
    return [name for name in names if name and name not in hidden]


def filter_system_users(engine: str, names: list[str]) -> list[str]:
    """Remove obvious system users from list views."""
    hidden = SYSTEM_USERS.get(engine, set())
    return [name for name in names if name and name not in hidden]


def parse_lines(output: str) -> list[str]:
    """Split command output into a clean list of values."""
    return [line.strip() for line in output.splitlines() if line.strip()]


def list_databases(engine: str) -> list[str]:
    """List non-system databases for the selected engine."""
    sql = "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;"
    if engine in MYSQL_FAMILY:
        sql = "SHOW DATABASES;"

    code, stdout, _ = run_database_sql(engine, sql)
    if code != 0:
        return []
    return filter_system_databases(engine, parse_lines(stdout))


def list_users(engine: str) -> list[str]:
    """List non-system login users for the selected engine."""
    sql = "SELECT rolname FROM pg_roles WHERE rolcanlogin = true ORDER BY rolname;"
    if engine in MYSQL_FAMILY:
        sql = "SELECT CONCAT(User, '@', Host) FROM mysql.user ORDER BY User, Host;"

    code, stdout, _ = run_database_sql(engine, sql)
    if code != 0:
        return []
    return filter_system_users(engine, parse_lines(stdout))


def create_database(engine: str, database: str) -> bool:
    """Create a database after validation."""
    if not validate_identifier(database):
        print_error("Database names may only contain letters, numbers, and underscores.")
        return False

    code, _, stderr = run_database_sql(engine, build_create_database_sql(engine, database))
    if code != 0:
        print_error(stderr or "Failed to create database.")
        return False

    print_success(f"Database '{database}' created.")
    return True


def create_user(engine: str, username: str, password: str, host: str = "%") -> bool:
    """Create a database user after validation."""
    if not validate_identifier(username):
        print_error("Usernames may only contain letters, numbers, and underscores.")
        return False

    code, _, stderr = run_database_sql(engine, build_create_user_sql(engine, username, password, host=host))
    if code != 0:
        print_error(stderr or "Failed to create user.")
        return False

    print_success(f"User '{username}' created.")
    return True


def grant_user_access(engine: str, username: str, database: str, host: str = "%") -> bool:
    """Grant a user access to a database."""
    if not validate_identifier(username) or not validate_identifier(database):
        print_error("Names may only contain letters, numbers, and underscores.")
        return False

    code, _, stderr = run_database_sql(engine, build_grant_access_sql(engine, username, database, host=host))
    if code != 0:
        print_error(stderr or "Failed to grant access.")
        return False

    print_success(f"Granted '{username}' access to '{database}'.")
    return True


def reset_user_password(engine: str, username: str, password: str, host: str = "%") -> bool:
    """Reset a database user's password."""
    if not validate_identifier(username):
        print_error("Usernames may only contain letters, numbers, and underscores.")
        return False

    code, _, stderr = run_database_sql(engine, build_reset_password_sql(engine, username, password, host=host))
    if code != 0:
        print_error(stderr or "Failed to reset password.")
        return False

    print_success(f"Password updated for '{username}'.")
    return True


def delete_database(engine: str, database: str) -> bool:
    """Delete a database with confirmation."""
    if not validate_identifier(database):
        print_error("Database names may only contain letters, numbers, and underscores.")
        return False
    if not confirm_action(f"Delete database '{database}'?", default=False):
        return False

    code, _, stderr = run_database_sql(engine, build_delete_database_sql(engine, database))
    if code != 0:
        print_error(stderr or "Failed to delete database.")
        return False

    print_success(f"Database '{database}' deleted.")
    return True


def delete_user(engine: str, username: str, host: str = "%") -> bool:
    """Delete a database user with confirmation."""
    if not validate_identifier(username):
        print_error("Usernames may only contain letters, numbers, and underscores.")
        return False
    if not confirm_action(f"Delete user '{username}'?", default=False):
        return False

    code, _, stderr = run_database_sql(engine, build_delete_user_sql(engine, username, host=host))
    if code != 0:
        print_error(stderr or "Failed to delete user.")
        return False

    print_success(f"User '{username}' deleted.")
    return True


def show_name_list(title: str, values: list[str]):
    """Render a simple list table."""
    clear_screen()
    print_header()
    print_breadcrumb(["Main", "Database Management", title])
    console.print()

    if not values:
        print_warning("No entries found.")
        console.print()
        questionary.press_any_key_to_continue().ask()
        return

    table = Table(title=title, box=box.ROUNDED, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    for value in values:
        table.add_row(value)

    console.print(table)
    console.print()
    questionary.press_any_key_to_continue().ask()


def prompt_identifier(message: str) -> Optional[str]:
    """Prompt for a validated identifier."""
    value = questionary.text(
        message,
        validate=lambda text: bool(text and validate_identifier(text)) or "Letters, numbers, underscores only",
    ).ask()
    return value or None


def prompt_password(message: str = "Password:") -> Optional[str]:
    """Prompt for a non-empty password."""
    value = questionary.password(
        message,
        validate=lambda text: bool(text) or "Password is required",
    ).ask()
    return value or None


def prompt_mysql_host() -> str:
    """Prompt for a MySQL/MariaDB host scope."""
    return questionary.text("Host scope:", default="%").ask() or "%"


def prompt_list_databases():
    """Prompt for engine and display databases."""
    engine = choose_engine()
    if engine:
        show_name_list("Databases", list_databases(engine))


def prompt_list_users():
    """Prompt for engine and display users."""
    engine = choose_engine()
    if engine:
        show_name_list("Users", list_users(engine))


def prompt_create_database():
    """Prompt for database creation."""
    engine = choose_engine()
    if not engine:
        return

    database = prompt_identifier("Database name:")
    if database:
        create_database(engine, database)
        console.print()
        questionary.press_any_key_to_continue().ask()


def prompt_create_user():
    """Prompt for user creation."""
    engine = choose_engine()
    if not engine:
        return

    username = prompt_identifier("Username:")
    password = prompt_password()
    if not username or not password:
        return

    host = prompt_mysql_host() if engine in MYSQL_FAMILY else "%"
    create_user(engine, username, password, host=host)
    console.print()
    questionary.press_any_key_to_continue().ask()


def prompt_grant_access():
    """Prompt for grant flow."""
    engine = choose_engine()
    if not engine:
        return

    username = prompt_identifier("Username:")
    database = prompt_identifier("Database name:")
    if not username or not database:
        return

    host = prompt_mysql_host() if engine in MYSQL_FAMILY else "%"
    grant_user_access(engine, username, database, host=host)
    console.print()
    questionary.press_any_key_to_continue().ask()


def prompt_reset_password():
    """Prompt for password reset flow."""
    engine = choose_engine()
    if not engine:
        return

    username = prompt_identifier("Username:")
    password = prompt_password("New password:")
    if not username or not password:
        return

    host = prompt_mysql_host() if engine in MYSQL_FAMILY else "%"
    reset_user_password(engine, username, password, host=host)
    console.print()
    questionary.press_any_key_to_continue().ask()


def prompt_delete_database():
    """Prompt for database deletion."""
    engine = choose_engine()
    if not engine:
        return

    database = prompt_identifier("Database name to delete:")
    if database:
        delete_database(engine, database)
        console.print()
        questionary.press_any_key_to_continue().ask()


def prompt_delete_user():
    """Prompt for user deletion."""
    engine = choose_engine()
    if not engine:
        return

    username = prompt_identifier("Username to delete:")
    if not username:
        return

    host = prompt_mysql_host() if engine in MYSQL_FAMILY else "%"
    delete_user(engine, username, host=host)
    console.print()
    questionary.press_any_key_to_continue().ask()
