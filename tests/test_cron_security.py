"""
Tests for Cron and Security modules
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCronModule:
    """Tests for cron management functions."""

    def test_cron_schedules_structure(self):
        """Test CRON_SCHEDULES has proper structure."""
        from cron import CRON_SCHEDULES

        assert len(CRON_SCHEDULES) > 5

        for key, value in CRON_SCHEDULES.items():
            assert "cron" in value
            assert "desc" in value
            # Cron expression should have 5 parts
            parts = value["cron"].split()
            assert len(parts) == 5

    def test_cron_to_human_every_minute(self):
        """Test cron expression to human readable."""
        from cron import cron_to_human

        assert cron_to_human("* * * * *") == "Every minute"
        assert cron_to_human("0 * * * *") == "Every hour"
        assert cron_to_human("0 0 * * *") == "Daily at midnight"

    def test_cron_to_human_custom(self):
        """Test cron to human for custom expressions."""
        from cron import cron_to_human

        result = cron_to_human("0 3 * * *")
        assert "3:00" in result or "3" in result

    @patch("cron.run_command")
    def test_get_crontab_entries(self, mock_run):
        """Test parsing crontab entries."""
        from cron import get_crontab_entries

        mock_run.return_value = (0, "0 * * * * /bin/command\n*/5 * * * * /bin/other", "")

        entries = get_crontab_entries()

        assert len(entries) == 2
        assert entries[0]["minute"] == "0"
        assert entries[0]["command"] == "/bin/command"
        assert entries[1]["minute"] == "*/5"

    @patch("cron.run_command")
    def test_get_crontab_entries_empty(self, mock_run):
        """Test empty crontab."""
        from cron import get_crontab_entries

        mock_run.return_value = (1, "", "no crontab")

        entries = get_crontab_entries()
        assert entries == []


class TestSecurityModule:
    """Tests for security module functions."""

    def test_scan_report_dir_exists(self):
        """Test SCAN_REPORT_DIR is defined."""
        from security import SCAN_REPORT_DIR

        assert SCAN_REPORT_DIR is not None
        assert isinstance(SCAN_REPORT_DIR, Path)

    def test_parse_clamscan_output_clean(self):
        """Test parsing clean scan output."""
        from security import parse_clamscan_output

        output = """
Scanned files: 100
Infected files: 0
Data scanned: 50.00 MB
"""
        result = parse_clamscan_output(output)

        assert result["files_scanned"] == 100
        assert result["infected_files"] == 0
        assert result["data_scanned"] == "50.00 MB"
        assert result["infected_list"] == []

    def test_parse_clamscan_output_infected(self):
        """Test parsing infected scan output."""
        from security import parse_clamscan_output

        output = """
/var/www/malware.php: Eicar-Test-Signature FOUND
Scanned files: 50
Infected files: 1
Data scanned: 25.00 MB
"""
        result = parse_clamscan_output(output)

        assert result["infected_files"] == 1
        assert len(result["infected_list"]) == 1
        assert "/var/www/malware.php" in result["infected_list"][0]

    def test_security_menu_choices(self):
        """Test security menu has proper choices."""
        from security import SECURITY_MENU_CHOICES

        values = [c.get("value") if isinstance(c, dict) else None
                  for c in SECURITY_MENU_CHOICES]

        assert "install" in values
        assert "quick_scan" in values
        assert "scan_web" in values
        assert "file_changes" in values


class TestSSLRenewalTracking:
    """Tests for SSL certificate renewal tracking."""

    def test_parse_certbot_certificates(self):
        """Test parsing certbot certificates output."""
        from sslcerts import parse_certbot_certificates

        output = """
Certificate Name: example.com
  Domains: example.com www.example.com
  Expiry Date: 2024-06-15 10:30:45+00:00 (VALID: 89 days)
  Certificate Path: /etc/letsencrypt/live/example.com/fullchain.pem
  Private Key Path: /etc/letsencrypt/live/example.com/privkey.pem

Certificate Name: api.example.com
  Domains: api.example.com
  Expiry Date: 2024-05-01 08:00:00+00:00 (VALID: 45 days)
"""
        certs = parse_certbot_certificates(output)

        assert len(certs) == 2
        assert certs[0]["name"] == "example.com"
        assert certs[0]["days_remaining"] == 89
        assert certs[0]["expiry"] == "2024-06-15"
        assert certs[1]["name"] == "api.example.com"
        assert certs[1]["days_remaining"] == 45

    def test_parse_certbot_empty(self):
        """Test parsing empty certbot output."""
        from sslcerts import parse_certbot_certificates

        result = parse_certbot_certificates("")
        assert result == []

        result = parse_certbot_certificates("No certificates found.")
        assert result == []
