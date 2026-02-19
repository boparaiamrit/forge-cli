"""
Tests for v0.11.0 Features - WebSocket Proxy, Multi-Upstream, Basic Auth

Tests the Nginx template rendering for:
- Additional proxy path → port mappings
- WebSocket location blocks
- HTTP Basic Auth directives
- Combined configurations
- State persistence of new fields
"""

import pytest

from nginx.templates import render_template, get_template_types


# ═══════════════════════════════════════════════════════════════════════════════
# PROXY PATHS
# ═══════════════════════════════════════════════════════════════════════════════


class TestProxyPaths:
    """Test additional reverse-proxy location blocks in rendered configs."""

    def test_single_proxy_path_rendered(self):
        """A single proxy path should produce a location block."""
        result = render_template(
            site_type="nextjs",
            domain="app.example.com",
            port=3000,
            proxy_paths=[
                {"path": "/api/", "port": 8000, "description": "REST API"},
            ],
        )

        assert "location /api/" in result
        assert "proxy_pass         http://127.0.0.1:8000/" in result
        assert "REST API" in result

    def test_multiple_proxy_paths(self):
        """Multiple proxy paths should all appear in the config."""
        result = render_template(
            site_type="nextjs",
            domain="app.example.com",
            port=3000,
            proxy_paths=[
                {"path": "/api/", "port": 8000, "description": "REST API"},
                {"path": "/graphql/", "port": 4000, "description": "GraphQL"},
            ],
        )

        assert "location /api/" in result
        assert "proxy_pass         http://127.0.0.1:8000/" in result
        assert "location /graphql/" in result
        assert "proxy_pass         http://127.0.0.1:4000/" in result

    def test_proxy_path_without_description(self):
        """Proxy paths without a description should still render."""
        result = render_template(
            site_type="nextjs",
            domain="app.example.com",
            port=3000,
            proxy_paths=[
                {"path": "/backend/", "port": 9000, "description": None},
            ],
        )

        assert "location /backend/" in result
        assert "proxy_pass         http://127.0.0.1:9000/" in result

    def test_no_proxy_paths_means_no_extra_blocks(self):
        """When proxy_paths is empty or None, no extra location blocks appear."""
        result = render_template(
            site_type="nextjs",
            domain="clean.example.com",
            port=3000,
            proxy_paths=[],
        )

        # The primary proxy_pass for port 3000 must exist
        assert "proxy_pass http://127.0.0.1:3000" in result
        # But no extra proxy block comment marker
        assert "── Proxy:" not in result

    def test_proxy_paths_have_required_headers(self):
        """Each proxy path block should include proper headers."""
        result = render_template(
            site_type="nextjs",
            domain="app.example.com",
            port=3000,
            proxy_paths=[
                {"path": "/api/", "port": 8000, "description": None},
            ],
        )

        assert "X-Real-IP" in result
        assert "X-Forwarded-For" in result
        assert "X-Forwarded-Proto" in result
        assert "proxy_read_timeout  300s" in result

    def test_proxy_paths_in_ssl_template(self):
        """Proxy paths should work in the SSL template variant too."""
        result = render_template(
            site_type="nextjs",
            domain="secure.example.com",
            port=3000,
            ssl_enabled=True,
            proxy_paths=[
                {"path": "/api/", "port": 8000, "description": "API"},
            ],
        )

        assert "listen 443 ssl http2" in result
        assert "location /api/" in result
        assert "proxy_pass         http://127.0.0.1:8000/" in result

    def test_proxy_paths_in_php_template(self):
        """PHP template should also render proxy path blocks (via basic_auth_block placeholder)."""
        result = render_template(
            site_type="php",
            domain="laravel.example.com",
            document_root="/var/www/laravel/public",
            php_version="8.3",
        )

        # PHP template shouldn't have extra proxy blocks when none requested
        assert "── Proxy:" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET PATHS
# ═══════════════════════════════════════════════════════════════════════════════


