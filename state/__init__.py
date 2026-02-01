"""
State Management - Persistent state for Forge CLI operations
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path


STATE_DIR = Path.home() / ".forge"
STATE_FILE = STATE_DIR / "state.json"
LINEAGE_FILE = STATE_DIR / "lineage.json"


def ensure_state_dir():
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> Dict[str, Any]:
    """Load state from disk."""
    ensure_state_dir()
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return get_default_state()
    return get_default_state()


def save_state(state: Dict[str, Any]):
    """Save state to disk."""
    ensure_state_dir()
    state["last_updated"] = datetime.now().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_default_state() -> Dict[str, Any]:
    """Return default empty state."""
    return {
        "version": "1.0.0",
        "sites": {},
        "php": {},
        "pending_operations": [],
        "last_updated": None,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SITE STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def get_site_state(domain: str) -> Optional[Dict[str, Any]]:
    """Get state for a specific site."""
    state = load_state()
    return state.get("sites", {}).get(domain)


def save_site_state(
    domain: str,
    site_type: str,
    ssl_enabled: bool = False,
    port: Optional[int] = None,
    document_root: Optional[str] = None,
    php_version: Optional[str] = None,
    enabled: bool = True,
    extra: Optional[Dict] = None,
):
    """Save or update site state."""
    state = load_state()

    if "sites" not in state:
        state["sites"] = {}

    old_state = state["sites"].get(domain)

    state["sites"][domain] = {
        "domain": domain,
        "type": site_type,
        "ssl_enabled": ssl_enabled,
        "port": port,
        "document_root": document_root,
        "php_version": php_version,
        "enabled": enabled,
        "created_at": state["sites"].get(domain, {}).get("created_at", datetime.now().isoformat()),
        "updated_at": datetime.now().isoformat(),
        **(extra or {}),
    }

    save_state(state)

    # Record lineage
    record_lineage(
        entity_type="site",
        entity_id=domain,
        action="update" if old_state else "create",
        old_state=old_state,
        new_state=state["sites"][domain],
    )


def update_site_ssl(domain: str, ssl_enabled: bool):
    """Update SSL status for a site."""
    state = load_state()
    if domain in state.get("sites", {}):
        old_ssl = state["sites"][domain].get("ssl_enabled")
        state["sites"][domain]["ssl_enabled"] = ssl_enabled
        state["sites"][domain]["updated_at"] = datetime.now().isoformat()
        save_state(state)

        # Record lineage
        record_lineage(
            entity_type="site",
            entity_id=domain,
            action="ssl_update",
            old_state={"ssl_enabled": old_ssl},
            new_state={"ssl_enabled": ssl_enabled},
        )


def delete_site_state(domain: str):
    """Remove site from state."""
    state = load_state()
    if domain in state.get("sites", {}):
        old_state = state["sites"][domain]
        del state["sites"][domain]
        save_state(state)

        # Record lineage
        record_lineage(
            entity_type="site",
            entity_id=domain,
            action="delete",
            old_state=old_state,
            new_state=None,
        )


def list_sites_state() -> Dict[str, Dict[str, Any]]:
    """Get all sites from state."""
    state = load_state()
    return state.get("sites", {})


# ═══════════════════════════════════════════════════════════════════════════════
# PHP STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def save_php_state(version: str, extensions: List[str], config: Optional[Dict] = None):
    """Save PHP version state."""
    state = load_state()

    if "php" not in state:
        state["php"] = {}

    old_state = state["php"].get(version)

    state["php"][version] = {
        "version": version,
        "extensions": extensions,
        "config": config or {},
        "installed_at": state["php"].get(version, {}).get("installed_at", datetime.now().isoformat()),
        "updated_at": datetime.now().isoformat(),
    }

    save_state(state)

    # Record lineage
    record_lineage(
        entity_type="php",
        entity_id=version,
        action="update" if old_state else "install",
        old_state=old_state,
        new_state=state["php"][version],
    )


def get_php_state(version: str) -> Optional[Dict[str, Any]]:
    """Get state for a PHP version."""
    state = load_state()
    return state.get("php", {}).get(version)


def add_php_extensions(version: str, extensions: List[str]):
    """Add extensions to PHP version state."""
    state = load_state()

    if "php" not in state:
        state["php"] = {}

    if version not in state["php"]:
        state["php"][version] = {
            "version": version,
            "extensions": [],
            "installed_at": datetime.now().isoformat(),
        }

    old_extensions = state["php"][version].get("extensions", [])
    new_extensions = list(set(old_extensions + extensions))

    state["php"][version]["extensions"] = new_extensions
    state["php"][version]["updated_at"] = datetime.now().isoformat()

    save_state(state)

    # Record lineage
    record_lineage(
        entity_type="php_extensions",
        entity_id=version,
        action="add",
        old_state={"extensions": old_extensions},
        new_state={"extensions": new_extensions},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PENDING OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def add_pending_operation(op_type: str, data: Dict[str, Any]) -> str:
    """Add a pending operation that can be resumed."""
    import uuid

    state = load_state()
    if "pending_operations" not in state:
        state["pending_operations"] = []

    op_id = str(uuid.uuid4())[:8]
    operation = {
        "id": op_id,
        "type": op_type,
        "data": data,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
    }

    state["pending_operations"].append(operation)
    save_state(state)

    # Record lineage
    record_lineage(
        entity_type="operation",
        entity_id=op_id,
        action="start",
        old_state=None,
        new_state=operation,
    )

    return op_id


def complete_pending_operation(op_id: str):
    """Mark a pending operation as complete."""
    state = load_state()
    for op in state.get("pending_operations", []):
        if op["id"] == op_id:
            op["status"] = "complete"
            op["completed_at"] = datetime.now().isoformat()

            # Record lineage
            record_lineage(
                entity_type="operation",
                entity_id=op_id,
                action="complete",
                old_state={"status": "pending"},
                new_state={"status": "complete"},
            )
            break
    save_state(state)


def get_pending_operations(op_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get pending operations, optionally filtered by type."""
    state = load_state()
    operations = [
        op for op in state.get("pending_operations", [])
        if op.get("status") == "pending"
    ]
    if op_type:
        operations = [op for op in operations if op.get("type") == op_type]
    return operations


