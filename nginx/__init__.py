"""
Nginx Module - Nginx configuration and management utilities
"""

from .templates import (
    render_template,
    get_template_types,
    NODEJS_TEMPLATE,
    PHP_TEMPLATE,
    STATIC_TEMPLATE,
    NODEJS_TEMPLATE_SSL,
    PHP_TEMPLATE_SSL,
    SECURITY_HEADERS,
    GZIP_CONFIG,
    SSL_CONFIG,
)

__all__ = [
    "render_template",
    "get_template_types",
    "NODEJS_TEMPLATE",
    "PHP_TEMPLATE",
    "STATIC_TEMPLATE",
    "NODEJS_TEMPLATE_SSL",
    "PHP_TEMPLATE_SSL",
    "SECURITY_HEADERS",
    "GZIP_CONFIG",
    "SSL_CONFIG",
]
