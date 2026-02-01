"""
Tests for State Management module
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestStateManagement:
    """Tests for state management functions."""

    def test_get_default_state(self):
        """Test default state structure."""
        from state import get_default_state

        state = get_default_state()

        assert "version" in state
        assert "sites" in state
        assert "pending_operations" in state
        assert state["sites"] == {}
        assert state["pending_operations"] == []

    def test_save_and_load_site_state(self, tmp_path, monkeypatch):
        """Test saving and loading site state."""
        from state import save_site_state, get_site_state, load_state, STATE_DIR, STATE_FILE, LINEAGE_FILE

        # Mock the state directory
        test_state_dir = tmp_path / ".forge"
        test_state_file = test_state_dir / "state.json"
        test_lineage_file = test_state_dir / "lineage.json"

        monkeypatch.setattr("state.STATE_DIR", test_state_dir)
        monkeypatch.setattr("state.STATE_FILE", test_state_file)
        monkeypatch.setattr("state.LINEAGE_FILE", test_lineage_file)

        # Save a site
        save_site_state(
            domain="example.com",
            site_type="nextjs",
            ssl_enabled=True,
            port=3000,
        )

        # Load and verify
        site = get_site_state("example.com")

        assert site is not None
        assert site["domain"] == "example.com"
        assert site["type"] == "nextjs"
        assert site["ssl_enabled"] is True
        assert site["port"] == 3000

    def test_update_site_ssl(self, tmp_path, monkeypatch):
        """Test updating site SSL status."""
        from state import save_site_state, update_site_ssl, get_site_state, STATE_DIR, STATE_FILE, LINEAGE_FILE

        test_state_dir = tmp_path / ".forge"
        test_state_file = test_state_dir / "state.json"
        test_lineage_file = test_state_dir / "lineage.json"

        monkeypatch.setattr("state.STATE_DIR", test_state_dir)
        monkeypatch.setattr("state.STATE_FILE", test_state_file)
        monkeypatch.setattr("state.LINEAGE_FILE", test_lineage_file)

        # Save a site without SSL
        save_site_state(
            domain="example.com",
            site_type="php",
            ssl_enabled=False,
        )

        # Update SSL status
        update_site_ssl("example.com", True)

        # Verify
        site = get_site_state("example.com")
        assert site["ssl_enabled"] is True

    def test_delete_site_state(self, tmp_path, monkeypatch):
        """Test deleting site from state."""
        from state import save_site_state, delete_site_state, get_site_state, STATE_DIR, STATE_FILE, LINEAGE_FILE

        test_state_dir = tmp_path / ".forge"
        test_state_file = test_state_dir / "state.json"
        test_lineage_file = test_state_dir / "lineage.json"

        monkeypatch.setattr("state.STATE_DIR", test_state_dir)
        monkeypatch.setattr("state.STATE_FILE", test_state_file)
        monkeypatch.setattr("state.LINEAGE_FILE", test_lineage_file)

        # Save and then delete
        save_site_state(domain="example.com", site_type="static")
        delete_site_state("example.com")

        # Verify it's gone
        site = get_site_state("example.com")
        assert site is None

    def test_pending_operations(self, tmp_path, monkeypatch):
        """Test pending operations management."""
        from state import (
            add_pending_operation,
            complete_pending_operation,
            get_pending_operations,
            STATE_DIR,
            STATE_FILE,
            LINEAGE_FILE
        )

        test_state_dir = tmp_path / ".forge"
        test_state_file = test_state_dir / "state.json"
        test_lineage_file = test_state_dir / "lineage.json"

        monkeypatch.setattr("state.STATE_DIR", test_state_dir)
        monkeypatch.setattr("state.STATE_FILE", test_state_file)
        monkeypatch.setattr("state.LINEAGE_FILE", test_lineage_file)

        # Add pending operation
        op_id = add_pending_operation("ssl_provision", {"domain": "example.com"})

        assert op_id is not None

        # Get pending operations
        pending = get_pending_operations("ssl_provision")
        assert len(pending) == 1
        assert pending[0]["data"]["domain"] == "example.com"

        # Complete it
        complete_pending_operation(op_id)

        # Should no longer be pending
        pending = get_pending_operations("ssl_provision")
        assert len(pending) == 0


class TestNginxTemplates:
    """Tests for Nginx template rendering."""

    def test_nodejs_template_rendering(self):
        """Test Node.js template renders correctly."""
        from nginx.templates import render_template

        config = render_template(
            site_type="nextjs",
            domain="example.com",
            www=True,
            port=3000,
        )

        assert "example.com" in config
        assert "www.example.com" in config
        assert "proxy_pass http://127.0.0.1:3000" in config
        assert "client_max_body_size" in config
        assert "proxy_connect_timeout" in config

    def test_php_template_rendering(self):
        """Test PHP template renders correctly."""
        from nginx.templates import render_template

        config = render_template(
            site_type="php",
            domain="laravel.test",
            www=True,
            document_root="/var/www/laravel/public",
            php_version="8.3",
        )

        assert "laravel.test" in config
        assert "/var/www/laravel/public" in config
        assert "php8.3-fpm.sock" in config
        assert "fastcgi_pass" in config

    def test_static_template_rendering(self):
        """Test static site template renders correctly."""
        from nginx.templates import render_template

        config = render_template(
            site_type="static",
            domain="static.example.com",
            www=False,
            document_root="/var/www/static",
        )

        assert "static.example.com" in config
        assert "www.static.example.com" not in config
        assert "try_files $uri $uri/ =404" in config

    def test_ssl_template_rendering(self):
        """Test SSL-enabled template renders correctly."""
        from nginx.templates import render_template

        config = render_template(
            site_type="nextjs",
            domain="secure.example.com",
            www=True,
            port=3000,
            ssl_enabled=True,
        )

        assert "listen 443 ssl http2" in config
        assert "ssl_certificate" in config
        assert "/etc/letsencrypt/live/secure.example.com" in config
        assert "return 301 https://" in config

    def test_security_headers_present(self):
        """Test security headers are included."""
        from nginx.templates import render_template

        config = render_template(
            site_type="nextjs",
            domain="example.com",
            port=3000,
        )

        assert "X-Frame-Options" in config
        assert "X-Content-Type-Options" in config
        assert "X-XSS-Protection" in config

    def test_gzip_config_present(self):
        """Test gzip configuration is included."""
        from nginx.templates import render_template

        config = render_template(
            site_type="php",
            domain="example.com",
            document_root="/var/www/example",
            php_version="8.3",
        )

        assert "gzip on" in config
        assert "gzip_types" in config


class TestNetworkUtilities:
    """Tests for network utility functions."""

    def test_check_port_open_closed(self):
        """Test checking a closed port."""
        from utils.network import check_port_open

        # Port 59999 should be closed in test environment
        result = check_port_open(59999, "127.0.0.1")
        assert result is False

    @patch("socket.socket")
    def test_check_port_open_success(self, mock_socket):
        """Test checking an open port."""
        from utils.network import check_port_open

        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 0
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        mock_socket.return_value = mock_sock_instance

        result = check_port_open(80, "127.0.0.1")
        # Since connect_ex returns 0, port should be open
        assert mock_sock_instance.connect_ex.called

    def test_check_dns_resolution_localhost(self):
        """Test DNS resolution for localhost."""
        from utils.network import check_dns_resolution

        result = check_dns_resolution("localhost")

        assert result["domain"] == "localhost"
        assert result["resolved"] is True
        assert "127.0.0.1" in result["a_records"]

    @patch("subprocess.run")
    def test_get_local_ips_mock(self, mock_run):
        """Test getting local IPs with mocked output."""
        # Mock subprocess to return empty
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        from utils.network import get_local_ips
        result = get_local_ips()

        # Should return empty list on failure
        assert isinstance(result, list)

    def test_http_check_params(self):
        """Test http_check function parameters."""
        from utils.network import http_check

        result = http_check("http://localhost:99999", timeout=1)

        assert "url" in result
        assert "success" in result
        assert "error" in result or "status_code" in result


class TestStateLineage:
    """Tests for state lineage tracking."""

    def test_record_lineage(self, tmp_path, monkeypatch):
        """Test recording lineage entries."""
        from state import (
            record_lineage, load_lineage,
            STATE_DIR, STATE_FILE, LINEAGE_FILE
        )

        test_state_dir = tmp_path / ".forge"
        test_state_file = test_state_dir / "state.json"
        test_lineage_file = test_state_dir / "lineage.json"

        monkeypatch.setattr("state.STATE_DIR", test_state_dir)
        monkeypatch.setattr("state.STATE_FILE", test_state_file)
        monkeypatch.setattr("state.LINEAGE_FILE", test_lineage_file)

        # Record a change
        record_lineage(
            entity_type="site",
            entity_id="example.com",
            action="create",
            old_state=None,
            new_state={"domain": "example.com"},
        )

        # Verify
        lineage = load_lineage()
        assert len(lineage) == 1
        assert lineage[0]["entity_type"] == "site"
        assert lineage[0]["entity_id"] == "example.com"
        assert lineage[0]["action"] == "create"

    def test_get_entity_history(self, tmp_path, monkeypatch):
        """Test getting history for a specific entity."""
        from state import (
            record_lineage, get_entity_history,
            STATE_DIR, STATE_FILE, LINEAGE_FILE
        )

        test_state_dir = tmp_path / ".forge"
        monkeypatch.setattr("state.STATE_DIR", test_state_dir)
        monkeypatch.setattr("state.STATE_FILE", test_state_dir / "state.json")
        monkeypatch.setattr("state.LINEAGE_FILE", test_state_dir / "lineage.json")

        # Record multiple changes
        record_lineage("site", "example.com", "create", None, {"domain": "example.com"})
        record_lineage("site", "other.com", "create", None, {"domain": "other.com"})
        record_lineage("site", "example.com", "update", {"ssl": False}, {"ssl": True})

        # Get history for example.com
        history = get_entity_history("site", "example.com")

        assert len(history) == 2
        assert all(h["entity_id"] == "example.com" for h in history)

    def test_get_recent_changes(self, tmp_path, monkeypatch):
        """Test getting recent changes."""
        from state import (
            record_lineage, get_recent_changes,
            STATE_DIR, STATE_FILE, LINEAGE_FILE
        )

        test_state_dir = tmp_path / ".forge"
        monkeypatch.setattr("state.STATE_DIR", test_state_dir)
        monkeypatch.setattr("state.STATE_FILE", test_state_dir / "state.json")
        monkeypatch.setattr("state.LINEAGE_FILE", test_state_dir / "lineage.json")

        # Record changes
        for i in range(10):
            record_lineage("test", f"entity_{i}", "create", None, {})

        # Get last 5
        recent = get_recent_changes(5)

        assert len(recent) == 5

    def test_export_lineage_report(self, tmp_path, monkeypatch):
        """Test exporting lineage report."""
        from state import (
            record_lineage, export_lineage_report,
            STATE_DIR, STATE_FILE, LINEAGE_FILE
        )

        test_state_dir = tmp_path / ".forge"
        monkeypatch.setattr("state.STATE_DIR", test_state_dir)
        monkeypatch.setattr("state.STATE_FILE", test_state_dir / "state.json")
        monkeypatch.setattr("state.LINEAGE_FILE", test_state_dir / "lineage.json")

        # Record some changes
        record_lineage("site", "example.com", "create", None, {})
        record_lineage("php", "8.3", "install", None, {})

        # Export report
        report = export_lineage_report()

        assert "FORGE CLI STATE LINEAGE REPORT" in report
        assert "SITE" in report
        assert "PHP" in report


class TestPHPExtensions:
    """Tests for PHP extension data."""

    def test_php_extensions_dict(self):
        """Test PHP extensions dictionary has required data."""
        from php import PHP_EXTENSIONS

        assert len(PHP_EXTENSIONS) > 20  # Should have many extensions

        # Check structure
        for ext, info in PHP_EXTENSIONS.items():
            assert "desc" in info
            assert "category" in info

    def test_extension_bundles(self):
        """Test extension bundles have valid extensions."""
        from php import EXTENSION_BUNDLES, PHP_EXTENSIONS

        for bundle_key, bundle in EXTENSION_BUNDLES.items():
            assert "name" in bundle
            assert "desc" in bundle
            assert "extensions" in bundle
            assert len(bundle["extensions"]) > 0

            # Laravel bundle should have essential extensions
            if bundle_key == "laravel":
                assert "mysql" in bundle["extensions"]
                assert "mbstring" in bundle["extensions"]
                assert "redis" in bundle["extensions"]

    def test_php_versions_list(self):
        """Test PHP versions list."""
        from php import PHP_VERSIONS

        assert "8.3" in PHP_VERSIONS
        assert "8.2" in PHP_VERSIONS
        assert len(PHP_VERSIONS) >= 5  # Should have multiple versions

    def test_php_state_functions(self, tmp_path, monkeypatch):
        """Test PHP state management functions."""
        from state import (
            save_php_state, get_php_state, add_php_extensions,
            STATE_DIR, STATE_FILE, LINEAGE_FILE
        )

        test_state_dir = tmp_path / ".forge"
        monkeypatch.setattr("state.STATE_DIR", test_state_dir)
        monkeypatch.setattr("state.STATE_FILE", test_state_dir / "state.json")
        monkeypatch.setattr("state.LINEAGE_FILE", test_state_dir / "lineage.json")

        # Save PHP state
        save_php_state("8.3", ["cli", "fpm", "mysql"])

        # Verify
        php_state = get_php_state("8.3")
        assert php_state is not None
        assert php_state["version"] == "8.3"
        assert "mysql" in php_state["extensions"]

        # Add extensions
        add_php_extensions("8.3", ["redis", "curl"])

        php_state = get_php_state("8.3")
        assert "redis" in php_state["extensions"]
        assert "curl" in php_state["extensions"]
        assert "mysql" in php_state["extensions"]  # Original still there
