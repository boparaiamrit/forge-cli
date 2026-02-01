"""Test that all modules can be imported correctly."""

def test_all_imports():
    """Verify all module imports work."""
    from sites import run_sites_menu
    from sslcerts import run_ssl_menu
    from services import run_services_menu
    from logs import run_logs_menu
    from monitor import run_monitor_menu
    from diagnostics import run_diagnostics_menu
    from php import run_php_menu
    from cron import run_cron_menu
    from security import run_security_menu
    from auditor import run_auditor_menu
    from cve import run_cve_menu
    from disk import run_disk_menu
    from alerts import run_alerts_menu
    from updater import run_updater_menu
    from installers import run_installer_menu

    # Check Panel import in sites
    from sites import Panel

    print("All imports OK")


if __name__ == "__main__":
    test_all_imports()