class TestWebSocketPaths:
    """Test WebSocket proxy location blocks."""

    def test_single_ws_path_rendered(self):
        """A single WS path should produce a WebSocket location block."""
        result = render_template(
            site_type="nextjs",
            domain="app.example.com",
            port=3000,
            ws_paths=[
                {"path": "/ws", "port": 8000, "upstream_path": "/ws", "description": "WebSocket"},
            ],
        )

        assert "location /ws" in result
        assert "proxy_pass         http://127.0.0.1:8000/ws" in result
        assert 'proxy_set_header   Upgrade    $http_upgrade' in result
        assert 'proxy_set_header   Connection "upgrade"' in result

    def test_ws_keepalive_timeouts(self):
        """WebSocket blocks should have long keepalive timeouts (86400s)."""
        result = render_template(
            site_type="nextjs",
            domain="app.example.com",
            port=3000,
            ws_paths=[
                {"path": "/ws", "port": 8000, "upstream_path": "/ws", "description": None},
            ],
        )

        assert "proxy_read_timeout  86400s" in result
        assert "proxy_send_timeout  86400s" in result

    def test_multiple_ws_paths(self):
        """Multiple WebSocket paths should all render."""
        result = render_template(
            site_type="nextjs",
            domain="app.example.com",
            port=3000,
            ws_paths=[
                {"path": "/ws", "port": 8000, "upstream_path": "/ws", "description": "Orders"},
                {"path": "/ws/chat", "port": 8001, "upstream_path": "/chat", "description": "Chat"},
            ],
        )

        assert "proxy_pass         http://127.0.0.1:8000/ws" in result
        assert "proxy_pass         http://127.0.0.1:8001/chat" in result

    def test_ws_path_different_upstream(self):
        """WS upstream_path can differ from the public path."""
        result = render_template(
            site_type="nextjs",
            domain="app.example.com",
            port=3000,
            ws_paths=[
                {"path": "/live", "port": 9000, "upstream_path": "/socket", "description": None},
            ],
        )

        assert "location /live" in result
        assert "proxy_pass         http://127.0.0.1:9000/socket" in result

    def test_no_ws_paths_means_no_ws_blocks(self):
        """When ws_paths is empty, no WS blocks appear."""
        result = render_template(
            site_type="nextjs",
            domain="clean.example.com",
            port=3000,
            ws_paths=[],
        )

        assert "── WebSocket:" not in result

    def test_ws_paths_in_ssl_template(self):
        """WebSocket paths should work in SSL template."""
        result = render_template(
            site_type="nextjs",
            domain="secure.example.com",
            port=3000,
            ssl_enabled=True,
            ws_paths=[
                {"path": "/ws", "port": 8000, "upstream_path": "/ws", "description": "WS"},
            ],
        )

        assert "listen 443 ssl http2" in result
        assert "location /ws" in result
        assert 'proxy_set_header   Connection "upgrade"' in result


# ═══════════════════════════════════════════════════════════════════════════════
# BASIC AUTH
# ═══════════════════════════════════════════════════════════════════════════════


