"""Flight data extraction from Google Flights results."""

import re
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from playwright.async_api import ElementHandle, Page

from ..utils import parse_duration, parse_price, parse_stops, random_delay
from .models import FlightOffer, FlightSegment, ScrapingError, SearchCriteria


class DataExtractor:
    """
    Handles extraction of flight data from Google Flights search results.

    This class implements robust data extraction strategies using multiple
    approaches to handle Google's dynamic interface changes:
    - Semantic extraction (aria-labels, data attributes)
    - Structural extraction (CSS selectors, DOM hierarchy)
    - Content-based extraction (text pattern matching)

    Attributes:
        page (Page): The Playwright page instance for data extraction
    """

    def __init__(self, page: Page):
        """
        Initialize the DataExtractor with a page instance.

        Args:
            page (Page): The Playwright page instance containing flight results
        """
        self.page = page

    async def extract_flight_data(
        self, criteria: SearchCriteria, max_results: int = 50
    ) -> List[FlightOffer]:
        """
        Extract comprehensive flight information from the results page.

        Uses a multi-strategy approach to locate and extract flight data:
        1. Identifies flight result containers using UL element targeting
        2. Extracts individual flight elements from containers
        3. Processes each flight element to extract detailed information
        4. Returns structured flight offers with all available data

        Args:
            criteria (SearchCriteria): Original search parameters for context
            max_results (int): Maximum number of flight results to extract

        Returns:
            List[FlightOffer]: List of extracted flight offers with complete information

        Raises:
            ScrapingError: If flight data extraction fails completely
        """
        try:
            logger.info("🔍 Extracting flight data using advanced UL targeting strategy...")

            # Skip the cheapest button clicking - use direct targeting
            logger.info("📋 Using direct UL targeting strategy for better reliability")
            await random_delay(3, 5)  # Allow content to fully load

            # Find and analyze all UL elements containing flight data
            flight_containers = await self._find_flight_containers()
            if not flight_containers:
                logger.warning("❌ No flight containers found")
                return []

            # Extract flight elements from containers
            flight_elements = await self._extract_flight_elements(flight_containers, max_results)
            if not flight_elements:
                logger.warning("❌ No individual flight elements found")
                return []

            logger.info(f"✅ Found {len(flight_elements)} flight elements for processing")

            # Process each flight element to extract structured data
            flights = await self._process_flight_elements(flight_elements)

            logger.info(f"✅ Successfully extracted {len(flights)} complete flight offers")
            return flights

        except Exception as e:
            logger.error(f"❌ Failed to extract flight data: {str(e)}")
            raise ScrapingError(f"Data extraction failed: {str(e)}")

    async def _find_flight_containers(self) -> List[Dict[str, Any]]:
        """
        Find all UL elements within tabpanel that contain flight data.

        Returns:
            List[Dict[str, Any]]: Information about found flight containers
        """
        try:
            logger.info("🔍 Finding all UL elements within div[role=tabpanel]...")

            ul_info = await self.page.evaluate(
                """
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
            """
            )

            logger.info(f"🔍 Found {ul_info['count']} UL elements within tabpanel")

            # Log details about each container
            for ul_data in ul_info["ulInfo"]:
                logger.info(
                    f"🔍 UL {ul_data['index'] + 1}: {ul_data['liCount']} li elements, "
                    f"text preview: {ul_data['textPreview']}..."
                )

            # Filter containers that actually contain flight data (have li elements)
            valid_containers = []
            if ul_info["count"] >= 1:
                for ul_data in ul_info["ulInfo"]:
                    if ul_data["liCount"] > 0:  # Only include ULs with flight data
                        valid_containers.append(ul_data)
                        logger.info(
                            f"🎯 Will extract from UL {ul_data['index'] + 1} "
                            f"({ul_data['liCount']} flights)"
                        )

                if not valid_containers:
                    logger.warning("❌ No UL elements found with li elements")
                    # Fallback to first few ULs if none have li elements initially
                    valid_containers = ul_info["ulInfo"][: min(ul_info["count"], 6)]

            return valid_containers

        except Exception as e:
            logger.error(f"❌ Error finding UL elements: {e}")
            return []

    async def _extract_flight_elements(
        self, containers: List[Dict[str, Any]], max_results: int
    ) -> List[ElementHandle]:
        """
        Extract individual flight elements from flight containers.

        Args:
            containers: List of container information
            max_results: Maximum number of elements to extract

        Returns:
            List[ElementHandle]: List of flight element handles
        """
        flight_elements = []

        for container in containers:
            try:
                ul_index = container["index"]
                logger.info(f"📊 Extracting flights from UL {ul_index + 1}...")

                # Validate container still contains flight data
                ul_data = await self.page.evaluate(
                    f"""
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
                """
                )

                if ul_data["found"] and ul_data["liCount"] > 0:
                    logger.info(
                        f"✅ Confirmed {ul_data['liCount']} li elements in UL {ul_index + 1}"
                    )
                    logger.debug(
                        f"🔍 UL {ul_index + 1} content preview: {ul_data['textContent']}..."
                    )

                    # Extract individual flight elements
                    elements_added = 0
                    for i in range(min(ul_data["liCount"], max_results - len(flight_elements))):
                        try:
                            # Use nth-child selector to get specific flight element
                            selector = f'div[role="tabpanel"] ul:nth-child({ul_index + 1}) li:nth-child({i + 1})'
                            element = await self.page.query_selector(selector)

                            if element:
                                flight_elements.append(element)
                                elements_added += 1

                        except Exception as e:
                            logger.debug(f"⚠️ Error getting element {i} from UL {ul_index + 1}: {e}")
                            continue

                    logger.info(
                        f"✅ Successfully extracted {elements_added} elements from UL {ul_index + 1}"
                    )

                    # Stop if we've reached max_results
                    if len(flight_elements) >= max_results:
                        break

                else:
                    logger.warning(f"❌ No li elements found in UL {ul_index + 1}")

            except Exception as e:
                logger.warning(f"⚠️ Error extracting from UL {container['index'] + 1}: {e}")
                continue

        # Remove any duplicate elements
        unique_elements = list(dict.fromkeys(flight_elements))
        logger.info(f"📊 Final count: {len(unique_elements)} unique flight elements")

        return unique_elements

    async def _process_flight_elements(self, elements: List[ElementHandle]) -> List[FlightOffer]:
        """
        Process flight elements to extract structured flight data.

        Args:
            elements: List of flight element handles

        Returns:
            List[FlightOffer]: List of structured flight offers
        """
        flights = []

        for i, element in enumerate(elements):
            try:
                logger.debug(f"🔄 Processing flight element {i+1}/{len(elements)}")

                flight_data = await self.extract_single_flight(element)
                if flight_data:
                    flights.append(flight_data)
                    logger.info(
                        f"✅ Extracted flight {i+1}: {flight_data.price} - "
                        f"{flight_data.segments[0].airline}"
                    )
                else:
                    logger.warning(f"⚠️ Failed to extract data from flight element {i+1}")

            except Exception as e:
                logger.warning(f"⚠️ Error processing flight element {i+1}: {str(e)}")
                continue

        return flights

    async def extract_single_flight(self, element: ElementHandle) -> Optional[FlightOffer]:
        """
        Extract comprehensive data from a single flight element.

        Uses multiple extraction strategies for each data point to ensure
        robust data collection even when Google changes their interface.

        Args:
            element (ElementHandle): The flight element to extract data from

        Returns:
            Optional[FlightOffer]: Complete flight offer data or None if extraction fails
        """
        try:
            # Extract core flight information using robust methods
            price = await self._extract_price_robust(element)
            airline = await self._extract_airline_robust(element)
            duration = await self._extract_duration_robust(element)
            stops = await self._extract_stops_robust(element)
            departure_time, arrival_time = await self._extract_times_robust(element)

            # Create flight segment with extracted data
            segment = FlightSegment(
                airline=airline.strip(),
                departure_airport="N/A",  # Would require more complex extraction
                arrival_airport="N/A",  # Would require more complex extraction
                departure_time=departure_time.strip(),
                arrival_time=arrival_time.strip(),
                duration=duration,
            )

            # Create complete flight offer
            flight_offer = FlightOffer(
                price=price, stops=stops, total_duration=duration, segments=[segment]
            )

            return flight_offer

        except Exception as e:
            logger.warning(f"⚠️ Error extracting single flight data: {str(e)}")
            return None

    async def _extract_price_robust(self, element: ElementHandle) -> str:
        """
        Extract price using hierarchical extraction strategies.

        Args:
            element: Flight element to extract price from

        Returns:
            str: Extracted price or "N/A" if not found
        """
        # Strategy 1: Semantic approach - price-specific attributes
        semantic_selectors = [
            '[aria-label*="dollar"]',
            '[aria-label*="price"]',
            '[data-testid*="price"]',
            '[data-gs*="price"]',
            '[jsname*="price"]',
        ]

        for selector in semantic_selectors:
            try:
                price_element = await element.query_selector(selector)
                if price_element:
                    price_text = await price_element.inner_text()
                    if price_text and "$" in price_text:
                        price = parse_price(price_text)
                        if price and price != "N/A":
                            logger.debug(
                                f"✅ Found price via semantic selector {selector}: {price}"
                            )
                            return price
            except:
                continue

        # Strategy 2: Content-based approach - search all text for price patterns
        try:
            all_text_elements = await element.query_selector_all("span, div")
            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if (
                        text_content
                        and "$" in text_content
                        and any(char.isdigit() for char in text_content)
                    ):
                        price = parse_price(text_content)
                        if price and price != "N/A" and "$" in price:
                            logger.debug(f"✅ Found price via content search: {price}")
                            return price
                except:
                    continue
        except:
            pass

        # Strategy 3: Structural approach - common price container patterns
        structural_selectors = [
            ".price-container",
            ".flight-price",
            ".fare-price",
            "div:last-child span",  # Often price is in the last column
            'div[style*="right"] span',  # Right-aligned price
        ]

        for selector in structural_selectors:
            try:
                price_element = await element.query_selector(selector)
                if price_element:
                    price_text = await price_element.inner_text()
                    if price_text and "$" in price_text:
                        price = parse_price(price_text)
                        if price and price != "N/A":
                            logger.debug(
                                f"✅ Found price via structural selector {selector}: {price}"
                            )
                            return price
            except:
                continue

        logger.warning("⚠️ Could not extract price with any method")
        return "N/A"

    async def _extract_airline_robust(self, element: ElementHandle) -> str:
        """
        Extract airline information using multiple strategies.

        Args:
            element: Flight element to extract airline from

        Returns:
            str: Extracted airline name or "Unknown"
        """
        # Strategy 1: Semantic approach
        semantic_selectors = [
            '[aria-label*="airline"]',
            '[data-testid*="airline"]',
            '[alt*="logo"]',
            "img[alt]",
        ]

        for selector in semantic_selectors:
            try:
                airline_element = await element.query_selector(selector)
                if airline_element:
                    # Try alt text first (for airline logos)
                    alt_text = await airline_element.get_attribute("alt")
                    if alt_text and len(alt_text) > 1:
                        logger.debug(
                            f"✅ Found airline via semantic selector {selector}: {alt_text}"
                        )
                        return alt_text

                    # Try inner text
                    airline_text = await airline_element.inner_text()
                    if airline_text:
                        logger.debug(
                            f"✅ Found airline via semantic selector {selector}: {airline_text}"
                        )
                        return airline_text.strip()
            except:
                continue

        # Strategy 2: Class-based approach (existing working selectors)
        class_selectors = [".Ir0Voe", ".sSHqwe", '[data-gs*="airline"]']
        for selector in class_selectors:
            try:
                airline_element = await element.query_selector(selector)
                if airline_element:
                    airline_text = await airline_element.inner_text()
                    if airline_text:
                        logger.debug(
                            f"✅ Found airline via class selector {selector}: {airline_text}"
                        )
                        return airline_text.strip()
            except:
                continue

        # Strategy 3: Content-based approach - pattern matching
        try:
            all_text_elements = await element.query_selector_all("span, div")
            airline_patterns = [
                "United",
                "American",
                "Delta",
                "Southwest",
                "JetBlue",
                "Alaska",
                "Spirit",
                "Frontier",
                "Lufthansa",
                "British Airways",
            ]

            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content:
                        for pattern in airline_patterns:
                            if pattern.lower() in text_content.lower():
                                logger.debug(
                                    f"✅ Found airline via pattern matching: {text_content}"
                                )
                                return text_content.strip()
                except:
                    continue
        except:
            pass

        logger.warning("⚠️ Could not extract airline with any method")
        return "Unknown"

    async def _extract_duration_robust(self, element: ElementHandle) -> str:
        """
        Extract flight duration using multiple strategies.

        Args:
            element: Flight element to extract duration from

        Returns:
            str: Extracted duration or "N/A"
        """
        # Strategy 1: Semantic approach
        semantic_selectors = [
            '[aria-label*="duration"]',
            '[data-testid*="duration"]',
            '[data-gs*="duration"]',
        ]

        for selector in semantic_selectors:
            try:
                duration_element = await element.query_selector(selector)
                if duration_element:
                    duration_text = await duration_element.inner_text()
                    if duration_text:
                        duration = parse_duration(duration_text)
                        logger.debug(
                            f"✅ Found duration via semantic selector {selector}: {duration}"
                        )
                        return duration
            except:
                continue

        # Strategy 2: Class-based approach
        class_selectors = [".gvkrdb", ".AdWm1c"]
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

        # Strategy 3: Content-based pattern matching
        try:
            time_pattern = re.compile(r"\d+h\s*\d*m?|\d+:\d+")
            all_text_elements = await element.query_selector_all("span, div")

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

    async def _extract_stops_robust(self, element: ElementHandle) -> int:
        """
        Extract number of stops using multiple strategies.

        Args:
            element: Flight element to extract stops from

        Returns:
            int: Number of stops (0 for nonstop)
        """
        # Strategy 1: Semantic approach
        semantic_selectors = ['[aria-label*="stop"]', '[data-testid*="stop"]', '[data-gs*="stop"]']

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

        # Strategy 2: Class-based approach
        class_selectors = [".EfT7Ae .ogfYpf", ".c8rWCd"]
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

        # Strategy 3: Content-based approach
        try:
            all_text_elements = await element.query_selector_all("span, div")

            for text_element in all_text_elements:
                try:
                    text_content = await text_element.inner_text()
                    if text_content:
                        stops = parse_stops(text_content)
                        if stops >= 0:  # Valid number found
                            logger.debug(f"✅ Found stops via content search: {stops}")
                            return stops
                except:
                    continue
        except:
            pass

        logger.warning("⚠️ Could not extract stops with any method")
        return 0  # Default to nonstop

    async def _extract_times_robust(self, element: ElementHandle) -> Tuple[str, str]:
        """
        Extract departure and arrival times using multiple strategies.

        Args:
            element: Flight element to extract times from

        Returns:
            Tuple[str, str]: (departure_time, arrival_time)
        """
        # Strategy 1: Semantic approach
        semantic_selectors = [
            '[aria-label*="departure"]',
            '[aria-label*="arrival"]',
            '[data-testid*="time"]',
            '[data-gs*="time"]',
        ]

        for selector in semantic_selectors:
            try:
                time_elements = await element.query_selector_all(selector)
                if len(time_elements) >= 2:
                    departure_time = await time_elements[0].inner_text()
                    arrival_time = await time_elements[-1].inner_text()
                    logger.debug(
                        f"✅ Found times via semantic selector {selector}: "
                        f"{departure_time} -> {arrival_time}"
                    )
                    return departure_time.strip(), arrival_time.strip()
            except:
                continue

        # Strategy 2: Class-based approach
        class_selectors = [".wtdjmc .eoY5cb", ".zxVSec"]
        for selector in class_selectors:
            try:
                time_elements = await element.query_selector_all(selector)
                if len(time_elements) >= 2:
                    departure_time = await time_elements[0].inner_text()
                    arrival_time = await time_elements[-1].inner_text()
                    logger.debug(
                        f"✅ Found times via class selector {selector}: "
                        f"{departure_time} -> {arrival_time}"
                    )
                    return departure_time.strip(), arrival_time.strip()
            except:
                continue

        # Strategy 3: Content-based pattern matching
        try:
            time_pattern = re.compile(r"\d{1,2}:\d{2}\s*[APap][Mm]?|\d{1,2}:\d{2}")
            all_text_elements = await element.query_selector_all("span, div")
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
                logger.debug(
                    f"✅ Found times via pattern matching: " f"{departure_time} -> {arrival_time}"
                )
                return departure_time.strip(), arrival_time.strip()

        except:
            pass

        logger.warning("⚠️ Could not extract times with any method")
        return "N/A", "N/A"
