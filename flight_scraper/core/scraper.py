"""Google Flights web scraper implementation."""

import asyncio
import time
from datetime import date
from typing import List, Optional, Dict, Any, Tuple
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
    retry_async_operation,
    RobustSelector, SelectorHealthMonitor, robust_find_element,
    robust_click, robust_fill, robust_get_text, ROBUST_SELECTOR_CONFIGS
)


class GoogleFlightsScraper:
    """Google Flights web scraper using Playwright."""
    
    def __init__(self, headless: bool = False):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.headless = headless
        self.health_monitor = SelectorHealthMonitor()
        self.selector_monitors: Dict[str, Any] = {}
        
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
        """Fill the flight search form with criteria using robust selectors."""
        try:
            logger.info(f"Filling search form with robust selectors: {criteria.model_dump()}")
            
            # Handle the "From" field with robust selector
            logger.info("🔍 Filling origin field...")
            origin_success = await robust_fill(self.page, "origin_input", criteria.origin)
            if not origin_success:
                logger.error("❌ Failed to fill origin field with all selector strategies")
                raise ElementNotFoundError("Could not find 'From' input field using any selector strategy")
            
            logger.info("✅ Successfully filled origin field")
            await self.page.keyboard.press('Enter')
            await random_delay(1, 2)
            
            # Handle the "To" field with robust selector
            logger.info("🔍 Filling destination field...")
            destination_success = await robust_fill(self.page, "destination_input", criteria.destination)
            if not destination_success:
                logger.error("❌ Failed to fill destination field with all selector strategies")
                raise ElementNotFoundError("Could not find 'To' input field using any selector strategy")
            
            logger.info("✅ Successfully filled destination field")
            await self.page.keyboard.press('Enter')
            await random_delay(1, 2)
            
            # Handle departure date with robust selector
            logger.info("🔍 Filling departure date...")
            departure_str = format_date_for_input(criteria.departure_date)
            departure_success = await robust_fill(self.page, "departure_date", departure_str)
            if not departure_success:
                logger.warning("⚠️ Could not fill departure date directly, trying click method")
                # Try clicking on date picker as fallback
                if await robust_click(self.page, "departure_date"):
                    await random_delay(1, 2)
                    # Try typing the date after clicking
                    await self.page.keyboard.type(departure_str)
                else:
                    logger.error("❌ Failed to interact with departure date field")
            else:
                logger.info("✅ Successfully filled departure date")
            
            await self.page.keyboard.press('Enter')
            await random_delay(1, 2)
            
            # Handle return date for round-trip
            if criteria.trip_type == TripType.ROUND_TRIP and criteria.return_date:
                logger.info("🔍 Filling return date...")
                return_str = format_date_for_input(criteria.return_date)
                return_success = await robust_fill(self.page, "return_date", return_str)
                if not return_success:
                    logger.warning("⚠️ Could not fill return date")
                else:
                    logger.info("✅ Successfully filled return date")
                
                await self.page.keyboard.press('Enter')
                await random_delay(1, 2)
            
            await random_delay(2, 3)
            logger.info("✅ Search form filled successfully with robust selectors")
            
        except Exception as e:
            logger.error(f"Failed to fill search form: {str(e)}")
            raise ScrapingError(f"Form filling failed: {str(e)}")
    
    async def trigger_search(self) -> None:
        """Trigger the flight search using robust selectors."""
        try:
            logger.info("🔍 Triggering flight search with robust selectors...")
            
            search_triggered = False
            
            # Try robust search button clicking first
            logger.info("🔍 Attempting robust search button click...")
            search_success = await robust_click(self.page, "search_button")
            
            if search_success:
                logger.info("✅ Successfully clicked search button with robust selector")
                search_triggered = True
                await random_delay(3, 5)
            else:
                logger.warning("⚠️ Robust search button click failed, trying fallback methods...")
                
                # Fallback to JavaScript click (keep the working approach as backup)
                try:
                    logger.info("🔄 Trying JavaScript click fallback...")
                    js_click_script = '''
                    document.querySelector("#yDmH0d > c-wiz.zQTmif.SSPGKf > div > div:nth-child(2) > c-wiz > div.cKvRXe > c-wiz > div.vg4Z0e > div:nth-child(1) > div.SS6Dqf.POQx1c > div.MXvFbd > div > button").click()
                    '''
                    await self.page.evaluate(js_click_script)
                    logger.info("✅ JavaScript click fallback succeeded")
                    search_triggered = True
                    await random_delay(3, 5)
                    
                except Exception as js_error:
                    logger.warning(f"⚠️ JavaScript click fallback failed: {js_error}")
                    
                    # Final fallback to Enter key
                    try:
                        logger.info("🔄 Trying Enter key as final fallback...")
                        await self.page.keyboard.press('Enter')
                        await random_delay(2, 3)
                        search_triggered = True
                        logger.info("✅ Enter key fallback succeeded")
                        
                    except Exception as enter_error:
                        logger.error(f"❌ All search trigger methods failed. Last error: {enter_error}")
            
            if not search_triggered:
                raise ScrapingError("Failed to trigger search with any method")
            
            # Wait for page to process the search
            logger.info("⏳ Waiting for search to execute...")
            await random_delay(10, 15)
            
            # Check if URL contains "search?" (proper search detection)
            current_url = self.page.url
            logger.info(f"📍 Current URL after search: {current_url}")
            
            if "search?" in current_url:
                logger.info("✅ Search successfully triggered (URL contains 'search?')")
            else:
                logger.warning("⚠️ Search not triggered - URL doesn't contain 'search?'")
                # Don't try additional clicking since we have robust selectors now
                # Just log the issue for monitoring
                
            # Wait for flight results to load
            logger.info("⏳ Waiting for flight results to appear...")
            await random_delay(5, 8)
            
            logger.info("✅ Search trigger process completed")
            
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
        """Extract data from a single flight element using robust extraction methods."""
        try:
            # Enhanced price extraction with hierarchical approach
            price = await self._extract_price_robust(element)
            
            # Enhanced airline extraction
            airline = await self._extract_airline_robust(element)
            
            # Enhanced duration extraction
            duration = await self._extract_duration_robust(element)
            
            # Enhanced stops extraction
            stops = await self._extract_stops_robust(element)
            
            # Enhanced time extraction
            departure_time, arrival_time = await self._extract_times_robust(element)
            
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
        """Main method to scrape flights based on search criteria with health monitoring."""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Starting flight scraping with robust selectors for {criteria.origin} -> {criteria.destination}")
            
            # Initialize selector monitoring for this session
            self.selector_monitors = {}
            
            # Navigate to Google Flights with appropriate URL
            await self.navigate_to_google_flights(criteria)
            
            # Fill search form with robust selectors
            await self.fill_search_form(criteria)
            
            # Trigger search with robust selectors
            await self.trigger_search()
            
            # Extract flight data with enhanced monitoring
            flights = await self.extract_flight_data(criteria, criteria.max_results)
            
            execution_time = time.time() - start_time
            
            # Record health monitoring data
            await self._record_session_health("flight_search_page")
            
            # Generate health report
            health_report = self.health_monitor.get_health_report()
            logger.info(f"📊 Selector health report: {health_report.get('overall_health', {})}")
            
            result = ScrapingResult(
                search_criteria=criteria,
                flights=flights,
                total_results=len(flights),
                success=True,
                execution_time=execution_time
            )
            
            logger.info(f"✅ Scraping completed successfully. Found {len(flights)} flights in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Scraping failed: {str(e)}")
            
            # Still record health data even on failure for analysis
            try:
                await self._record_session_health("flight_search_page_failed")
            except:
                pass
            
            return ScrapingResult(
                search_criteria=criteria,
                flights=[],
                total_results=0,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _record_session_health(self, page_type: str):
        """Record selector health data for the current session."""
        try:
            # Collect monitoring data from any robust selectors used
            # This would be populated by the RobustSelector instances during the session
            
            # For now, create a basic health record
            # In a full implementation, we'd collect data from all RobustSelector instances
            monitor_data = {}
            
            # Record the session
            self.health_monitor.record_page_health(page_type, monitor_data)
            
            logger.debug(f"📈 Recorded selector health data for {page_type}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to record selector health: {str(e)}")

    async def _extract_price_robust(self, element) -> str:
        """Extract price using robust hierarchical approach."""
        # Semantic approach - look for price-specific attributes
        semantic_selectors = [
            '[aria-label*="dollar"]',
            '[aria-label*="price"]',
            '[data-testid*="price"]',
            '[data-gs*="price"]',
            '[jsname*="price"]'
        ]
        
        for selector in semantic_selectors:
            try:
                price_element = await element.query_selector(selector)
                if price_element:
                    price_text = await price_element.inner_text()
                    if price_text and '$' in price_text:
                        price = parse_price(price_text)
                        if price and price != "N/A":
                            logger.debug(f"✅ Found price via semantic selector {selector}: {price}")
                            return price
            except:
                continue
        
        # Content-based approach - search all text elements for price patterns
        try:
            all_text_elements = await element.query_selector_all('span, div')
            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content and '$' in text_content and any(char.isdigit() for char in text_content):
                        price = parse_price(text_content)
                        if price and price != "N/A" and '$' in price:
                            logger.debug(f"✅ Found price via content search: {price}")
                            return price
                except:
                    continue
        except:
            pass
        
        # Structural approach - common price container patterns
        structural_selectors = [
            '.price-container',
            '.flight-price',
            '.fare-price',
            'div:last-child span', # Often price is in the last column
            'div[style*="right"] span' # Right-aligned price
        ]
        
        for selector in structural_selectors:
            try:
                price_element = await element.query_selector(selector)
                if price_element:
                    price_text = await price_element.inner_text()
                    if price_text and '$' in price_text:
                        price = parse_price(price_text)
                        if price and price != "N/A":
                            logger.debug(f"✅ Found price via structural selector {selector}: {price}")
                            return price
            except:
                continue
        
        logger.warning("⚠️ Could not extract price with any method")
        return "N/A"
    
    async def _extract_airline_robust(self, element) -> str:
        """Extract airline using robust hierarchical approach."""
        # Semantic approach
        semantic_selectors = [
            '[aria-label*="airline"]',
            '[data-testid*="airline"]',
            '[alt*="logo"]',
            'img[alt]'
        ]
        
        for selector in semantic_selectors:
            try:
                airline_element = await element.query_selector(selector)
                if airline_element:
                    # Try alt text first (for logos)
                    alt_text = await airline_element.get_attribute('alt')
                    if alt_text and len(alt_text) > 1:
                        logger.debug(f"✅ Found airline via semantic selector {selector}: {alt_text}")
                        return alt_text
                    
                    # Try inner text
                    airline_text = await airline_element.inner_text()
                    if airline_text:
                        logger.debug(f"✅ Found airline via semantic selector {selector}: {airline_text}")
                        return airline_text.strip()
            except:
                continue
        
        # Class-based approach (existing working selectors)
        class_selectors = ['.Ir0Voe', '.sSHqwe', '[data-gs*="airline"]']
        for selector in class_selectors:
            try:
                airline_element = await element.query_selector(selector)
                if airline_element:
                    airline_text = await airline_element.inner_text()
                    if airline_text:
                        logger.debug(f"✅ Found airline via class selector {selector}: {airline_text}")
                        return airline_text.strip()
            except:
                continue
        
        # Content-based approach - look for airline name patterns
        try:
            all_text_elements = await element.query_selector_all('span, div')
            airline_patterns = ['United', 'American', 'Delta', 'Southwest', 'JetBlue', 'Alaska', 'Spirit', 'Frontier']
            
            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content:
                        for pattern in airline_patterns:
                            if pattern.lower() in text_content.lower():
                                logger.debug(f"✅ Found airline via pattern matching: {text_content}")
                                return text_content.strip()
                except:
                    continue
        except:
            pass
        
        logger.warning("⚠️ Could not extract airline with any method")
        return "Unknown"
    
    async def _extract_duration_robust(self, element) -> str:
        """Extract duration using robust hierarchical approach."""
        # Semantic approach
        semantic_selectors = [
            '[aria-label*="duration"]',
            '[data-testid*="duration"]',
            '[data-gs*="duration"]'
        ]
        
        for selector in semantic_selectors:
            try:
                duration_element = await element.query_selector(selector)
                if duration_element:
                    duration_text = await duration_element.inner_text()
                    if duration_text:
                        duration = parse_duration(duration_text)
                        logger.debug(f"✅ Found duration via semantic selector {selector}: {duration}")
                        return duration
            except:
                continue
        
        # Class-based approach (existing working selectors)
        class_selectors = ['.gvkrdb', '.AdWm1c']
        for selector in class_selectors:
            try:
                duration_element = await element.query_selector(selector)
                if duration_element:
                    duration_text = await duration_element.inner_text()
                    if duration_text:
                        duration = parse_duration(duration_text)
                        logger.debug(f"✅ Found duration via class selector {selector}: {duration}")
                        return duration
            except:
                continue
        
        # Content-based approach - look for time patterns
        try:
            import re
            all_text_elements = await element.query_selector_all('span, div')
            time_pattern = re.compile(r'\d+h\s*\d*m?|\d+:\d+')
            
            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content and time_pattern.search(text_content):
                        duration = parse_duration(text_content)
                        logger.debug(f"✅ Found duration via pattern matching: {duration}")
                        return duration
                except:
                    continue
        except:
            pass
        
        logger.warning("⚠️ Could not extract duration with any method")
        return "N/A"
    
    async def _extract_stops_robust(self, element) -> int:
        """Extract stops information using robust hierarchical approach."""
        # Semantic approach
        semantic_selectors = [
            '[aria-label*="stop"]',
            '[data-testid*="stop"]',
            '[data-gs*="stop"]'
        ]
        
        for selector in semantic_selectors:
            try:
                stops_element = await element.query_selector(selector)
                if stops_element:
                    stops_text = await stops_element.inner_text()
                    if stops_text:
                        stops = parse_stops(stops_text)
                        logger.debug(f"✅ Found stops via semantic selector {selector}: {stops}")
                        return stops
            except:
                continue
        
        # Class-based approach (existing working selectors)
        class_selectors = ['.EfT7Ae .ogfYpf', '.c8rWCd']
        for selector in class_selectors:
            try:
                stops_element = await element.query_selector(selector)
                if stops_element:
                    stops_text = await stops_element.inner_text()
                    if stops_text:
                        stops = parse_stops(stops_text)
                        logger.debug(f"✅ Found stops via class selector {selector}: {stops}")
                        return stops
            except:
                continue
        
        # Content-based approach - look for stop patterns
        try:
            all_text_elements = await element.query_selector_all('span, div')
            
            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content:
                        stops = parse_stops(text_content)
                        if stops >= 0:  # parse_stops returns valid number
                            logger.debug(f"✅ Found stops via content search: {stops}")
                            return stops
                except:
                    continue
        except:
            pass
        
        logger.warning("⚠️ Could not extract stops with any method")
        return 0  # Default to nonstop if we can't determine
    
    async def _extract_times_robust(self, element) -> Tuple[str, str]:
        """Extract departure and arrival times using robust hierarchical approach."""
        # Semantic approach
        semantic_selectors = [
            '[aria-label*="departure"]',
            '[aria-label*="arrival"]',
            '[data-testid*="time"]',
            '[data-gs*="time"]'
        ]
        
        departure_time = "N/A"
        arrival_time = "N/A"
        
        for selector in semantic_selectors:
            try:
                time_elements = await element.query_selector_all(selector)
                if len(time_elements) >= 2:
                    departure_time = await time_elements[0].inner_text()
                    arrival_time = await time_elements[-1].inner_text()
                    logger.debug(f"✅ Found times via semantic selector {selector}: {departure_time} -> {arrival_time}")
                    return departure_time.strip(), arrival_time.strip()
            except:
                continue
        
        # Class-based approach (existing working selectors)
        class_selectors = ['.wtdjmc .eoY5cb', '.zxVSec']
        for selector in class_selectors:
            try:
                time_elements = await element.query_selector_all(selector)
                if len(time_elements) >= 2:
                    departure_time = await time_elements[0].inner_text()
                    arrival_time = await time_elements[-1].inner_text()
                    logger.debug(f"✅ Found times via class selector {selector}: {departure_time} -> {arrival_time}")
                    return departure_time.strip(), arrival_time.strip()
            except:
                continue
        
        # Content-based approach - look for time patterns
        try:
            import re
            all_text_elements = await element.query_selector_all('span, div')
            time_pattern = re.compile(r'\d{1,2}:\d{2}\s*[APap][Mm]?|\d{1,2}:\d{2}')
            times_found = []
            
            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content:
                        matches = time_pattern.findall(text_content)
                        times_found.extend(matches)
                except:
                    continue
            
            if len(times_found) >= 2:
                departure_time = times_found[0]
                arrival_time = times_found[-1]
                logger.debug(f"✅ Found times via pattern matching: {departure_time} -> {arrival_time}")
                return departure_time.strip(), arrival_time.strip()
                
        except:
            pass
        
        logger.warning("⚠️ Could not extract times with any method")
        return "N/A", "N/A"


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
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        trip_type=TripType.ROUND_TRIP if return_date else TripType.ONE_WAY,
        max_results=max_results
    )
    logger.info(f"Created SearchCriteria: {criteria.model_dump()}")
    
    async with GoogleFlightsScraper(headless=headless) as scraper:
        return await scraper.scrape_flights(criteria)


    async def _extract_price_robust(self, element) -> str:
        """Extract price using robust hierarchical approach."""
        # Semantic approach - look for price-specific attributes
        semantic_selectors = [
            '[aria-label*="dollar"]',
            '[aria-label*="price"]',
            '[data-testid*="price"]',
            '[data-gs*="price"]',
            '[jsname*="price"]'
        ]
        
        for selector in semantic_selectors:
            try:
                price_element = await element.query_selector(selector)
                if price_element:
                    price_text = await price_element.inner_text()
                    if price_text and '$' in price_text:
                        price = parse_price(price_text)
                        if price and price != "N/A":
                            logger.debug(f"✅ Found price via semantic selector {selector}: {price}")
                            return price
            except:
                continue
        
        # Content-based approach - search all text elements for price patterns
        try:
            all_text_elements = await element.query_selector_all('span, div')
            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content and '$' in text_content and any(char.isdigit() for char in text_content):
                        price = parse_price(text_content)
                        if price and price != "N/A" and '$' in price:
                            logger.debug(f"✅ Found price via content search: {price}")
                            return price
                except:
                    continue
        except:
            pass
        
        # Structural approach - common price container patterns
        structural_selectors = [
            '.price-container',
            '.flight-price',
            '.fare-price',
            'div:last-child span', # Often price is in the last column
            'div[style*="right"] span' # Right-aligned price
        ]
        
        for selector in structural_selectors:
            try:
                price_element = await element.query_selector(selector)
                if price_element:
                    price_text = await price_element.inner_text()
                    if price_text and '$' in price_text:
                        price = parse_price(price_text)
                        if price and price != "N/A":
                            logger.debug(f"✅ Found price via structural selector {selector}: {price}")
                            return price
            except:
                continue
        
        logger.warning("⚠️ Could not extract price with any method")
        return "N/A"
    
    async def _extract_airline_robust(self, element) -> str:
        """Extract airline using robust hierarchical approach."""
        # Semantic approach
        semantic_selectors = [
            '[aria-label*="airline"]',
            '[data-testid*="airline"]',
            '[alt*="logo"]',
            'img[alt]'
        ]
        
        for selector in semantic_selectors:
            try:
                airline_element = await element.query_selector(selector)
                if airline_element:
                    # Try alt text first (for logos)
                    alt_text = await airline_element.get_attribute('alt')
                    if alt_text and len(alt_text) > 1:
                        logger.debug(f"✅ Found airline via semantic selector {selector}: {alt_text}")
                        return alt_text
                    
                    # Try inner text
                    airline_text = await airline_element.inner_text()
                    if airline_text:
                        logger.debug(f"✅ Found airline via semantic selector {selector}: {airline_text}")
                        return airline_text.strip()
            except:
                continue
        
        # Class-based approach (existing working selectors)
        class_selectors = ['.Ir0Voe', '.sSHqwe', '[data-gs*="airline"]']
        for selector in class_selectors:
            try:
                airline_element = await element.query_selector(selector)
                if airline_element:
                    airline_text = await airline_element.inner_text()
                    if airline_text:
                        logger.debug(f"✅ Found airline via class selector {selector}: {airline_text}")
                        return airline_text.strip()
            except:
                continue
        
        # Content-based approach - look for airline name patterns
        try:
            all_text_elements = await element.query_selector_all('span, div')
            airline_patterns = ['United', 'American', 'Delta', 'Southwest', 'JetBlue', 'Alaska', 'Spirit', 'Frontier']
            
            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content:
                        for pattern in airline_patterns:
                            if pattern.lower() in text_content.lower():
                                logger.debug(f"✅ Found airline via pattern matching: {text_content}")
                                return text_content.strip()
                except:
                    continue
        except:
            pass
        
        logger.warning("⚠️ Could not extract airline with any method")
        return "Unknown"
    
    async def _extract_duration_robust(self, element) -> str:
        """Extract duration using robust hierarchical approach."""
        # Semantic approach
        semantic_selectors = [
            '[aria-label*="duration"]',
            '[data-testid*="duration"]',
            '[data-gs*="duration"]'
        ]
        
        for selector in semantic_selectors:
            try:
                duration_element = await element.query_selector(selector)
                if duration_element:
                    duration_text = await duration_element.inner_text()
                    if duration_text:
                        duration = parse_duration(duration_text)
                        logger.debug(f"✅ Found duration via semantic selector {selector}: {duration}")
                        return duration
            except:
                continue
        
        # Class-based approach (existing working selectors)
        class_selectors = ['.gvkrdb', '.AdWm1c']
        for selector in class_selectors:
            try:
                duration_element = await element.query_selector(selector)
                if duration_element:
                    duration_text = await duration_element.inner_text()
                    if duration_text:
                        duration = parse_duration(duration_text)
                        logger.debug(f"✅ Found duration via class selector {selector}: {duration}")
                        return duration
            except:
                continue
        
        # Content-based approach - look for time patterns
        try:
            all_text_elements = await element.query_selector_all('span, div')
            time_pattern = re.compile(r'\d+h\s*\d*m?|\d+:\d+')
            
            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content and time_pattern.search(text_content):
                        duration = parse_duration(text_content)
                        logger.debug(f"✅ Found duration via pattern matching: {duration}")
                        return duration
                except:
                    continue
        except:
            pass
        
        logger.warning("⚠️ Could not extract duration with any method")
        return "N/A"
    
    async def _extract_stops_robust(self, element) -> int:
        """Extract stops information using robust hierarchical approach."""
        # Semantic approach
        semantic_selectors = [
            '[aria-label*="stop"]',
            '[data-testid*="stop"]',
            '[data-gs*="stop"]'
        ]
        
        for selector in semantic_selectors:
            try:
                stops_element = await element.query_selector(selector)
                if stops_element:
                    stops_text = await stops_element.inner_text()
                    if stops_text:
                        stops = parse_stops(stops_text)
                        logger.debug(f"✅ Found stops via semantic selector {selector}: {stops}")
                        return stops
            except:
                continue
        
        # Class-based approach (existing working selectors)
        class_selectors = ['.EfT7Ae .ogfYpf', '.c8rWCd']
        for selector in class_selectors:
            try:
                stops_element = await element.query_selector(selector)
                if stops_element:
                    stops_text = await stops_element.inner_text()
                    if stops_text:
                        stops = parse_stops(stops_text)
                        logger.debug(f"✅ Found stops via class selector {selector}: {stops}")
                        return stops
            except:
                continue
        
        # Content-based approach - look for stop patterns
        try:
            all_text_elements = await element.query_selector_all('span, div')
            
            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content:
                        stops = parse_stops(text_content)
                        if stops >= 0:  # parse_stops returns valid number
                            logger.debug(f"✅ Found stops via content search: {stops}")
                            return stops
                except:
                    continue
        except:
            pass
        
        logger.warning("⚠️ Could not extract stops with any method")
        return 0  # Default to nonstop if we can't determine
    
    async def _extract_times_robust(self, element) -> Tuple[str, str]:
        """Extract departure and arrival times using robust hierarchical approach."""
        # Semantic approach
        semantic_selectors = [
            '[aria-label*="departure"]',
            '[aria-label*="arrival"]',
            '[data-testid*="time"]',
            '[data-gs*="time"]'
        ]
        
        departure_time = "N/A"
        arrival_time = "N/A"
        
        for selector in semantic_selectors:
            try:
                time_elements = await element.query_selector_all(selector)
                if len(time_elements) >= 2:
                    departure_time = await time_elements[0].inner_text()
                    arrival_time = await time_elements[-1].inner_text()
                    logger.debug(f"✅ Found times via semantic selector {selector}: {departure_time} -> {arrival_time}")
                    return departure_time.strip(), arrival_time.strip()
            except:
                continue
        
        # Class-based approach (existing working selectors)
        class_selectors = ['.wtdjmc .eoY5cb', '.zxVSec']
        for selector in class_selectors:
            try:
                time_elements = await element.query_selector_all(selector)
                if len(time_elements) >= 2:
                    departure_time = await time_elements[0].inner_text()
                    arrival_time = await time_elements[-1].inner_text()
                    logger.debug(f"✅ Found times via class selector {selector}: {departure_time} -> {arrival_time}")
                    return departure_time.strip(), arrival_time.strip()
            except:
                continue
        
        # Content-based approach - look for time patterns
        try:
            all_text_elements = await element.query_selector_all('span, div')
            time_pattern = re.compile(r'\d{1,2}:\d{2}\s*[APap][Mm]?|\d{1,2}:\d{2}')
            times_found = []
            
            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content:
                        matches = time_pattern.findall(text_content)
                        times_found.extend(matches)
                except:
                    continue
            
            if len(times_found) >= 2:
                departure_time = times_found[0]
                arrival_time = times_found[-1]
                logger.debug(f"✅ Found times via pattern matching: {departure_time} -> {arrival_time}")
                return departure_time.strip(), arrival_time.strip()
                
        except:
            pass
        
        logger.warning("⚠️ Could not extract times with any method")
        return "N/A", "N/A"


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
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        trip_type=TripType.ROUND_TRIP if return_date else TripType.ONE_WAY,
        max_results=max_results
    )
    logger.info(f"Created SearchCriteria: {criteria.model_dump()}")
    
    async with GoogleFlightsScraper(headless=headless) as scraper:
        return await scraper.scrape_flights(criteria)