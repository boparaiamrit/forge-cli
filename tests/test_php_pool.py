"""
Tests for PHP FPM Pool Configuration
"""

import pytest


class TestPHPPoolConfiguration:
    """Tests for PHP-FPM pool configuration functions."""

    def test_get_server_specs_exists(self):
        """Test get_server_specs function exists."""
        from php import get_server_specs
        assert callable(get_server_specs)

    def test_calculate_fpm_pool_settings_exists(self):
        """Test calculate_fpm_pool_settings function exists."""
        from php import calculate_fpm_pool_settings
        assert callable(calculate_fpm_pool_settings)

    def test_configure_smart_pool_exists(self):
        """Test configure_smart_pool function exists."""
        from php import configure_smart_pool
        assert callable(configure_smart_pool)

    def test_configure_custom_pool_exists(self):
        """Test configure_custom_pool function exists."""
        from php import configure_custom_pool
        assert callable(configure_custom_pool)

    def test_read_pool_setting_exists(self):
        """Test read_pool_setting function exists."""
        from php import read_pool_setting
        assert callable(read_pool_setting)

    def test_apply_pool_settings_exists(self):
        """Test apply_pool_settings function exists."""
        from php import apply_pool_settings
        assert callable(apply_pool_settings)


class TestPoolCalculations:
    """Tests for pool calculation logic."""

    def test_small_server_ondemand(self):
        """Test that small servers get ondemand pm."""
        from php import calculate_fpm_pool_settings

        # Simulate 1GB RAM server
        specs = {
            "ram_total": 1 * 1024 * 1024 * 1024,  # 1GB
            "ram_available": 512 * 1024 * 1024,
            "swap_total": 0,
            "swap_available": 0,
            "cpu_count": 1,
        }

        result = calculate_fpm_pool_settings(specs, 50)

        assert result["pm"] == "ondemand"
        assert result["server_size"] == "small"
        assert result["pm.max_children"] >= 2

    def test_medium_server_dynamic(self):
        """Test that medium servers get dynamic pm."""
        from php import calculate_fpm_pool_settings

        # Simulate 4GB RAM server
        specs = {
            "ram_total": 4 * 1024 * 1024 * 1024,  # 4GB
            "ram_available": 2 * 1024 * 1024 * 1024,
            "swap_total": 2 * 1024 * 1024 * 1024,
            "swap_available": 2 * 1024 * 1024 * 1024,
            "cpu_count": 2,
        }

        result = calculate_fpm_pool_settings(specs, 50)

        assert result["pm"] == "dynamic"
        assert result["server_size"] == "medium"
        assert result["pm.max_children"] > 10

    def test_large_server_dynamic(self):
        """Test that large servers get dynamic pm with more children."""
        from php import calculate_fpm_pool_settings

        # Simulate 8GB RAM server
        specs = {
            "ram_total": 8 * 1024 * 1024 * 1024,  # 8GB
            "ram_available": 6 * 1024 * 1024 * 1024,
            "swap_total": 4 * 1024 * 1024 * 1024,
            "swap_available": 4 * 1024 * 1024 * 1024,
            "cpu_count": 4,
        }

        result = calculate_fpm_pool_settings(specs, 50)

        assert result["pm"] == "dynamic"
        assert result["server_size"] == "large"
        assert result["pm.max_children"] > 50

    def test_enterprise_server(self):
        """Test that enterprise servers get correct settings."""
        from php import calculate_fpm_pool_settings

        # Simulate 32GB RAM server
        specs = {
            "ram_total": 32 * 1024 * 1024 * 1024,  # 32GB
            "ram_available": 24 * 1024 * 1024 * 1024,
            "swap_total": 16 * 1024 * 1024 * 1024,
            "swap_available": 16 * 1024 * 1024 * 1024,
            "cpu_count": 8,
        }

        result = calculate_fpm_pool_settings(specs, 50)

        assert result["pm"] == "dynamic"
        assert result["server_size"] == "enterprise"
        assert result["pm.max_children"] > 100

    def test_swap_increases_max_children(self):
        """Test that swap adds to available PHP memory."""
        from php import calculate_fpm_pool_settings

        # Without swap
        specs_no_swap = {
            "ram_total": 4 * 1024 * 1024 * 1024,  # 4GB
            "ram_available": 2 * 1024 * 1024 * 1024,
            "swap_total": 0,
            "swap_available": 0,
            "cpu_count": 2,
        }

        # With swap
        specs_with_swap = {
            "ram_total": 4 * 1024 * 1024 * 1024,  # 4GB
            "ram_available": 2 * 1024 * 1024 * 1024,
            "swap_total": 4 * 1024 * 1024 * 1024,  # 4GB swap
            "swap_available": 4 * 1024 * 1024 * 1024,
            "cpu_count": 2,
        }

        result_no_swap = calculate_fpm_pool_settings(specs_no_swap, 50)
        result_with_swap = calculate_fpm_pool_settings(specs_with_swap, 50)

        # Swap should increase available children
        assert result_with_swap["pm.max_children"] > result_no_swap["pm.max_children"]

    def test_higher_process_memory_reduces_children(self):
        """Test that higher avg process memory reduces max children."""
        from php import calculate_fpm_pool_settings

        specs = {
            "ram_total": 4 * 1024 * 1024 * 1024,  # 4GB
            "ram_available": 2 * 1024 * 1024 * 1024,
            "swap_total": 0,
            "swap_available": 0,
            "cpu_count": 2,
        }

        result_50mb = calculate_fpm_pool_settings(specs, 50)
        result_100mb = calculate_fpm_pool_settings(specs, 100)

        # Higher process memory should result in fewer children
        assert result_100mb["pm.max_children"] < result_50mb["pm.max_children"]

    def test_max_children_capped(self):
        """Test that max_children is capped at 500."""
        from php import calculate_fpm_pool_settings

        # Huge server
        specs = {
            "ram_total": 128 * 1024 * 1024 * 1024,  # 128GB
            "ram_available": 100 * 1024 * 1024 * 1024,
            "swap_total": 64 * 1024 * 1024 * 1024,
            "swap_available": 64 * 1024 * 1024 * 1024,
            "cpu_count": 32,
        }

        result = calculate_fpm_pool_settings(specs, 30)  # Low process memory

        assert result["pm.max_children"] <= 500

    def test_min_children_at_least_2(self):
        """Test that max_children is at least 2."""
        from php import calculate_fpm_pool_settings

        # Tiny server
        specs = {
            "ram_total": 256 * 1024 * 1024,  # 256MB
            "ram_available": 128 * 1024 * 1024,
            "swap_total": 0,
            "swap_available": 0,
            "cpu_count": 1,
        }

        result = calculate_fpm_pool_settings(specs, 150)  # High process memory

        assert result["pm.max_children"] >= 2

    def test_settings_include_all_required_keys(self):
        """Test that calculated settings include all required keys."""
        from php import calculate_fpm_pool_settings

        specs = {
            "ram_total": 4 * 1024 * 1024 * 1024,
            "ram_available": 2 * 1024 * 1024 * 1024,
            "swap_total": 2 * 1024 * 1024 * 1024,
            "swap_available": 2 * 1024 * 1024 * 1024,
            "cpu_count": 2,
        }

        result = calculate_fpm_pool_settings(specs, 50)

        required_keys = [
            "pm",
            "pm.max_children",
            "pm.start_servers",
            "pm.min_spare_servers",
            "pm.max_spare_servers",
            "pm.max_requests",
            "server_size",
            "ram_mb",
            "swap_mb",
            "cpu_count",
            "available_for_php_mb",
            "avg_process_mb",
        ]

        for key in required_keys:
            assert key in result, f"Missing key: {key}"
