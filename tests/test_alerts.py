"""
Tests for Monitoring & Alerts module
"""

import pytest
from pathlib import Path


class TestAlertsModule:
    """Tests for alerts and monitoring module."""

    def test_module_imports(self):
        """Test that the alerts module imports correctly."""
        from alerts import (
            run_alerts_menu,
            ALERTS_MENU_CHOICES,
            DEFAULT_THRESHOLDS,
            MONITOR_DATA_DIR,
        )
        assert callable(run_alerts_menu)
        assert len(ALERTS_MENU_CHOICES) > 0
        assert len(DEFAULT_THRESHOLDS) > 0
        assert isinstance(MONITOR_DATA_DIR, Path)

    def test_menu_structure(self):
        """Test that menu has expected options."""
        from alerts import ALERTS_MENU_CHOICES

        values = [c.get("value") for c in ALERTS_MENU_CHOICES if isinstance(c, dict)]

        # Verify key menu options exist
        assert "status" in values
        assert "history" in values
        assert "view_alerts" in values
        assert "alert_history" in values
        assert "thresholds" in values
        assert "setup_cron" in values
        assert "record" in values
        assert "back" in values

    def test_default_thresholds(self):
        """Test default thresholds are properly defined."""
        from alerts import DEFAULT_THRESHOLDS

        # CPU thresholds
        assert "cpu_warning" in DEFAULT_THRESHOLDS
        assert "cpu_critical" in DEFAULT_THRESHOLDS
        assert DEFAULT_THRESHOLDS["cpu_warning"] < DEFAULT_THRESHOLDS["cpu_critical"]

        # Memory thresholds
        assert "memory_warning" in DEFAULT_THRESHOLDS
        assert "memory_critical" in DEFAULT_THRESHOLDS
        assert DEFAULT_THRESHOLDS["memory_warning"] < DEFAULT_THRESHOLDS["memory_critical"]

        # Disk thresholds
        assert "disk_warning" in DEFAULT_THRESHOLDS
        assert "disk_critical" in DEFAULT_THRESHOLDS
        assert DEFAULT_THRESHOLDS["disk_warning"] < DEFAULT_THRESHOLDS["disk_critical"]

        # Swap thresholds
        assert "swap_warning" in DEFAULT_THRESHOLDS
        assert "swap_critical" in DEFAULT_THRESHOLDS

    def test_data_paths(self):
        """Test that data paths are defined."""
        from alerts import MONITOR_DATA_DIR, ALERTS_FILE, HISTORY_FILE, THRESHOLDS_FILE

        assert isinstance(MONITOR_DATA_DIR, Path)
        assert isinstance(ALERTS_FILE, Path)
        assert isinstance(HISTORY_FILE, Path)
        assert isinstance(THRESHOLDS_FILE, Path)

        assert ".forge" in str(MONITOR_DATA_DIR)
        assert "monitoring" in str(MONITOR_DATA_DIR)


class TestMetricsFunctions:
    """Tests for metrics collection functions."""

    def test_get_cpu_usage_exists(self):
        """Test CPU usage function exists."""
        from alerts import get_cpu_usage
        assert callable(get_cpu_usage)

    def test_get_memory_usage_exists(self):
        """Test memory usage function exists."""
        from alerts import get_memory_usage
        assert callable(get_memory_usage)

    def test_get_disk_usage_exists(self):
        """Test disk usage function exists."""
        from alerts import get_disk_usage
        assert callable(get_disk_usage)

    def test_get_load_average_exists(self):
        """Test load average function exists."""
        from alerts import get_load_average
        assert callable(get_load_average)

    def test_get_swap_usage_exists(self):
        """Test swap usage function exists."""
        from alerts import get_swap_usage
        assert callable(get_swap_usage)

    def test_collect_all_metrics_exists(self):
        """Test collect all metrics function exists."""
        from alerts import collect_all_metrics
        assert callable(collect_all_metrics)


class TestAlertsFunctions:
    """Tests for alerts management functions."""

    def test_load_alerts_exists(self):
        """Test load alerts function exists."""
        from alerts import load_alerts
        assert callable(load_alerts)

    def test_save_alerts_exists(self):
        """Test save alerts function exists."""
        from alerts import save_alerts
        assert callable(save_alerts)

    def test_add_alert_exists(self):
        """Test add alert function exists."""
        from alerts import add_alert
        assert callable(add_alert)

    def test_load_thresholds_exists(self):
        """Test load thresholds function exists."""
        from alerts import load_thresholds
        assert callable(load_thresholds)

    def test_save_thresholds_exists(self):
        """Test save thresholds function exists."""
        from alerts import save_thresholds
        assert callable(save_thresholds)


class TestHistoryFunctions:
    """Tests for history management functions."""

    def test_load_history_exists(self):
        """Test load history function exists."""
        from alerts import load_history
        assert callable(load_history)

    def test_save_history_entry_exists(self):
        """Test save history entry function exists."""
        from alerts import save_history_entry
        assert callable(save_history_entry)


class TestDisplayFunctions:
    """Tests for display functions."""

    def test_show_current_status_exists(self):
        """Test show current status function exists."""
        from alerts import show_current_status
        assert callable(show_current_status)

    def test_show_usage_history_exists(self):
        """Test show usage history function exists."""
        from alerts import show_usage_history
        assert callable(show_usage_history)

    def test_view_active_alerts_exists(self):
        """Test view active alerts function exists."""
        from alerts import view_active_alerts
        assert callable(view_active_alerts)

    def test_view_alert_history_exists(self):
        """Test view alert history function exists."""
        from alerts import view_alert_history
        assert callable(view_alert_history)

    def test_configure_thresholds_exists(self):
        """Test configure thresholds function exists."""
        from alerts import configure_thresholds
        assert callable(configure_thresholds)

    def test_format_bytes_exists(self):
        """Test format bytes function exists."""
        from alerts import format_bytes
        assert callable(format_bytes)

    def test_get_status_icon_exists(self):
        """Test get status icon function exists."""
        from alerts import get_status_icon
        assert callable(get_status_icon)


class TestFormatBytes:
    """Tests for format_bytes utility."""

    def test_format_bytes_kb(self):
        """Test formatting bytes to KB."""
        from alerts import format_bytes
        result = format_bytes(1024)
        assert "KB" in result or "B" in result

    def test_format_bytes_mb(self):
        """Test formatting bytes to MB."""
        from alerts import format_bytes
        result = format_bytes(1048576)
        assert "MB" in result or "KB" in result

    def test_format_bytes_gb(self):
        """Test formatting bytes to GB."""
        from alerts import format_bytes
        result = format_bytes(1073741824)
        assert "GB" in result or "MB" in result


class TestStatusIcons:
    """Tests for status icon generation."""

    def test_status_ok(self):
        """Test OK status icon."""
        from alerts import get_status_icon
        result = get_status_icon(50, 70, 90)
        assert "OK" in result or "green" in result.lower()

    def test_status_warning(self):
        """Test warning status icon."""
        from alerts import get_status_icon
        result = get_status_icon(75, 70, 90)
        assert "WARNING" in result or "yellow" in result.lower()

    def test_status_critical(self):
        """Test critical status icon."""
        from alerts import get_status_icon
        result = get_status_icon(95, 70, 90)
        assert "CRITICAL" in result or "red" in result.lower()
