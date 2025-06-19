"""Form handling operations for Google Flights search interface."""


from loguru import logger
from playwright.async_api import Page

from ..utils import format_date_for_input, random_delay, robust_click, robust_fill
from .config import GOOGLE_FLIGHTS_URLS
from .models import ElementNotFoundError, NavigationError, ScrapingError, SearchCriteria, TripType


class FormHandler:
    """
    Handles all Google Flights search form operations.

    This class encapsulates navigation to Google Flights, form filling,
    and search triggering using robust selector strategies.

    Attributes:
        page (Page): The Playwright page instance for form interactions
    """

    def __init__(self, page: Page):
        """
        Initialize the FormHandler with a page instance.

        Args:
            page (Page): The Playwright page instance to use for form operations
        """
        self.page = page

    async def navigate_to_google_flights(self, criteria: SearchCriteria) -> None:
        """
        Navigate to the appropriate Google Flights URL based on search criteria.

        Chooses the optimal URL based on trip type and implements fallback
        navigation if the primary URL fails to load properly.

        Args:
            criteria (SearchCriteria): Search parameters to determine the appropriate URL

        Raises:
            NavigationError: If navigation fails with both primary and fallback URLs
        """
        try:
            # Select appropriate URL based on trip type
            url = (
                GOOGLE_FLIGHTS_URLS["round_trip"]
                if criteria.trip_type == TripType.ROUND_TRIP
                else GOOGLE_FLIGHTS_URLS["base"]
            )

            logger.info(f"🌐 Navigating to Google Flights: {url}")

            # Navigate with DOM content loaded strategy for faster loading
            await self.page.goto(url, wait_until="domcontentloaded")
            logger.info("✅ DOM content loaded, allowing page to stabilize...")

            # Give time for JavaScript to initialize
            await random_delay(3, 5)
            logger.info("✅ Successfully loaded Google Flights")

        except Exception as e:
            logger.error(f"❌ Primary navigation failed: {str(e)}")

            # Implement fallback navigation strategy
            try:
                logger.info("🔄 Attempting fallback navigation...")
                fallback_url = "https://www.google.com/travel/flights"
                await self.page.goto(fallback_url, wait_until="domcontentloaded")
                await random_delay(3, 5)
                logger.info("✅ Fallback navigation successful")

            except Exception as fallback_error:
                logger.error(f"❌ Fallback navigation also failed: {str(fallback_error)}")
                raise NavigationError(
                    f"Navigation failed with both primary and fallback URLs: {str(e)}"
                )

    async def fill_search_form(self, criteria: SearchCriteria) -> None:
        """
        Fill the Google Flights search form with the provided criteria.

        Uses robust selector strategies to reliably interact with form elements
        even when Google updates their interface. Handles all form fields including:
        - Origin airport/city
        - Destination airport/city
        - Departure date
        - Return date (for round-trip searches)

        Args:
            criteria (SearchCriteria): The search parameters to fill in the form

        Raises:
            ElementNotFoundError: If required form elements cannot be found
            ScrapingError: If form filling fails due to other reasons
        """
        try:
            logger.info(f"📝 Filling search form with robust selectors: {criteria.model_dump()}")

            # Fill origin field with robust selector strategy
            logger.info("🔍 Filling origin field...")
            origin_success = await robust_fill(self.page, "origin_input", criteria.origin)
            if not origin_success:
                logger.error("❌ Failed to fill origin field with all selector strategies")
                raise ElementNotFoundError(
                    "Could not find 'From' input field using any selector strategy"
                )

            logger.info("✅ Successfully filled origin field")
            await self.page.keyboard.press("Enter")
            await random_delay(1, 2)

            # Fill destination field with robust selector strategy
            logger.info("🔍 Filling destination field...")
            destination_success = await robust_fill(
                self.page, "destination_input", criteria.destination
            )
            if not destination_success:
                logger.error("❌ Failed to fill destination field with all selector strategies")
                raise ElementNotFoundError(
                    "Could not find 'To' input field using any selector strategy"
                )

            logger.info("✅ Successfully filled destination field")
            await self.page.keyboard.press("Enter")
            await random_delay(1, 2)

            # Handle departure date with multiple strategies
            await self._fill_departure_date(criteria.departure_date)

            # Handle return date for round-trip searches
            if criteria.trip_type == TripType.ROUND_TRIP and criteria.return_date:
                await self._fill_return_date(criteria.return_date)

            await random_delay(2, 3)
            logger.info("✅ Search form filled successfully with robust selectors")

        except Exception as e:
            logger.error(f"❌ Failed to fill search form: {str(e)}")
            raise ScrapingError(f"Form filling failed: {str(e)}")

    async def _fill_departure_date(self, departure_date) -> None:
        """
        Fill the departure date field with fallback strategies.

        Args:
            departure_date: The departure date to fill

        Raises:
            ElementNotFoundError: If departure date field cannot be found or filled
        """
        logger.info("🔍 Filling departure date...")
        departure_str = format_date_for_input(departure_date)

        # Try direct fill first
        departure_success = await robust_fill(self.page, "departure_date", departure_str)
        if not departure_success:
            logger.warning("⚠️ Could not fill departure date directly, trying click method")

            # Fallback to click-then-type approach
            if await robust_click(self.page, "departure_date"):
                await random_delay(1, 2)
                try:
                    await self.page.keyboard.type(departure_str)
                    logger.info("✅ Successfully filled departure date via click-type method")
                except Exception as e:
                    logger.error(f"❌ Click-type method also failed: {str(e)}")
                    raise ElementNotFoundError("Failed to interact with departure date field")
            else:
                logger.error("❌ Failed to interact with departure date field")
                raise ElementNotFoundError("Could not find or interact with departure date field")
        else:
            logger.info("✅ Successfully filled departure date")

        await self.page.keyboard.press("Enter")
        await random_delay(1, 2)

    async def _fill_return_date(self, return_date) -> None:
        """
        Fill the return date field for round-trip searches.

        Args:
            return_date: The return date to fill
        """
        logger.info("🔍 Filling return date...")
        return_str = format_date_for_input(return_date)

        return_success = await robust_fill(self.page, "return_date", return_str)
        if not return_success:
            logger.warning("⚠️ Could not fill return date")
        else:
            logger.info("✅ Successfully filled return date")

        await self.page.keyboard.press("Enter")
        await random_delay(1, 2)

    async def trigger_search(self) -> None:
        """
        Trigger the flight search using multiple fallback strategies.

        Implements a comprehensive search triggering approach:
        1. Robust selector-based button clicking
        2. JavaScript-based clicking as fallback
        3. Enter key press as final fallback
        4. Search execution validation

        Raises:
            ScrapingError: If all search trigger methods fail
        """
        try:
            logger.info("🔍 Triggering flight search with robust selectors...")
            search_triggered = False

            # Primary strategy: Robust search button clicking
            logger.info("🔍 Attempting robust search button click...")
            search_success = await robust_click(self.page, "search_button")

            if search_success:
                logger.info("✅ Successfully clicked search button with robust selector")
                search_triggered = True
                await random_delay(3, 5)
            else:
                search_triggered = await self._fallback_search_strategies()

            if not search_triggered:
                raise ScrapingError("Failed to trigger search with any method")

            # Wait for search processing and validate
            await self._wait_and_validate_search()

        except Exception as e:
            logger.error(f"❌ Failed to trigger search: {str(e)}")
            raise ScrapingError(f"Search trigger failed: {str(e)}")

    async def _fallback_search_strategies(self) -> bool:
        """
        Execute fallback search triggering strategies.

        Returns:
            bool: True if any fallback strategy succeeded, False otherwise
        """
        logger.warning("⚠️ Robust search button click failed, trying fallback methods...")

        # Fallback 1: JavaScript click (for when selectors change)
        try:
            logger.info("🔄 Trying JavaScript click fallback...")
            js_click_script = """
            document.querySelector("#yDmH0d > c-wiz.zQTmif.SSPGKf > div > div:nth-child(2) > c-wiz > div.cKvRXe > c-wiz > div.vg4Z0e > div:nth-child(1) > div.SS6Dqf.POQx1c > div.MXvFbd > div > button").click()
            """
            await self.page.evaluate(js_click_script)
            logger.info("✅ JavaScript click fallback succeeded")
            await random_delay(3, 5)
            return True

        except Exception as js_error:
            logger.warning(f"⚠️ JavaScript click fallback failed: {js_error}")

        # Fallback 2: Enter key press
        try:
            logger.info("🔄 Trying Enter key as final fallback...")
            await self.page.keyboard.press("Enter")
            await random_delay(2, 3)
            logger.info("✅ Enter key fallback succeeded")
            return True

        except Exception as enter_error:
            logger.error(f"❌ All search trigger methods failed. Last error: {enter_error}")
            return False

    async def _wait_and_validate_search(self) -> None:
        """
        Wait for search execution and validate that it was triggered properly.

        Validates search success by checking URL parameters and waiting
        for flight results to begin loading.
        """
        logger.info("⏳ Waiting for search to execute...")
        await random_delay(10, 15)

        # Validate search was triggered by checking URL
        current_url = self.page.url
        logger.info(f"📍 Current URL after search: {current_url}")

        if "search?" in current_url:
            logger.info("✅ Search successfully triggered (URL contains 'search?')")
        else:
            logger.warning("⚠️ Search not triggered - URL doesn't contain 'search?'")

        # Wait for flight results to begin loading
        logger.info("⏳ Waiting for flight results to appear...")
        await random_delay(5, 8)

        logger.info("✅ Search trigger process completed")
