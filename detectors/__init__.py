"""
System Detectors - Check installed software and versions
"""

from typing import TypedDict, Optional
from utils.shell import command_exists, get_command_output, run_command
import re


class SoftwareStatus(TypedDict):
    name: str
    installed: bool
    version: Optional[str]
    details: Optional[str]


def detect_nginx() -> SoftwareStatus:
    """Detect Nginx installation and version."""
    if not command_exists("nginx"):
        return {"name": "🌐 Nginx", "installed": False, "version": None, "details": None}

    output = get_command_output("nginx -v")
    # nginx -v outputs to stderr, so we need to capture it differently
    code, _, stderr = run_command("nginx -v", check=False)
    version = None
    if stderr:
        match = re.search(r"nginx/(\d+\.\d+\.\d+)", stderr)
        if match:
            version = match.group(1)

    # Check if running
    code, stdout, _ = run_command("systemctl is-active nginx", check=False)
    status = "Running" if stdout == "active" else "Stopped"

    return {
        "name": "🌐 Nginx",
        "installed": True,
        "version": version,
        "details": status,
    }


def detect_php() -> SoftwareStatus:
    """Detect PHP installation and version."""
    if not command_exists("php"):
        return {"name": "🐘 PHP", "installed": False, "version": None, "details": None}

    output = get_command_output("php -v")
    version = None
    if output:
        match = re.search(r"PHP (\d+\.\d+\.\d+)", output)
        if match:
            version = match.group(1)

    # Get loaded extensions count
    ext_output = get_command_output("php -m")
    ext_count = len(ext_output.split("\n")) if ext_output else 0

    return {
        "name": "🐘 PHP",
        "installed": True,
        "version": version,
        "details": f"{ext_count} extensions",
    }


def detect_node() -> SoftwareStatus:
    """Detect Node.js installation (via direct or NVM)."""
    if not command_exists("node"):
        return {"name": "🟢 Node.js", "installed": False, "version": None, "details": None}

    output = get_command_output("node -v")
    version = output.lstrip("v") if output else None

    # Check if NVM is installed
    nvm_dir = get_command_output("echo $NVM_DIR")
    details = "via NVM" if nvm_dir else "System"

    return {
        "name": "🟢 Node.js",
        "installed": True,
        "version": version,
        "details": details,
    }


def detect_redis() -> SoftwareStatus:
    """Detect Redis installation."""
    if not command_exists("redis-cli"):
        return {"name": "🔴 Redis", "installed": False, "version": None, "details": None}

    output = get_command_output("redis-cli --version")
    version = None
    if output:
        match = re.search(r"(\d+\.\d+\.\d+)", output)
        if match:
            version = match.group(1)

    # Check if running
    code, stdout, _ = run_command("systemctl is-active redis-server", check=False)
    if stdout != "active":
        code, stdout, _ = run_command("systemctl is-active redis", check=False)
    status = "Running" if stdout == "active" else "Stopped"

    return {
        "name": "🔴 Redis",
        "installed": True,
        "version": version,
        "details": status,
    }


def detect_certbot() -> SoftwareStatus:
    """Detect Certbot installation."""
    if not command_exists("certbot"):
        return {"name": "🔒 Certbot", "installed": False, "version": None, "details": None}

    output = get_command_output("certbot --version")
    version = None
    if output:
        match = re.search(r"certbot (\d+\.\d+\.\d+)", output)
        if match:
            version = match.group(1)

    return {
        "name": "🔒 Certbot",
        "installed": True,
        "version": version,
        "details": "Let's Encrypt",
    }


def detect_mysql() -> SoftwareStatus:
    """Detect MySQL/MariaDB installation."""
    is_mysql = command_exists("mysql")

    if not is_mysql:
        return {"name": "🗄️  MySQL", "installed": False, "version": None, "details": None}

    output = get_command_output("mysql --version")
    version = None
    db_type = "MySQL"
    if output:
        if "MariaDB" in output:
            db_type = "MariaDB"
            match = re.search(r"MariaDB.*?(\d+\.\d+\.\d+)", output)
        else:
            match = re.search(r"mysql.*?(\d+\.\d+\.\d+)", output, re.IGNORECASE)
        if match:
            version = match.group(1)

    return {
        "name": f"🗄️  {db_type}",
        "installed": True,
        "version": version,
        "details": None,
    }


def detect_postgresql() -> SoftwareStatus:
    """Detect PostgreSQL installation."""
    if not command_exists("psql"):
        return {"name": "🐘 PostgreSQL", "installed": False, "version": None, "details": None}

    output = get_command_output("psql --version")
    version = None
    if output:
        match = re.search(r"(\d+\.\d+)", output)
        if match:
            version = match.group(1)

    return {
        "name": "🐘 PostgreSQL",
        "installed": True,
        "version": version,
        "details": None,
    }


def detect_composer() -> SoftwareStatus:
    """Detect Composer installation."""
    if not command_exists("composer"):
        return {"name": "📦 Composer", "installed": False, "version": None, "details": None}

    output = get_command_output("composer --version")
    version = None
    if output:
        match = re.search(r"Composer version (\d+\.\d+\.\d+)", output)
        if match:
            version = match.group(1)

    return {
        "name": "📦 Composer",
        "installed": True,
        "version": version,
        "details": None,
    }


def detect_pm2() -> SoftwareStatus:
    """Detect PM2 process manager."""
    if not command_exists("pm2"):
        return {"name": "⚡ PM2", "installed": False, "version": None, "details": None}

    output = get_command_output("pm2 --version")
    version = output if output else None

    # Get running processes count
    list_output = get_command_output("pm2 jlist")
    if list_output:
        import json
        try:
            processes = json.loads(list_output)
            details = f"{len(processes)} processes"
        except:
            details = None
    else:
        details = None

    return {
        "name": "⚡ PM2",
        "installed": True,
        "version": version,
        "details": details,
    }


def get_system_status() -> list[SoftwareStatus]:
    """Get status of all detected software."""
    detectors = [
        detect_nginx,
        detect_php,
        detect_node,
        detect_pm2,
        detect_redis,
        detect_certbot,
        detect_mysql,
        detect_postgresql,
        detect_composer,
    ]

    return [detector() for detector in detectors]
