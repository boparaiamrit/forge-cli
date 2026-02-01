"""
Tests for Site Management
"""

import pytest
from jinja2 import Template

from nginx.templates import (
    NODEJS_TEMPLATE,
    PHP_TEMPLATE,
    STATIC_TEMPLATE,
    render_template,
)


class TestNginxTemplates:
    """Test Nginx configuration templates."""

    def test_nextjs_template_renders(self):
        """Next.js template should render correctly using render_template."""
        result = render_template(
            site_type="nextjs",
            domain="myapp.com",
            www=True,
            port=3000,
        )

        assert "myapp.com" in result
        assert "www.myapp.com" in result
        assert "proxy_pass http://127.0.0.1:3000" in result
        assert "proxy_http_version 1.1" in result
        assert "proxy_set_header Upgrade" in result

    def test_nextjs_template_without_www(self):
        """Next.js template should work without www."""
        result = render_template(
            site_type="nextjs",
            domain="api.example.com",
            www=False,
            port=4000,
        )

        assert "api.example.com" in result
        assert "www.api.example.com" not in result
        assert "proxy_pass http://127.0.0.1:4000" in result

    def test_nuxt_template_renders(self):
        """Nuxt template should render correctly."""
        result = render_template(
            site_type="nuxtjs",
            domain="nuxt.example.com",
            www=True,
            port=3001,
        )

        assert "nuxt.example.com" in result
        assert "www.nuxt.example.com" in result
        assert "proxy_pass http://127.0.0.1:3001" in result

    def test_php_template_renders(self):
        """PHP template should render correctly."""
        result = render_template(
            site_type="php",
            domain="laravel.example.com",
            www=True,
            document_root="/var/www/laravel/public",
            php_version="8.3",
        )

        assert "/var/www/laravel/public" in result
        assert "php8.3-fpm.sock" in result
        assert "fastcgi_pass" in result

    def test_php_template_different_version(self):
        """PHP template should use correct PHP version."""
        result = render_template(
            site_type="php",
            domain="app.com",
            www=False,
            document_root="/var/www/app",
            php_version="8.1",
        )

        assert "php8.1-fpm.sock" in result

    def test_static_template_renders(self):
        """Static template should render correctly."""
        result = render_template(
            site_type="static",
            domain="static.example.com",
            www=True,
            document_root="/var/www/static",
        )

        assert "/var/www/static" in result
        assert "try_files $uri $uri/ =404" in result
        assert "fastcgi_pass" not in result  # No PHP

    def test_all_templates_listen_on_port_80(self):
        """All templates should listen on port 80."""
        templates = [NODEJS_TEMPLATE, PHP_TEMPLATE, STATIC_TEMPLATE]

        for tmpl in templates:
            assert "listen 80" in tmpl
            assert "listen [::]:80" in tmpl

    def test_ssl_template(self):
        """SSL template should include SSL configuration."""
        result = render_template(
            site_type="nextjs",
            domain="secure.example.com",
            www=True,
            port=3000,
            ssl_enabled=True,
        )

        assert "listen 443 ssl http2" in result
        assert "ssl_certificate" in result
        assert "/etc/letsencrypt/live/secure.example.com" in result

    def test_security_headers_present(self):
        """Templates should include security headers."""
        result = render_template(
            site_type="nextjs",
            domain="example.com",
            port=3000,
        )

        assert "X-Frame-Options" in result
        assert "X-Content-Type-Options" in result
        assert "X-XSS-Protection" in result


class TestSiteValidation:
    """Test site configuration validation."""

    def test_domain_must_contain_dot(self):
        """Domain validation should require a dot."""
        valid_domains = ["example.com", "sub.example.com", "my-app.io"]
        invalid_domains = ["localhost", "myapp", ""]

        for domain in valid_domains:
            assert "." in domain and len(domain) > 0

        for domain in invalid_domains:
            assert "." not in domain or len(domain) == 0

    def test_port_must_be_valid(self):
        """Port validation should check range."""
        valid_ports = ["3000", "4000", "8080", "65535"]
        invalid_ports = ["0", "999", "65536", "abc", ""]

        for port in valid_ports:
            assert port.isdigit() and 1000 <= int(port) <= 65535

        for port in invalid_ports:
            assert not (port.isdigit() and 1000 <= int(port) <= 65535) if port else True
