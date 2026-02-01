"""
Tests for Disk Management module
"""

import pytest
from pathlib import Path


class TestDiskModule:
    """Tests for disk management module."""

    def test_module_imports(self):
        """Test that the disk module imports correctly."""
        from disk import (
            run_disk_menu,
            DISK_MENU_CHOICES,
            CLEANABLE_DIRS,
            LOG_DIRS,
        )
        assert callable(run_disk_menu)
        assert len(DISK_MENU_CHOICES) > 0
        assert len(CLEANABLE_DIRS) > 0
        assert len(LOG_DIRS) > 0

    def test_menu_structure(self):
        """Test that menu has expected options."""
        from disk import DISK_MENU_CHOICES

        values = [c.get("value") for c in DISK_MENU_CHOICES if isinstance(c, dict)]

        # Verify key menu options exist
        assert "overview" in values
        assert "analyze" in values
        assert "quick_cleanup" in values
        assert "deep_cleanup" in values
        assert "log_rotation" in values
        assert "swap" in values
        assert "find_large" in values
        assert "back" in values

    def test_data_directory(self):
        """Test that data directory constant is defined."""
        from disk import DISK_DATA_DIR

        assert isinstance(DISK_DATA_DIR, Path)
        assert ".forge" in str(DISK_DATA_DIR)
        assert "disk" in str(DISK_DATA_DIR)

    def test_cleanable_directories(self):
        """Test cleanable directories configuration."""
        from disk import CLEANABLE_DIRS

        for path, config in CLEANABLE_DIRS.items():
            assert "name" in config
            assert "pattern" in config
            assert "min_age_days" in config
            assert isinstance(config["min_age_days"], int)

    def test_log_directories(self):
        """Test log directories list."""
        from disk import LOG_DIRS

        assert "/var/log/nginx" in LOG_DIRS
        # Should contain various log paths
        assert any("fpm" in log for log in LOG_DIRS)


class TestDiskFunctions:
    """Tests for disk management functions."""

    def test_show_disk_overview_exists(self):
        """Test disk overview function exists."""
        from disk import show_disk_overview
        assert callable(show_disk_overview)

    def test_analyze_directory_sizes_exists(self):
        """Test analyze function exists."""
        from disk import analyze_directory_sizes
        assert callable(analyze_directory_sizes)

    def test_quick_cleanup_exists(self):
        """Test quick cleanup function exists."""
        from disk import quick_cleanup
        assert callable(quick_cleanup)

    def test_deep_cleanup_exists(self):
        """Test deep cleanup function exists."""
        from disk import deep_cleanup
        assert callable(deep_cleanup)

    def test_manage_swap_exists(self):
        """Test swap management function exists."""
        from disk import manage_swap
        assert callable(manage_swap)

    def test_find_large_files_exists(self):
        """Test find large files function exists."""
        from disk import find_large_files
        assert callable(find_large_files)

    def test_find_old_files_exists(self):
        """Test find old files function exists."""
        from disk import find_old_files
        assert callable(find_old_files)

    def test_show_log_rotation_status_exists(self):
        """Test log rotation status function exists."""
        from disk import show_log_rotation_status
        assert callable(show_log_rotation_status)

    def test_rotate_logs_now_exists(self):
        """Test rotate logs now function exists."""
        from disk import rotate_logs_now
        assert callable(rotate_logs_now)

    def test_setup_cleanup_cron_exists(self):
        """Test cleanup cron setup function exists."""
        from disk import setup_cleanup_cron
        assert callable(setup_cleanup_cron)


class TestSwapManagement:
    """Tests for swap management functions."""

    def test_create_swap_file_exists(self):
        """Test create swap file function exists."""
        from disk import create_swap_file
        assert callable(create_swap_file)

    def test_adjust_swappiness_exists(self):
        """Test adjust swappiness function exists."""
        from disk import adjust_swappiness
        assert callable(adjust_swappiness)

    def test_remove_swap_exists(self):
        """Test remove swap function exists."""
        from disk import remove_swap
        assert callable(remove_swap)
