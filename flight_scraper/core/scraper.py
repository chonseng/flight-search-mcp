"""Google Flights web scraper implementation."""

import asyncio
import time
from datetime import date
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from loguru import logger

from .config import SCRAPER_CONFIG, GOOGLE_FLIGHTS_URLS, SELECTORS
from .models import (
    SearchCriteria, FlightOffer, FlightSegment, ScrapingResult, 
    TripType, ScrapingError, NavigationError, ElementNotFoundError, TimeoutError
)
from ..utils import (
    random_delay, wait_for_element, safe_click, safe_fill, safe_get_text,
    format_date_for_input, parse_duration, parse_price, parse_stops,
    retry_async_operation, normalize_airport_code
)


class GoogleFlightsScraper:
    """Google Flights web scraper using Playwright."""
    
    def __init__(self, headless: bool = False):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.headless = headless
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
        
    async def initialize(self) -> None:
        """Initialize the browser and context."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            self.context = await self.browser.new_context(
                user_agent=SCRAPER_CONFIG["user_agent"],
                viewport=SCRAPER_CONFIG["viewport"]
            )
            
            # Add stealth settings
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            self.page = await self.context.new_page()
            
            # Set default timeouts
            self.page.set_default_timeout(SCRAPER_CONFIG["timeout"])
            self.page.set_default_navigation_timeout(SCRAPER_CONFIG["navigation_timeout"])
            
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise ScrapingError(f"Browser initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up browser resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("Browser cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def navigate_to_google_flights(self, criteria: SearchCriteria) -> None:
        """Navigate to Google Flights with appropriate URL based on search criteria."""
        try:
            url = GOOGLE_FLIGHTS_URLS["round_trip"] if criteria.trip_type == TripType.ROUND_TRIP else GOOGLE_FLIGHTS_URLS["base"]
            logger.info(f"Navigating to Google Flights: {url}")
            await self.page.goto(url, wait_until="domcontentloaded")
            logger.info("DOM content loaded, proceeding without waiting for network idle...")
            await random_delay(3, 5)  # Give time for page to stabilize
            logger.info("Successfully loaded Google Flights")
        except Exception as e:
            logger.error(f"Failed to navigate to Google Flights: {str(e)}")
            # Try simple fallback URL
            try:
                logger.info("Trying simple fallback URL...")
                await self.page.goto("https://www.google.com/travel/flights", wait_until="domcontentloaded")
                await random_delay(3, 5)
                logger.info("Successfully loaded Google Flights with fallback URL")
            except Exception as fallback_error:
                logger.error(f"Fallback navigation also failed: {str(fallback_error)}")
                raise NavigationError(f"Navigation failed: {str(e)}")
    
    async def fill_search_form(self, criteria: SearchCriteria) -> None:
        """Fill the flight search form with criteria."""
        try:
            logger.info(f"Filling search form: {criteria.model_dump()}")
            
            # Handle the "From" field
            from_selector = 'input[placeholder*="Where from"], input[aria-label*="Where from"]'
            if not await safe_fill(self.page, from_selector, criteria.origin):
                # Try alternative selector
                from_selector = '.II2One input'
                if not await safe_fill(self.page, from_selector, criteria.origin):
                    raise ElementNotFoundError("Could not find 'From' input field")
            
            # Press Enter to confirm the "From" selection
            await self.page.keyboard.press('Enter')
            await random_delay(1, 2)
            
            # Handle the "To" field
            to_selector = 'input[placeholder*="Where to"], input[aria-label*="Where to"]'
            if not await safe_fill(self.page, to_selector, criteria.destination):
                # Try alternative selector
                to_selector = '.II2One input:nth-child(2)'
                if not await safe_fill(self.page, to_selector, criteria.destination):
                    raise ElementNotFoundError("Could not find 'To' input field")
            
            # Press Enter to confirm the "To" selection
            await self.page.keyboard.press('Enter')
            await random_delay(1, 2)
            
            # Handle departure date
            departure_str = format_date_for_input(criteria.departure_date)
            date_selector = 'input[placeholder*="Departure"], input[aria-label*="Departure"]'
            if not await safe_fill(self.page, date_selector, departure_str):
                logger.warning("Could not fill departure date directly, trying click method")
                # Try clicking on date picker
                if await safe_click(self.page, date_selector):
                    await random_delay(1, 2)
            
            # Press Enter after filling the departure date
            await self.page.keyboard.press('Enter')
            await random_delay(1, 2)
            
            # Handle return date for round-trip
            if criteria.trip_type == TripType.ROUND_TRIP and criteria.return_date:
                return_str = format_date_for_input(criteria.return_date)
                return_selector = 'input[placeholder*="Return"], input[aria-label*="Return"]'
                if not await safe_fill(self.page, return_selector, return_str):
                    logger.warning("Could not fill return date")
                # Press Enter after return date too
                await self.page.keyboard.press('Enter')
                await random_delay(1, 2)
            
            await random_delay(2, 3)
            logger.info("Search form filled successfully")
            
        except Exception as e:
            logger.error(f"Failed to fill search form: {str(e)}")
            raise ScrapingError(f"Form filling failed: {str(e)}")
    
    async def trigger_search(self) -> None:
        """Trigger the flight search."""
        try:
            logger.info("Triggering flight search...")
            
            search_triggered = False
            
            # Try JavaScript click approach first (most reliable based on user feedback)
            try:
                logger.info("Trying JavaScript click on search button...")
                js_click_script = '''
                document.querySelector("#yDmH0d > c-wiz.zQTmif.SSPGKf > div > div:nth-child(2) > c-wiz > div.cKvRXe > c-wiz > div.vg4Z0e > div:nth-child(1) > div.SS6Dqf.POQx1c > div.MXvFbd > div > button").click()
                '''
                await self.page.evaluate(js_click_script)
                logger.info("Successfully executed JavaScript click")
                search_triggered = True
                await random_delay(3, 5)
                
            except Exception as e:
                logger.warning(f"JavaScript click failed: {e}")
                
                # Fallback to Enter key approach
                try:
                    logger.info("Trying Enter key to trigger search...")
                    await self.page.keyboard.press('Enter')
                    await random_delay(2, 3)
                    search_triggered = True
                    
                except Exception as e2:
                    logger.warning(f"Enter key approach failed: {e2}")
                    
                    # Fallback to button clicking
                    search_selectors = [
                        'button:has-text("Explore")',
                        'button[aria-label*="Search"]',
                        'button:has-text("Search")',
                    ]
                    
                    search_clicked = False
                    for selector in search_selectors:
                        try:
                            if await safe_click(self.page, selector):
                                logger.info(f"Clicked search button with selector: {selector}")
                                await random_delay(2, 3)
                                search_clicked = True
                                search_triggered = True
                                break
                        except Exception as click_error:
                            logger.debug(f"Failed to click selector {selector}: {click_error}")
                        await random_delay(0.5, 1)
                    
                    if not search_clicked:
                        logger.warning("Could not trigger search with any method")
            
            # Wait for page to process the search
            logger.info("Waiting for search to execute...")
            await random_delay(10, 15)
            
            # Check if URL contains "search?" (proper search detection)
            current_url = self.page.url
            logger.info(f"Current URL after search: {current_url}")
            
            if "search?" in current_url:
                logger.info("Search successfully triggered (URL contains 'search?')")
            else:
                logger.warning("Search not triggered - URL doesn't contain 'search?'")
                logger.warning("Will try additional search button clicking...")
                
                # Try more aggressive search button clicking
                additional_selectors = [
                    'div[role="button"]:has-text("Search")',
                    'div[role="button"]:has-text("Explore")',
                ]
                
                for selector in additional_selectors:
                    try:
                        if await safe_click(self.page, selector):
                            logger.info(f"Clicked additional search selector: {selector}")
                            await random_delay(3, 5)
                            
                            # Check URL again
                            new_url = self.page.url
                            if "search?" in new_url:
                                logger.info("Search now triggered after additional clicking")
                                break
                    except Exception as e:
                        logger.debug(f"Additional selector {selector} failed: {e}")
            
            # Wait for flight results to load
            logger.info("Waiting for flight results to appear...")
            await random_delay(5, 8)
            
            logger.info("Search triggered successfully")
            
        except Exception as e:
            logger.error(f"Failed to trigger search: {str(e)}")
            raise ScrapingError(f"Search trigger failed: {str(e)}")
    
    async def extract_flight_data(self, criteria: SearchCriteria, max_results: int = 50) -> List[FlightOffer]:
        """Extract flight information from the results page."""
        try:
            logger.info("Extracting flight data...")
            
            # Skip clicking cheapest button - use direct UL targeting approach
            logger.info("Using direct UL targeting strategy (skipping cheapest button)")
            
            # Use specific UL targeting strategy based on user's guidance
            logger.info("Using specific UL targeting strategy...")
            await random_delay(3, 5)  # Give time for content to load
            
            # Find all UL elements within tabpanel using JavaScript
            try:
                logger.info("Finding all UL elements within div[role=tabpanel]...")
                
                ul_info = await self.page.evaluate('''
                () => {
                    const uls = document.querySelectorAll("div[role=tabpanel] ul");
                    return {
                        count: uls.length,
                        ulInfo: Array.from(uls).map((ul, index) => ({
                            index: index,
                            textLength: ul.innerText ? ul.innerText.length : 0,
                            textPreview: ul.innerText ? ul.innerText.substring(0, 100) : "No text",
                            liCount: ul.querySelectorAll('li').length
                        }))
                    };
                }
                ''')
                
                logger.info(f"🔍 Found {ul_info['count']} UL elements within tabpanel")
                
                for ul_data in ul_info['ulInfo']:
                    logger.info(f"🔍 UL {ul_data['index'] + 1}: {ul_data['liCount']} li elements, text preview: {ul_data['textPreview']}...")
                
                if ul_info['count'] >= 1:
                    logger.info(f"✅ Found {ul_info['count']} UL elements - targeting all UL elements with flight data")
                    
                    # Target all UL elements that contain flight data (li elements)
                    target_ul_indices = []
                    for ul_data in ul_info['ulInfo']:
                        if ul_data['liCount'] > 0:  # Only include ULs that have li elements
                            target_ul_indices.append(ul_data['index'])
                            logger.info(f"🎯 Will extract from UL {ul_data['index'] + 1} ({ul_data['liCount']} flights)")
                    
                    if not target_ul_indices:
                        logger.warning("❌ No UL elements found with li elements")
                        target_ul_indices = list(range(min(ul_info['count'], 6)))  # Fallback to first 6 ULs
                    
                else:
                    logger.warning(f"❌ No UL elements found within tabpanel")
                    target_ul_indices = []
                    
            except Exception as e:
                logger.error(f"Error finding UL elements: {e}")
                return []
            
            # Extract flight elements from target UL elements
            flights = []
            flight_elements = []
            
            for ul_index in target_ul_indices:
                try:
                    logger.info(f"Extracting flights from UL {ul_index + 1}...")
                    
                    # Use JavaScript to get the specific UL and its li elements directly
                    ul_data = await self.page.evaluate(f'''
                    () => {{
                        const uls = document.querySelectorAll("div[role=tabpanel] ul");
                        if (uls.length > {ul_index}) {{
                            const targetUl = uls[{ul_index}];
                            const liElements = targetUl.querySelectorAll('li');
                            return {{
                                found: true,
                                liCount: liElements.length,
                                textContent: targetUl.innerText.substring(0, 200)
                            }};
                        }}
                        return {{ found: false, liCount: 0, textContent: "" }};
                    }}
                    ''')
                    
                    if ul_data['found'] and ul_data['liCount'] > 0:
                        logger.info(f"✅ Found {ul_data['liCount']} li elements in UL {ul_index + 1}")
                        logger.info(f"🔍 UL {ul_index + 1} content preview: {ul_data['textContent']}...")
                        
                        # Use JavaScript to get handles to the li elements for data extraction
                        li_handles = await self.page.evaluate_handle(f'''
                        () => {{
                            const uls = document.querySelectorAll("div[role=tabpanel] ul");
                            if (uls.length > {ul_index}) {{
                                return Array.from(uls[{ul_index}].querySelectorAll('li'));
                            }}
                            return [];
                        }}
                        ''')
                        
                        # Convert JS handles to Playwright element handles
                        li_elements = await li_handles.evaluate('elements => elements')
                        
                        if isinstance(li_elements, list):
                            # Get actual Playwright elements for each li
                            for i in range(min(len(li_elements), max_results)):
                                try:
                                    # Use the index-based selector to get Playwright element handle
                                    element = await self.page.query_selector(f'div[role="tabpanel"] ul:nth-child({ul_index + 1}) li:nth-child({i + 1})')
                                    if element:
                                        flight_elements.append(element)
                                except Exception as e:
                                    logger.debug(f"Error getting element {i} from UL {ul_index + 1}: {e}")
                                    continue
                        
                        logger.info(f"✅ Successfully extracted {len([e for e in flight_elements if e])} elements from UL {ul_index + 1}")
                        
                    else:
                        logger.warning(f"❌ No li elements found in UL {ul_index + 1}")
                        
                except Exception as e:
                    logger.warning(f"Error extracting from UL {ul_index + 1}: {e}")
                    continue
            
            results_found = len(flight_elements) > 0
            working_selector = f"all UL elements with flight data ({len(target_ul_indices)} ULs)"
            
            if not results_found:
                logger.warning("No flight results found")
                return []
            
            # Remove duplicates by converting to set based on element handles
            unique_elements = list(dict.fromkeys(flight_elements))
            
            logger.info(f"Found {len(unique_elements)} flight elements")
            
            # Extract flight data from the found elements
            flights = []
            for i, element in enumerate(unique_elements[:max_results]):
                try:
                    flight_data = await self.extract_single_flight(element)
                    if flight_data:
                        flights.append(flight_data)
                        logger.info(f"✅ Extracted flight {i+1}: {flight_data.price} - {flight_data.segments[0].airline}")
                except Exception as e:
                    logger.warning(f"Failed to extract flight {i+1}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(flights)} flights")
            return flights
            
        except Exception as e:
            logger.error(f"Failed to extract flight data: {str(e)}")
            raise ScrapingError(f"Data extraction failed: {str(e)}")
    
    async def extract_single_flight(self, element) -> Optional[FlightOffer]:
        """Extract data from a single flight element."""
        try:
            # Extract price with comprehensive selectors and debugging
            price_selectors = [
                '[data-gs*="price"]',
                '[jsname*="price"]',
                'span[aria-label*="dollars"]',
                'span[aria-label*="price"]',
                'div[aria-label*="dollars"]',
                '*[aria-label*="price"]'
            ]
            
            price = "N/A"
            # First try to find any element containing dollar sign
            try:
                all_text_elements = await element.query_selector_all('span, div')
                for text_element in all_text_elements:
                    try:
                        text_content = await text_element.inner_text()
                        if text_content and '$' in text_content and any(char.isdigit() for char in text_content):
                            price = parse_price(text_content)
                            if price and price != "N/A" and '$' in price:
                                logger.debug(f"Found price via text search: {price}")
                                break
                    except:
                        continue
            except:
                pass
            
            # If text search didn't work, try specific selectors
            if price == "N/A":
                for selector in price_selectors:
                    try:
                        price_element = await element.query_selector(selector)
                        if price_element:
                            price_text = await price_element.inner_text()
                            if price_text and '$' in price_text:
                                price = parse_price(price_text)
                                if price and price != "N/A":
                                    logger.debug(f"Found price via selector {selector}: {price}")
                                    break
                    except:
                        continue
            
            # Extract airline
            airline_selectors = ['.Ir0Voe', '.sSHqwe', '[data-gs*="airline"]']
            airline = "Unknown"
            for selector in airline_selectors:
                airline_element = await element.query_selector(selector)
                if airline_element:
                    airline = await airline_element.inner_text()
                    break
            
            # Extract duration
            duration_selectors = ['.gvkrdb', '.AdWm1c', '[data-gs*="duration"]']
            duration = "N/A"
            for selector in duration_selectors:
                duration_element = await element.query_selector(selector)
                if duration_element:
                    duration_text = await duration_element.inner_text()
                    duration = parse_duration(duration_text)
                    break
            
            # Extract stops information
            stops_selectors = ['.EfT7Ae .ogfYpf', '.c8rWCd', '[data-gs*="stops"]']
            stops_text = ""
            for selector in stops_selectors:
                stops_element = await element.query_selector(selector)
                if stops_element:
                    stops_text = await stops_element.inner_text()
                    break
            
            stops = parse_stops(stops_text)
            
            # Extract departure and arrival times
            time_selectors = ['.wtdjmc .eoY5cb', '.zxVSec', '[data-gs*="time"]']
            departure_time = "N/A"
            arrival_time = "N/A"
            
            for selector in time_selectors:
                time_elements = await element.query_selector_all(selector)
                if len(time_elements) >= 2:
                    departure_time = await time_elements[0].inner_text()
                    arrival_time = await time_elements[-1].inner_text()
                    break
            
            # Create flight segment (simplified for now)
            segment = FlightSegment(
                airline=airline.strip(),
                departure_airport="N/A",  # Would need more complex extraction
                arrival_airport="N/A",
                departure_time=departure_time.strip(),
                arrival_time=arrival_time.strip(),
                duration=duration
            )
            
            # Create flight offer
            flight_offer = FlightOffer(
                price=price,
                stops=stops,
                total_duration=duration,
                segments=[segment]
            )
            
            return flight_offer
            
        except Exception as e:
            logger.warning(f"Error extracting single flight: {str(e)}")
            return None
    
    async def scrape_flights(self, criteria: SearchCriteria) -> ScrapingResult:
        """Main method to scrape flights based on search criteria."""
        start_time = time.time()
        
        try:
            logger.info(f"Starting flight scraping for {criteria.origin} -> {criteria.destination}")
            
            
            # Navigate to Google Flights with appropriate URL
            await self.navigate_to_google_flights(criteria)
            
            # Fill search form
            await self.fill_search_form(criteria)
            
            # Trigger search
            await self.trigger_search()
            
            # Extract flight data
            flights = await self.extract_flight_data(criteria, criteria.max_results)
            
            execution_time = time.time() - start_time
            
            result = ScrapingResult(
                search_criteria=criteria,
                flights=flights,
                total_results=len(flights),
                success=True,
                execution_time=execution_time
            )
            
            logger.info(f"Scraping completed successfully. Found {len(flights)} flights in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Scraping failed: {str(e)}")
            
            return ScrapingResult(
                search_criteria=criteria,
                flights=[],
                total_results=0,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )


async def scrape_flights_async(
    origin: str,
    destination: str,
    departure_date: date,
    return_date: Optional[date] = None,
    max_results: int = 50,
    headless: bool = False
) -> ScrapingResult:
    """Convenience function to scrape flights asynchronously."""
    
    criteria = SearchCriteria(
        origin=normalize_airport_code(origin),
        destination=normalize_airport_code(destination),
        departure_date=departure_date,
        return_date=return_date,
        trip_type=TripType.ROUND_TRIP if return_date else TripType.ONE_WAY,
        max_results=max_results
    )
    logger.info(f"Created SearchCriteria: {criteria.model_dump()}")
    
    async with GoogleFlightsScraper(headless=headless) as scraper:
        return await scraper.scrape_flights(criteria)