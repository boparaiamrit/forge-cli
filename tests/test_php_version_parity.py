"""Regression tests for shared PHP version support."""

from provisioning.config import PHP_VERSIONS as PROVISIONING_PHP_VERSIONS


def test_provisioning_supports_php_84_and_85():
    """Provisioning config should include the newer supported PHP versions."""
    assert "8.5" in PROVISIONING_PHP_VERSIONS
    assert "8.4" in PROVISIONING_PHP_VERSIONS


def test_site_php_choices_include_newer_versions():
    """Site creation choices should expose PHP 8.4 and 8.5."""
    from sites import get_php_version_choices

    assert get_php_version_choices()[:3] == ["8.5", "8.4", "8.3"]
