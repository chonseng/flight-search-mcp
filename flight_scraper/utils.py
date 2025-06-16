"""Utility functions for the flight scraper."""

import asyncio
import random
import re
import time
from datetime import datetime, date
from typing import Optional, Tuple, Any, List, Dict, Union
from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, ElementHandle

from .core.config import SCRAPER_CONFIG
from .core.models import (
    ScrapingError, TimeoutError, ElementNotFoundError,
    SelectorAttempt, SelectorMonitoring, SelectorStrategy, SelectorFailureType,
    PageSelectorHealth, SelectorFailureAlert
)


async def random_delay(min_delay: Optional[float] = None, max_delay: Optional[float] = None) -> None:
    """Add random delay to simulate human behavior."""
    if min_delay is None or max_delay is None:
        min_delay, max_delay = SCRAPER_CONFIG["delay_range"]
    
    delay = random.uniform(min_delay, max_delay)
    logger.debug(f"Adding random delay of {delay:.2f} seconds")
    await asyncio.sleep(delay)


async def wait_for_element(page: Page, selector: str, timeout: int = 10000) -> bool:
    """Wait for an element to appear on the page."""
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        logger.warning(f"Element not found within timeout: {selector}")
        return False


async def safe_click(page: Page, selector: str, timeout: int = 10000) -> bool:
    """Safely click an element with error handling."""
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        await page.click(selector)
        await random_delay(0.5, 1.5)
        return True
    except PlaywrightTimeoutError:
        logger.error(f"Could not click element: {selector}")
        return False
    except Exception as e:
        logger.error(f"Error clicking element {selector}: {str(e)}")
        return False


async def safe_fill(page: Page, selector: str, value: str, timeout: int = 10000) -> bool:
    """Safely fill an input field with error handling."""
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        await page.fill(selector, value)
        await random_delay(0.5, 1.0)
        return True
    except PlaywrightTimeoutError:
        logger.error(f"Could not fill element: {selector}")
        return False
    except Exception as e:
        logger.error(f"Error filling element {selector}: {str(e)}")
        return False


async def safe_get_text(page: Page, selector: str, timeout: int = 5000) -> Optional[str]:
    """Safely get text from an element."""
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        element = await page.query_selector(selector)
        if element:
            text = await element.inner_text()
            return text.strip() if text else None
        return None
    except PlaywrightTimeoutError:
        logger.debug(f"Element not found for text extraction: {selector}")
        return None
    except Exception as e:
        logger.error(f"Error getting text from {selector}: {str(e)}")
        return None


def format_date_for_input(date_obj: date) -> str:
    """Format date for Google Flights input field."""
    return date_obj.strftime("%Y-%m-%d")


def parse_duration(duration_str: str) -> str:
    """Parse and normalize duration string."""
    if not duration_str:
        return "Unknown"
    
    # Clean up the duration string
    duration = re.sub(r'[^\d\w\s]', '', duration_str).strip()
    return duration if duration else "Unknown"


def parse_price(price_str: str) -> str:
    """Parse and normalize price string."""
    if not price_str:
        return "0"
    
    # Extract price using regex
    price_match = re.search(r'[\$£€¥]?[\d,]+', price_str)
    return price_match.group() if price_match else price_str.strip()


def parse_stops(stops_str: str) -> int:
    """Parse number of stops from string."""
    if not stops_str:
        return 0
    
    # Look for numbers in the stops string
    if "nonstop" in stops_str.lower() or "direct" in stops_str.lower():
        return 0
    
    stop_match = re.search(r'(\d+)', stops_str)
    return int(stop_match.group(1)) if stop_match else 1


