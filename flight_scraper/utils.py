"""Utility functions for the flight scraper."""

import asyncio
import random
import re
from datetime import datetime, date
from typing import Optional, Tuple, Any
from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .core.config import SCRAPER_CONFIG
from .core.models import ScrapingError, TimeoutError, ElementNotFoundError


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