def clear_completed_operations():
    """Remove completed operations from state."""
    state = load_state()
    state["pending_operations"] = [
        op for op in state.get("pending_operations", [])
        if op.get("status") != "complete"
    ]
    save_state(state)


# ═══════════════════════════════════════════════════════════════════════════════
# SSL CERTIFICATE STATE
# ═══════════════════════════════════════════════════════════════════════════════

def check_ssl_status(domain: str) -> Dict[str, Any]:
    """
    Check if SSL is configured for a domain.
    Returns dict with ssl_enabled, expiry_date, issuer.
    """
    import subprocess

    result = {
        "ssl_enabled": False,
        "expiry_date": None,
        "issuer": None,
        "days_remaining": None,
    }

    # Check if certificate exists
    cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
    if os.path.exists(cert_path):
        result["ssl_enabled"] = True

        # Get certificate info
        try:
            cmd = f"openssl x509 -in {cert_path} -noout -enddate"
            proc = subprocess.run(cmd.split(), capture_output=True, text=True)
            if proc.returncode == 0:
                # Parse enddate: notAfter=Dec 31 23:59:59 2024 GMT
                date_str = proc.stdout.strip().replace("notAfter=", "")
                from datetime import datetime
                try:
                    expiry = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
                    result["expiry_date"] = expiry.isoformat()
                    result["days_remaining"] = (expiry - datetime.now()).days
                except ValueError:
                    pass
        except Exception:
            pass

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# STATE LINEAGE - AUDIT TRAIL
# ═══════════════════════════════════════════════════════════════════════════════

def load_lineage() -> List[Dict[str, Any]]:
    """Load lineage history from disk."""
    ensure_state_dir()
    if LINEAGE_FILE.exists():
        try:
            with open(LINEAGE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_lineage(lineage: List[Dict[str, Any]]):
    """Save lineage history to disk."""
    ensure_state_dir()
    # Keep only last 1000 entries to prevent unbounded growth
    if len(lineage) > 1000:
        lineage = lineage[-1000:]
    with open(LINEAGE_FILE, "w") as f:
        json.dump(lineage, f, indent=2)


def record_lineage(
    entity_type: str,
    entity_id: str,
    action: str,
    old_state: Optional[Dict] = None,
    new_state: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
):
    """
    Record a state change in the lineage history.

    Args:
        entity_type: Type of entity (site, php, operation, etc.)
        entity_id: Unique identifier for the entity
        action: Action performed (create, update, delete, etc.)
        old_state: Previous state (if any)
        new_state: New state (if any)
        metadata: Additional metadata about the change
    """
    lineage = load_lineage()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "old_state": old_state,
        "new_state": new_state,
        "metadata": metadata or {},
    }

    lineage.append(entry)
    save_lineage(lineage)


def get_entity_history(entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
    """Get the history of changes for a specific entity."""
    lineage = load_lineage()
    return [
        entry for entry in lineage
        if entry.get("entity_type") == entity_type and entry.get("entity_id") == entity_id
    ]


def get_recent_changes(limit: int = 50) -> List[Dict[str, Any]]:
    """Get the most recent state changes."""
    lineage = load_lineage()
    return lineage[-limit:]


def get_changes_by_action(action: str) -> List[Dict[str, Any]]:
    """Get all changes of a specific action type."""
    lineage = load_lineage()
    return [entry for entry in lineage if entry.get("action") == action]


def get_changes_since(since: datetime) -> List[Dict[str, Any]]:
    """Get all changes since a specific datetime."""
    lineage = load_lineage()
    since_iso = since.isoformat()
    return [entry for entry in lineage if entry.get("timestamp", "") >= since_iso]


def clear_lineage():
    """Clear all lineage history."""
    save_lineage([])


def export_lineage_report() -> str:
    """Generate a human-readable lineage report."""
    lineage = load_lineage()

    if not lineage:
        return "No state changes recorded."

    report = []
    report.append("=" * 60)
    report.append("FORGE CLI STATE LINEAGE REPORT")
    report.append("=" * 60)
    report.append(f"Total entries: {len(lineage)}")
    report.append(f"Date range: {lineage[0]['timestamp'][:10]} to {lineage[-1]['timestamp'][:10]}")
    report.append("=" * 60)
    report.append("")

    # Group by entity type
    by_type = {}
    for entry in lineage:
        etype = entry.get("entity_type", "unknown")
        if etype not in by_type:
            by_type[etype] = []
        by_type[etype].append(entry)

    for etype, entries in by_type.items():
        report.append(f"[{etype.upper()}]")
        report.append("-" * 40)
        for entry in entries[-10:]:  # Show last 10 of each type
            timestamp = entry["timestamp"][:19]
            action = entry.get("action", "unknown")
            entity_id = entry.get("entity_id", "?")
            report.append(f"  {timestamp} | {action:12} | {entity_id}")
        if len(entries) > 10:
            report.append(f"  ... and {len(entries) - 10} more entries")
        report.append("")

    return "\n".join(report)