async def retry_async_operation(
    operation,
    max_attempts: int = 3,
    delay: float = 1.0,
    exponential_backoff: bool = True
) -> Any:
    """Retry an async operation with exponential backoff."""
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_attempts}")
            return await operation()
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < max_attempts - 1:
                wait_time = delay * (2 ** attempt) if exponential_backoff else delay
                logger.debug(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
    
    raise last_exception


def setup_logging() -> None:
    """Configure logging for the application."""
    from .core.config import LOG_CONFIG
    
    logger.remove()  # Remove default handler
    logger.add(
        LOG_CONFIG["file"],
        level=LOG_CONFIG["level"],
        format=LOG_CONFIG["format"],
        rotation=LOG_CONFIG["rotation"],
        retention=LOG_CONFIG["retention"],
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level=LOG_CONFIG["level"],
        format=LOG_CONFIG["format"],
        colorize=True,
    )


def validate_airport_code(code: str) -> bool:
    """Validate airport code format."""
    return bool(re.match(r'^[A-Z]{3}$', code.upper())) if code else False


def normalize_airport_code(code: str) -> str:
    """Normalize airport code to uppercase 3-letter format."""
    if not code:
        return ""
    return code.upper().strip()[:3]
class RobustSelector:
    """Robust selector with intelligent fallback hierarchy."""
    
    def __init__(self, element_type: str, page: Page):
        self.element_type = element_type
        self.page = page
        self.monitoring = SelectorMonitoring(element_type=element_type)
        
    async def find_element(self, selector_config: Dict[str, List[str]], timeout: int = 10000) -> Optional[ElementHandle]:
        """
        Find element using hierarchical selector strategy.
        
        Args:
            selector_config: Dictionary with strategy -> list of selectors
            timeout: Maximum time to wait for element
            
        Returns:
            ElementHandle if found, None otherwise
        """
        start_time = time.time()
        
        # Define strategy order (most robust first)
        strategy_order = [
            SelectorStrategy.SEMANTIC,
            SelectorStrategy.STRUCTURAL, 
            SelectorStrategy.CLASS_BASED,
            SelectorStrategy.CONTENT_BASED
        ]
        
        for strategy in strategy_order:
            if strategy.value not in selector_config:
                continue
                
            selectors = selector_config[strategy.value]
            for selector in selectors:
                attempt_start = time.time()
                
                try:
                    # Attempt to find element
                    element = await self._try_selector(selector, timeout // len(selectors))
                    
                    if element:
                        # Success - record attempt and return
                        attempt_time = time.time() - attempt_start
                        self._record_attempt(selector, strategy, True, None, None, attempt_time)
                        self.monitoring.successful_selector = selector
                        self.monitoring.successful_strategy = strategy
                        self.monitoring.final_success = True
                        
                        logger.info(f"✅ Found {self.element_type} using {strategy.value} strategy: {selector}")
                        return element
                        
                except Exception as e:
                    # Failure - record attempt and continue
                    attempt_time = time.time() - attempt_start
                    failure_type = self._categorize_failure(e)
                    dom_context = await self._get_dom_context(selector)
                    
                    self._record_attempt(selector, strategy, False, failure_type, str(e), attempt_time, dom_context)
                    logger.debug(f"❌ Failed {self.element_type} with {strategy.value}: {selector} - {str(e)}")
        
        # All strategies failed
        self.monitoring.final_success = False
        total_time = time.time() - start_time
        self.monitoring.total_time = total_time
        
        logger.error(f"🚨 All selector strategies failed for {self.element_type} (took {total_time:.2f}s)")
        return None
    
    async def _try_selector(self, selector: str, timeout: int) -> Optional[ElementHandle]:
        """Try a single selector with proper error handling."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            element = await self.page.query_selector(selector)
            
            if element:
                # Verify element is interactable
                is_visible = await element.is_visible()
                is_enabled = await element.is_enabled()
                
                if is_visible and is_enabled:
                    return element
                else:
                    raise Exception(f"Element found but not interactable (visible: {is_visible}, enabled: {is_enabled})")
                    
        except PlaywrightTimeoutError:
            raise Exception("Element not found within timeout")
        except Exception as e:
            raise e
            
        return None
    
    def _categorize_failure(self, error: Exception) -> SelectorFailureType:
        """Categorize the type of selector failure."""
        error_str = str(error).lower()
        
        if "timeout" in error_str or "not found" in error_str:
            return SelectorFailureType.NOT_FOUND
        elif "not interactable" in error_str or "not visible" in error_str or "not enabled" in error_str:
            return SelectorFailureType.UNINTERACTABLE
        elif "stale" in error_str or "detached" in error_str:
            return SelectorFailureType.STALE_ELEMENT
        elif "permission" in error_str or "denied" in error_str:
            return SelectorFailureType.PERMISSION_DENIED
        else:
            return SelectorFailureType.STRUCTURE_CHANGED
    
    async def _get_dom_context(self, selector: str) -> Optional[str]:
        """Get DOM context around failed selector for debugging."""
        try:
            # Try to get some context about the page structure
            context = await self.page.evaluate(f'''
            () => {{
                const element = document.querySelector("{selector}");
                if (element) {{
                    return element.outerHTML.substring(0, 200);
                }}
                
                // If direct selector fails, try to find similar elements
                const parts = "{selector}".split(" ");
                if (parts.length > 1) {{
                    const parentSelector = parts.slice(0, -1).join(" ");
                    const parent = document.querySelector(parentSelector);
                    if (parent) {{
                        return "Parent found: " + parent.outerHTML.substring(0, 200);
                    }}
                }}
                
                return "No matching elements found";
            }}
            ''')
            return str(context)
        except:
            return None
    
    def _record_attempt(self, selector: str, strategy: SelectorStrategy, success: bool, 
                       failure_type: Optional[SelectorFailureType], error_message: Optional[str], 
                       execution_time: float, dom_context: Optional[str] = None):
        """Record a selector attempt for monitoring."""
        attempt = SelectorAttempt(
            selector=selector,
            strategy=strategy,
            success=success,
            failure_type=failure_type,
            error_message=error_message,
            dom_context=dom_context,
            execution_time=execution_time
        )
        
        self.monitoring.attempts.append(attempt)
        self.monitoring.total_attempts += 1
        self.monitoring.total_time += execution_time


class SelectorHealthMonitor:
    """Monitor and analyze selector health across scraping sessions."""
    
    def __init__(self):
        self.page_health: Dict[str, PageSelectorHealth] = {}
        self.failure_patterns: Dict[str, List[SelectorFailureAlert]] = {}
    
    def record_page_health(self, page_type: str, selector_monitors: Dict[str, SelectorMonitoring]):
        """Record health data for a page."""
        health = PageSelectorHealth(
            page_type=page_type,
            selector_monitoring=selector_monitors
        )
        
        # Calculate overall success rate
        total_selectors = len(selector_monitors)
        successful_selectors = sum(1 for m in selector_monitors.values() if m.final_success)
        health.overall_success_rate = successful_selectors / total_selectors if total_selectors > 0 else 0.0
        
        # Identify critical failures
        for element_type, monitor in selector_monitors.items():
            if not monitor.final_success:
                health.critical_failures.append(element_type)
        
        # Detect structure changes
        health.page_structure_changed = self._detect_structure_changes(selector_monitors)
        
        self.page_health[page_type] = health
        
        # Generate alerts if needed
        self._generate_alerts(page_type, health)
    
    def _detect_structure_changes(self, monitors: Dict[str, SelectorMonitoring]) -> bool:
        """Detect if page structure has significantly changed."""
        structure_change_indicators = 0
        total_monitors = len(monitors)
        
        for monitor in monitors.values():
            # Look for patterns indicating structure changes
            failure_types = [attempt.failure_type for attempt in monitor.attempts if not attempt.success]
            
            if SelectorFailureType.STRUCTURE_CHANGED in failure_types:
                structure_change_indicators += 1
            
            # If all strategies failed, likely a structure change
            if not monitor.final_success and monitor.total_attempts >= 3:
                structure_change_indicators += 1
        
        # Consider structure changed if >50% of monitors show indicators
        return structure_change_indicators > (total_monitors * 0.5)
    
    def _generate_alerts(self, page_type: str, health: PageSelectorHealth):
        """Generate alerts for significant selector issues."""
        alerts = []
        
        # Critical alert: Overall success rate below 50%
        if health.overall_success_rate < 0.5:
            alert = SelectorFailureAlert(
                alert_id=f"{page_type}_critical_failure_{int(time.time())}",
                severity="critical",
                element_type="multiple",
                failure_patterns=[f"Overall success rate: {health.overall_success_rate:.1%}"],
                recommended_actions=[
                    "Review page structure changes",
                    "Update selector configurations",
                    "Check for Google Flights UI updates"
                ],
                failure_count=len(health.critical_failures),
                first_failure=health.scraping_timestamp,
                last_failure=health.scraping_timestamp,
                dom_changes_detected=health.page_structure_changed
            )
            alerts.append(alert)
        
        # Warning alerts for individual element failures
        for element_type in health.critical_failures:
            monitor = health.selector_monitoring[element_type]
            
            alert = SelectorFailureAlert(
                alert_id=f"{element_type}_failure_{int(time.time())}",
                severity="warning",
                element_type=element_type,
                failure_patterns=[attempt.error_message for attempt in monitor.attempts if attempt.error_message],
                recommended_actions=[
                    f"Review {element_type} selector configuration",
                    f"Test {element_type} selectors manually",
                    f"Add more fallback selectors for {element_type}"
                ],
                failure_count=monitor.total_attempts,
                first_failure=monitor.attempts[0].attempted_at if monitor.attempts else health.scraping_timestamp,
                last_failure=monitor.attempts[-1].attempted_at if monitor.attempts else health.scraping_timestamp,
                dom_changes_detected=any(attempt.failure_type == SelectorFailureType.STRUCTURE_CHANGED 
                                       for attempt in monitor.attempts)
            )
            alerts.append(alert)
        
        # Store alerts
        if page_type not in self.failure_patterns:
            self.failure_patterns[page_type] = []
        self.failure_patterns[page_type].extend(alerts)
        
        # Log alerts
        for alert in alerts:
            if alert.severity == "critical":
                logger.error(f"🚨 CRITICAL SELECTOR ALERT: {alert.element_type} - {alert.failure_patterns}")
            else:
                logger.warning(f"⚠️ SELECTOR WARNING: {alert.element_type} - {alert.failure_patterns}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        report = {
            "timestamp": datetime.now(),
            "pages_monitored": len(self.page_health),
            "overall_health": {},
            "critical_issues": [],
            "recommendations": []
        }
        
        # Calculate overall health metrics
        all_success_rates = [health.overall_success_rate for health in self.page_health.values()]
        if all_success_rates:
            report["overall_health"]["average_success_rate"] = sum(all_success_rates) / len(all_success_rates)
            report["overall_health"]["worst_success_rate"] = min(all_success_rates)
            report["overall_health"]["best_success_rate"] = max(all_success_rates)
        
        # Identify critical issues
        for page_type, health in self.page_health.items():
            if health.page_structure_changed:
                report["critical_issues"].append(f"Structure changes detected on {page_type}")
            
            if health.overall_success_rate < 0.3:
                report["critical_issues"].append(f"Very low success rate on {page_type}: {health.overall_success_rate:.1%}")
        
        # Generate recommendations
        if report["overall_health"].get("average_success_rate", 1.0) < 0.7:
            report["recommendations"].append("Consider updating selector configurations")
            report["recommendations"].append("Review recent Google Flights changes")
            
        return report


# Enhanced selector configurations for different elements
ROBUST_SELECTOR_CONFIGS = {
    "origin_input": {
        "semantic": [
            'input[aria-label*="Where from"]',
            'input[aria-label*="Origin"]',
            'input[placeholder*="Where from"]',
            'input[data-testid*="origin"]',
            'input[name*="origin"]'
        ],
        "structural": [
            'form input:first-of-type',
            '.search-form input:nth-child(1)',
            'div[role="combobox"] input:first-child'
        ],
        "class_based": [
            '.II2One input:first-child',
            '.input-group input:first-child',
            '.origin-input'
        ],
        "content_based": [
            'input:below(text("From"))',
            'input:near(text("Origin"))'
        ]
    },
    
    "destination_input": {
        "semantic": [
            'input[aria-label*="Where to"]',
            'input[aria-label*="Destination"]', 
            'input[placeholder*="Where to"]',
            'input[data-testid*="destination"]',
            'input[name*="destination"]'
        ],
        "structural": [
            'form input:nth-of-type(2)',
            '.search-form input:nth-child(2)',
            'div[role="combobox"] input:nth-child(2)'
        ],
        "class_based": [
            '.II2One input:nth-child(2)',
            '.input-group input:nth-child(2)',
            '.destination-input'
        ],
        "content_based": [
            'input:below(text("To"))',
            'input:near(text("Destination"))'
        ]
    },
    
    "departure_date": {
        "semantic": [
            'input[aria-label*="Departure"]',
            'input[placeholder*="Departure"]',
            'input[data-testid*="departure"]',
            'input[name*="departure"]',
            'input[type="date"]'
        ],
        "structural": [
            '.date-picker input:first-child',
            '.date-input:first-of-type input'
        ],
        "class_based": [
            '.departure-date input',
            '.date-selector input'
        ],
        "content_based": [
            'input:near(text("Departure"))',
            'input[value*="-"]'
        ]
    },
    
    "return_date": {
        "semantic": [
            'input[aria-label*="Return"]',
            'input[placeholder*="Return"]',
            'input[data-testid*="return"]',
            'input[name*="return"]'
        ],
        "structural": [
            '.date-picker input:nth-child(2)',
            '.date-input:nth-of-type(2) input'
        ],
        "class_based": [
            '.return-date input',
            '.date-selector input:nth-child(2)'
        ],
        "content_based": [
            'input:near(text("Return"))',
            'input:below(text("Return"))'
        ]
    },
    
    "search_button": {
        "semantic": [
            'button[aria-label*="Search"]',
            'button[type="submit"]',
            'button[data-testid*="search"]',
            'input[type="submit"]'
        ],
        "structural": [
            'form button',
            '.search-form button'
        ],
        "class_based": [
            '.search-button',
            '.submit-button',
            '.btn-search'
        ],
        "content_based": [
            'button:has-text("Search")',
            'div[role="button"]:has-text("Search")',
            'button:contains("Search")'
        ]
    },
    
    "flight_results": {
        "semantic": [
            '[data-testid*="flight"]',
            '[role="listitem"]',
            '[aria-label*="flight"]'
        ],
        "structural": [
            'div[role="tabpanel"] ul li',
            '.results-container li',
            '.flight-list li'
        ],
        "class_based": [
            '.pIav2d',
            '.flight-result',
            '.flight-card'
        ],
        "content_based": [
            'li:has-text("$")',
            'div:has-text("hr"):has-text("$")'
        ]
    }
}


async def robust_find_element(page: Page, element_type: str, timeout: int = 10000) -> Optional[ElementHandle]:
    """
    Find element using robust selector strategy with monitoring.
    
    Args:
        page: Playwright page object
        element_type: Type of element to find (must be in ROBUST_SELECTOR_CONFIGS)
        timeout: Maximum time to wait
        
    Returns:
        ElementHandle if found, None otherwise
    """
    if element_type not in ROBUST_SELECTOR_CONFIGS:
        logger.error(f"Unknown element type: {element_type}")
        return None
    
    selector = RobustSelector(element_type, page)
    config = ROBUST_SELECTOR_CONFIGS[element_type]
    
    return await selector.find_element(config, timeout)


async def robust_click(page: Page, element_type: str, timeout: int = 10000) -> bool:
    """Robustly click an element with monitoring."""
    element = await robust_find_element(page, element_type, timeout)
    if element:
        try:
            await element.click()
            await random_delay(0.5, 1.5)
            return True
        except Exception as e:
            logger.error(f"Failed to click {element_type}: {str(e)}")
            return False
    return False


async def robust_fill(page: Page, element_type: str, value: str, timeout: int = 10000) -> bool:
    """Robustly fill an input field with monitoring."""
    element = await robust_find_element(page, element_type, timeout)
    if element:
        try:
            await element.fill(value)
            await random_delay(0.5, 1.0)
            return True
        except Exception as e:
            logger.error(f"Failed to fill {element_type}: {str(e)}")
            return False
    return False


async def robust_get_text(page: Page, element_type: str, timeout: int = 5000) -> Optional[str]:
    """Robustly get text from an element with monitoring."""
    element = await robust_find_element(page, element_type, timeout)
    if element:
        try:
            text = await element.inner_text()
            return text.strip() if text else None
        except Exception as e:
            logger.error(f"Failed to get text from {element_type}: {str(e)}")
            return None
    return None