class TestBasicAuth:
    """Test HTTP Basic Authentication directives."""

    def test_basic_auth_enabled(self):
        """When basic_auth=True, auth directives should appear."""
        result = render_template(
            site_type="nextjs",
            domain="secret.example.com",
            port=3000,
            basic_auth=True,
        )

        assert 'auth_basic           "Restricted Access"' in result
        assert "auth_basic_user_file /etc/nginx/.htpasswd-secret.example.com" in result

    def test_basic_auth_custom_realm(self):
        """Custom realm message should appear in the auth directive."""
        result = render_template(
            site_type="nextjs",
            domain="admin.example.com",
            port=3000,
            basic_auth=True,
            basic_auth_realm="Admin Panel",
        )

        assert 'auth_basic           "Admin Panel"' in result
        assert "auth_basic_user_file /etc/nginx/.htpasswd-admin.example.com" in result

    def test_basic_auth_disabled_by_default(self):
        """Auth directives should NOT appear when basic_auth is False/omitted."""
        result = render_template(
            site_type="nextjs",
            domain="public.example.com",
            port=3000,
        )

        assert "auth_basic" not in result
        assert ".htpasswd" not in result

    def test_basic_auth_explicitly_disabled(self):
        """Auth directives should NOT appear when basic_auth=False."""
        result = render_template(
            site_type="nextjs",
            domain="public.example.com",
            port=3000,
            basic_auth=False,
        )

        assert "auth_basic" not in result

    def test_basic_auth_with_ssl(self):
        """Basic auth should work in SSL template."""
        result = render_template(
            site_type="nextjs",
            domain="secure.example.com",
            port=3000,
            ssl_enabled=True,
            basic_auth=True,
            basic_auth_realm="Production",
        )

        assert "listen 443 ssl http2" in result
        assert 'auth_basic           "Production"' in result
        assert "auth_basic_user_file /etc/nginx/.htpasswd-secure.example.com" in result

    def test_basic_auth_on_php_template(self):
        """PHP template should also support basic auth."""
        result = render_template(
            site_type="php",
            domain="admin.example.com",
            document_root="/var/www/admin/public",
            php_version="8.3",
            basic_auth=True,
            basic_auth_realm="Private",
        )

        assert 'auth_basic           "Private"' in result
        assert "auth_basic_user_file /etc/nginx/.htpasswd-admin.example.com" in result

    def test_basic_auth_on_static_template(self):
        """Static template should also support basic auth."""
        result = render_template(
            site_type="static",
            domain="docs.example.com",
            document_root="/var/www/docs",
            basic_auth=True,
        )

        assert 'auth_basic           "Restricted Access"' in result
        assert "auth_basic_user_file /etc/nginx/.htpasswd-docs.example.com" in result


# ═══════════════════════════════════════════════════════════════════════════════
# COMBINED CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════


class TestCombinedConfig:
    """Test configurations with multiple features enabled simultaneously."""

    def test_full_trading_setup(self):
        """Simulate the full trading UI setup: WS + proxy + auth + SSL."""
        result = render_template(
            site_type="nextjs",
            domain="trading.example.com",
            www=False,
            port=3000,
            ssl_enabled=True,
            basic_auth=True,
            basic_auth_realm="Trading Dashboard",
            proxy_paths=[
                {"path": "/api/", "port": 8000, "description": "Mock Exchange REST API"},
            ],
            ws_paths=[
                {"path": "/ws", "port": 8000, "upstream_path": "/ws", "description": "Real-time updates"},
            ],
        )

        # SSL
        assert "listen 443 ssl http2" in result
        assert "return 301 https://$server_name$request_uri" in result

        # Primary proxy
        assert "proxy_pass http://127.0.0.1:3000" in result

        # Extra proxy
        assert "location /api/" in result
        assert "proxy_pass         http://127.0.0.1:8000/" in result
        assert "Mock Exchange REST API" in result

        # WebSocket
        assert "location /ws" in result
        assert "proxy_pass         http://127.0.0.1:8000/ws" in result
        assert 'proxy_set_header   Connection "upgrade"' in result
        assert "Real-time updates" in result

        # Basic Auth
        assert 'auth_basic           "Trading Dashboard"' in result
        assert "auth_basic_user_file /etc/nginx/.htpasswd-trading.example.com" in result

        # Security headers still present
        assert "X-Frame-Options" in result
        assert "X-Content-Type-Options" in result

        # Gzip still present
        assert "gzip on" in result

    def test_proxy_and_ws_without_auth(self):
        """Proxy + WS without basic auth should not include auth directives."""
        result = render_template(
            site_type="nextjs",
            domain="app.example.com",
            port=3000,
            proxy_paths=[
                {"path": "/api/", "port": 8000, "description": None},
            ],
            ws_paths=[
                {"path": "/ws", "port": 8000, "upstream_path": "/ws", "description": None},
            ],
        )

        assert "location /api/" in result
        assert "location /ws" in result
        assert "auth_basic" not in result

    def test_auth_without_proxy_or_ws(self):
        """Auth alone should work without proxy or WS paths."""
        result = render_template(
            site_type="nextjs",
            domain="simple.example.com",
            port=3000,
            basic_auth=True,
        )

        assert "auth_basic" in result
        assert "── Proxy:" not in result
        assert "── WebSocket:" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════════════


