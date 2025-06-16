"""Unit tests for robust selector logic."""

import unittest
from unittest.mock import Mock, AsyncMock, patch

from flight_scraper.utils import RobustSelector, SelectorHealthMonitor, ROBUST_SELECTOR_CONFIGS
from flight_scraper.core.models import SelectorStrategy, SelectorFailureType


class TestRobustSelector(unittest.TestCase):
    """Test robust selector functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock()
        self.mock_page.query_selector = AsyncMock()
        self.mock_page.query_selector_all = AsyncMock()
        self.mock_page.evaluate = AsyncMock()
        
        self.selector = RobustSelector(
            element_type="test_element",
            page=self.mock_page
        )
    
    def test_robust_selector_initialization(self):
        """Test RobustSelector initialization."""
        self.assertEqual(self.selector.element_type, "test_element")
        self.assertEqual(self.selector.page, self.mock_page)
        self.assertIsNotNone(self.selector.monitoring)
    
    def test_find_element_method_exists(self):
        """Test that find_element method exists."""
        self.assertTrue(hasattr(self.selector, 'find_element'))
        self.assertTrue(callable(getattr(self.selector, 'find_element')))
    
    def test_monitoring_attributes(self):
        """Test monitoring attributes exist."""
        self.assertTrue(hasattr(self.selector.monitoring, 'element_type'))
        self.assertEqual(self.selector.monitoring.element_type, "test_element")
    
    def test_selector_health_monitor_initialization(self):
        """Test SelectorHealthMonitor initialization."""
        monitor = SelectorHealthMonitor()
        self.assertIsInstance(monitor, SelectorHealthMonitor)
        health_report = monitor.get_health_report()
        self.assertIsInstance(health_report, dict)
    
    def test_selector_strategies_enum(self):
        """Test SelectorStrategy enum values."""
        self.assertEqual(SelectorStrategy.SEMANTIC, "semantic")
        self.assertEqual(SelectorStrategy.STRUCTURAL, "structural")
        self.assertEqual(SelectorStrategy.CLASS_BASED, "class_based")
        self.assertEqual(SelectorStrategy.CONTENT_BASED, "content_based")
    
    def test_selector_failure_types_enum(self):
        """Test SelectorFailureType enum values."""
        self.assertEqual(SelectorFailureType.NOT_FOUND, "not_found")
        self.assertEqual(SelectorFailureType.UNINTERACTABLE, "uninteractable")
        self.assertEqual(SelectorFailureType.STRUCTURE_CHANGED, "structure_changed")
        self.assertEqual(SelectorFailureType.TIMING_ISSUE, "timing_issue")
        self.assertEqual(SelectorFailureType.STALE_ELEMENT, "stale_element")
        self.assertEqual(SelectorFailureType.PERMISSION_DENIED, "permission_denied")
    
    def test_robust_selector_configs_loaded(self):
        """Test that robust selector configurations are loaded."""
        self.assertIsInstance(ROBUST_SELECTOR_CONFIGS, dict)
        self.assertGreater(len(ROBUST_SELECTOR_CONFIGS), 0)
        
        # Check for specific configurations
        if "origin_input" in ROBUST_SELECTOR_CONFIGS:
            origin_config = ROBUST_SELECTOR_CONFIGS["origin_input"]
            self.assertIsInstance(origin_config, dict)
        
        if "search_button" in ROBUST_SELECTOR_CONFIGS:
            search_config = ROBUST_SELECTOR_CONFIGS["search_button"]
            self.assertIsInstance(search_config, dict)
    
    def test_internal_methods_exist(self):
        """Test that internal methods exist."""
        self.assertTrue(hasattr(self.selector, '_try_selector'))
        self.assertTrue(hasattr(self.selector, '_categorize_failure'))
        self.assertTrue(hasattr(self.selector, '_record_attempt'))


class TestSelectorHealthMonitor(unittest.TestCase):
    """Test selector health monitoring functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = SelectorHealthMonitor()
    
    def test_health_monitor_initialization(self):
        """Test health monitor initializes correctly."""
        self.assertIsInstance(self.monitor, SelectorHealthMonitor)
    
    def test_get_health_report_structure(self):
        """Test health report returns expected structure."""
        report = self.monitor.get_health_report()
        self.assertIsInstance(report, dict)
        
        # Check for expected keys (these may vary based on implementation)
        expected_keys = ['overall_health', 'critical_issues', 'recommendations']
        for key in expected_keys:
            if key in report:
                self.assertIsInstance(report[key], (dict, list))
    
    def test_record_page_health_method_exists(self):
        """Test that page health recording method exists."""
        # This tests the interface exists
        self.assertTrue(hasattr(self.monitor, 'record_page_health'))
        self.assertTrue(callable(getattr(self.monitor, 'record_page_health')))
    
    def test_failure_patterns_attribute(self):
        """Test that failure patterns attribute exists."""
        # This tests the interface exists
        self.assertTrue(hasattr(self.monitor, 'failure_patterns'))
        self.assertIsInstance(self.monitor.failure_patterns, dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)