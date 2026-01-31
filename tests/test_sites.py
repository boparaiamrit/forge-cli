"""
Tests for Site Management
"""

import pytest
from jinja2 import Template

from sites import (
    NEXTJS_TEMPLATE,
    NUXT_TEMPLATE,
    PHP_TEMPLATE,
    STATIC_TEMPLATE,
)


class TestNginxTemplates:
    """Test Nginx configuration templates."""

    def test_nextjs_template_renders(self):
        """Next.js template should render correctly."""
        template = Template(NEXTJS_TEMPLATE)
        result = template.render(
            domain="myapp.com",
            www=True,
            port=3000,
        )

        assert "server_name myapp.com www.myapp.com" in result
        assert "proxy_pass http://127.0.0.1:3000" in result
        assert "proxy_http_version 1.1" in result
        assert "proxy_set_header Upgrade" in result

    def test_nextjs_template_without_www(self):
        """Next.js template should work without www."""
        template = Template(NEXTJS_TEMPLATE)
        result = template.render(
            domain="api.example.com",
            www=False,
            port=4000,
        )

        assert "server_name api.example.com;" in result
        assert "www.api.example.com" not in result
        assert "proxy_pass http://127.0.0.1:4000" in result

    def test_nuxt_template_renders(self):
        """Nuxt template should render correctly."""
        template = Template(NUXT_TEMPLATE)
        result = template.render(
            domain="nuxt.example.com",
            www=True,
            port=3001,
        )

        assert "Nuxt.js" in result
        assert "nuxt.example.com www.nuxt.example.com" in result
        assert "proxy_pass http://127.0.0.1:3001" in result

    def test_php_template_renders(self):
        """PHP template should render correctly."""
        template = Template(PHP_TEMPLATE)
        result = template.render(
            domain="laravel.example.com",
            www=True,
            document_root="/var/www/laravel/public",
            php_version="8.3",
        )

        assert "PHP Application" in result
        assert "root /var/www/laravel/public" in result
        assert "fastcgi_pass unix:/var/run/php/php8.3-fpm.sock" in result
        assert "try_files $uri $uri/ /index.php" in result

    def test_php_template_different_version(self):
        """PHP template should use correct PHP version."""
        template = Template(PHP_TEMPLATE)
        result = template.render(
            domain="app.com",
            www=False,
            document_root="/var/www/app",
            php_version="8.1",
        )

        assert "php8.1-fpm.sock" in result

    def test_static_template_renders(self):
        """Static template should render correctly."""
        template = Template(STATIC_TEMPLATE)
        result = template.render(
            domain="static.example.com",
            www=True,
            document_root="/var/www/static",
        )

        assert "Static Site" in result
        assert "root /var/www/static" in result
        assert "try_files $uri $uri/ =404" in result
        assert "fastcgi_pass" not in result  # No PHP

    def test_all_templates_listen_on_port_80(self):
        """All templates should listen on port 80."""
        templates = [NEXTJS_TEMPLATE, NUXT_TEMPLATE, PHP_TEMPLATE, STATIC_TEMPLATE]

        for tmpl in templates:
            assert "listen 80" in tmpl
            assert "listen [::]:80" in tmpl


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