class TestBackwardCompatibility:
    """Ensure existing usage without new params still works identically."""

    def test_nextjs_without_new_params(self):
        """Next.js template should work as before with no new params."""
        result = render_template(
            site_type="nextjs",
            domain="legacy.example.com",
            www=True,
            port=3000,
        )

        assert "legacy.example.com" in result
        assert "www.legacy.example.com" in result
        assert "proxy_pass http://127.0.0.1:3000" in result
        assert "auth_basic" not in result
        assert "── Proxy:" not in result
        assert "── WebSocket:" not in result

    def test_php_without_new_params(self):
        """PHP template should work as before."""
        result = render_template(
            site_type="php",
            domain="laravel.example.com",
            www=True,
            document_root="/var/www/laravel/public",
            php_version="8.3",
        )

        assert "fastcgi_pass" in result
        assert "php8.3-fpm.sock" in result
        assert "auth_basic" not in result

    def test_static_without_new_params(self):
        """Static template should work as before."""
        result = render_template(
            site_type="static",
            domain="static.example.com",
            www=True,
            document_root="/var/www/static",
        )

        assert "try_files $uri $uri/ =404" in result
        assert "auth_basic" not in result

    def test_ssl_without_new_params(self):
        """SSL template should work as before."""
        result = render_template(
            site_type="nextjs",
            domain="secure.example.com",
            www=True,
            port=3000,
            ssl_enabled=True,
        )

        assert "listen 443 ssl http2" in result
        assert "ssl_certificate" in result
        assert "auth_basic" not in result

    def test_get_template_types_unchanged(self):
        """Template types list should still return same options."""
        types = get_template_types()
        values = [t["value"] for t in types]

        assert "nextjs" in values
        assert "nuxt" in values
        assert "php" in values
        assert "static" in values
        assert len(types) == 4


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTION UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestHelperImports:
    """Test that new helper functions from sites module are importable."""

    def test_collect_helpers_exist(self):
        """Helper functions should be importable (requires questionary)."""
        questionary = pytest.importorskip("questionary")
        from sites import _collect_proxy_paths
        from sites import _collect_ws_paths
        from sites import _collect_basic_auth
        from sites import _provision_htpasswd

        assert callable(_collect_proxy_paths)
        assert callable(_collect_ws_paths)
        assert callable(_collect_basic_auth)
        assert callable(_provision_htpasswd)

    def test_render_template_accepts_new_params(self):
        """render_template should accept all new keyword arguments."""
        import inspect
        sig = inspect.signature(render_template)
        param_names = list(sig.parameters.keys())

        assert "proxy_paths" in param_names
        assert "ws_paths" in param_names
        assert "basic_auth" in param_names
        assert "basic_auth_realm" in param_names


# ═══════════════════════════════════════════════════════════════════════════════
# VERSION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestVersion:
    """Ensure version is bumped correctly for this release."""

    def test_version_is_0_11_0_in_pyproject(self):
        """pyproject.toml should declare version 0.11.0."""
        import pathlib
        import re

        pyproject = pathlib.Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject.read_text()
        match = re.search(r'^version\s*=\s*"(.+?)"', content, re.MULTILINE)

        assert match is not None, "version not found in pyproject.toml"
        assert match.group(1) == "0.11.0"

    def test_updater_version_matches_pyproject(self):
        """updater/__init__.py should declare the same version as pyproject.toml."""
        import pathlib
        import re

        updater_init = pathlib.Path(__file__).parent.parent / "updater" / "__init__.py"
        content = updater_init.read_text()
        match = re.search(r'^CURRENT_VERSION\s*=\s*"(.+?)"', content, re.MULTILINE)

        assert match is not None, "CURRENT_VERSION not found in updater/__init__.py"
        assert match.group(1) == "0.11.0"
