"""Refactored Google Flights web scraper implementation."""

import time
from datetime import date
from typing import List, Optional, Dict, Any
from loguru import logger

from .config import SCRAPER_CONFIG
from .models import (
    SearchCriteria, FlightOffer, ScrapingResult, TripType, ScrapingError
)
from .browser_manager import BrowserManager
from .form_handler import FormHandler
from .data_extractor import DataExtractor
from ..utils import SelectorHealthMonitor


class GoogleFlightsScraper:
    """
    Main Google Flights web scraper using modular component architecture.
    
    This refactored scraper delegates responsibilities to specialized components:
    - BrowserManager: Handles browser lifecycle and stealth configuration
    - FormHandler: Manages navigation and form interactions
    - DataExtractor: Extracts and processes flight data
    
    The scraper coordinates these components to provide a clean, maintainable
    interface for flight data collection with comprehensive error handling
    and health monitoring.
    
    Attributes:
        headless (bool): Whether to run browser in headless mode
        browser_manager (Optional[BrowserManager]): Browser lifecycle manager
        form_handler (Optional[FormHandler]): Form interaction handler
        data_extractor (Optional[DataExtractor]): Flight data extractor
        health_monitor (SelectorHealthMonitor): Selector health monitoring system
        selector_monitors (Dict[str, Any]): Session-specific selector monitoring data
    
    Example:
        >>> async with GoogleFlightsScraper(headless=True) as scraper:
        ...     criteria = SearchCriteria(
        ...         origin="NYC",
        ...         destination="LAX", 
        ...         departure_date=date(2024, 6, 15)
        ...     )
        ...     result = await scraper.scrape_flights(criteria)
        ...     print(f"Found {len(result.flights)} flights")
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize the GoogleFlightsScraper with component architecture.
        
        Args:
            headless (bool): Whether to run the browser in headless mode.
                           Defaults to False for easier debugging and development.
                           Set to True for production or automated environments.
        """
        self.headless = headless
        self.browser_manager: Optional[BrowserManager] = None
        self.form_handler: Optional[FormHandler] = None
        self.data_extractor: Optional[DataExtractor] = None
        self.health_monitor = SelectorHealthMonitor()
        self.selector_monitors: Dict[str, Any] = {}
        
    async def __aenter__(self):
        """
        Async context manager entry point.
        
        Initializes all components and establishes browser session.
        
        Returns:
            GoogleFlightsScraper: The fully initialized scraper instance
            
        Raises:
            ScrapingError: If component initialization fails
        """
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit point.
        
        Ensures proper cleanup of all components and browser resources.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        await self.cleanup()
        
    async def initialize(self) -> None:
        """
        Initialize all scraper components in the correct order.
        
        Sets up the component architecture:
        1. BrowserManager - Establishes browser session with stealth settings
        2. FormHandler - Prepares form interaction capabilities
        3. DataExtractor - Configures data extraction strategies
        
        This method ensures all components are properly initialized and
        ready for coordinated scraping operations.
        
        Raises:
            ScrapingError: If any component fails to initialize properly
        """
        try:
            logger.info("🚀 Initializing Google Flights scraper components...")
            
            # Initialize browser manager with stealth settings
            self.browser_manager = BrowserManager(headless=self.headless)
            await self.browser_manager.initialize()
            
            # Get the initialized page for other components
            page = self.browser_manager.get_page()
            
            # Initialize form handler with page reference
            self.form_handler = FormHandler(page)
            
            # Initialize data extractor with page reference
            self.data_extractor = DataExtractor(page)
            
            logger.info("✅ All scraper components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize scraper components: {str(e)}")
            await self.cleanup()  # Clean up any partial initialization
            raise ScrapingError(f"Scraper initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """
        Clean up all scraper components and resources.
        
        Performs cleanup in reverse order of initialization to ensure
        proper resource deallocation. This method is safe to call
        multiple times and handles partial cleanup scenarios.
        """
        try:
            logger.info("🧹 Starting scraper cleanup...")
            
            # Clear component references
            self.data_extractor = None
            self.form_handler = None
            
            # Clean up browser manager (handles browser resources)
            if self.browser_manager:
                await self.browser_manager.cleanup()
                self.browser_manager = None
                
            logger.info("✅ Scraper cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"⚠️ Error during scraper cleanup: {str(e)}")
    
    async def scrape_flights(self, criteria: SearchCriteria) -> ScrapingResult:
        """
        Main method to scrape flights based on search criteria.
        
        Orchestrates the complete flight scraping process using the component
        architecture. This method coordinates all phases of scraping:
        
        1. Navigation to Google Flights with appropriate URL
        2. Form filling with robust selector strategies
        3. Search execution with multiple fallback methods
        4. Data extraction with comprehensive error handling
        5. Health monitoring and performance tracking
        
        Args:
            criteria (SearchCriteria): Complete search parameters including:
                - origin: Origin airport code or city name
                - destination: Destination airport code or city name
                - departure_date: Departure date
                - return_date: Return date for round-trip (optional)
                - trip_type: ONE_WAY or ROUND_TRIP
                - max_results: Maximum number of results to return
                
        Returns:
            ScrapingResult: Comprehensive scraping results containing:
                - search_criteria: Original search parameters
                - flights: List of extracted flight offers
                - total_results: Number of flights found
                - success: Whether scraping completed successfully
                - error_message: Error details if scraping failed
                - execution_time: Total time taken for scraping
                - scraped_at: Timestamp of scraping operation
                
        Raises:
            ScrapingError: If scraper components are not initialized
            
        Example:
            >>> criteria = SearchCriteria(
            ...     origin="JFK",
            ...     destination="LAX",
            ...     departure_date=date(2024, 7, 1),
            ...     return_date=date(2024, 7, 8),
            ...     trip_type=TripType.ROUND_TRIP,
            ...     max_results=25
            ... )
            >>> result = await scraper.scrape_flights(criteria)
            >>> print(f"Success: {result.success}")
            >>> print(f"Found {result.total_results} flights")
            >>> for flight in result.flights:
            ...     print(f"  {flight.price} - {flight.segments[0].airline}")
        """
        start_time = time.time()
        
        # Validate component initialization
        if not all([self.browser_manager, self.form_handler, self.data_extractor]):
            raise ScrapingError("Scraper components not initialized. Call initialize() first.")
        
        try:
            logger.info(f"🚀 Starting flight scraping: {criteria.origin} → {criteria.destination}")
            logger.info(f"📅 Departure: {criteria.departure_date}" + 
                       (f", Return: {criteria.return_date}" if criteria.return_date else ""))
            
            # Initialize selector monitoring for this session
            self.selector_monitors = {}
            
            # Phase 1: Navigate to Google Flights
            logger.info("📍 Phase 1: Navigation")
            await self.form_handler.navigate_to_google_flights(criteria)
            
            # Phase 2: Fill search form
            logger.info("📝 Phase 2: Form Filling")
            await self.form_handler.fill_search_form(criteria)
            
            # Phase 3: Trigger search
            logger.info("🔍 Phase 3: Search Execution")
            await self.form_handler.trigger_search()
            
            # Phase 4: Extract flight data
            logger.info("📊 Phase 4: Data Extraction")
            flights = await self.data_extractor.extract_flight_data(criteria, criteria.max_results)
            
            execution_time = time.time() - start_time
            
            # Phase 5: Health monitoring and reporting
            await self._record_session_health("flight_search_page")
            health_report = self.health_monitor.get_health_report()
            logger.info(f"📊 Selector health report: {health_report.get('overall_health', {})}")
            
            # Create successful result
            result = ScrapingResult(
                search_criteria=criteria,
                flights=flights,
                total_results=len(flights),
                success=True,
                execution_time=execution_time
            )
            
            logger.info(f"✅ Scraping completed successfully!")
            logger.info(f"📊 Results: {len(flights)} flights found in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Scraping failed after {execution_time:.2f}s: {str(e)}")
            
            # Record health data even on failure for analysis
            try:
                await self._record_session_health("flight_search_page_failed")
            except:
                pass
            
            # Create failure result
            return ScrapingResult(
                search_criteria=criteria,
                flights=[],
                total_results=0,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _record_session_health(self, page_type: str) -> None:
        """
        Record selector health data for the current scraping session.
        
        Collects performance and reliability metrics from the robust selector
        system to help identify when Google Flights changes require selector
        updates or when new strategies need to be implemented.
        
        Args:
            page_type (str): Type of page being scraped (e.g., "flight_search_page")
                           Used for categorizing health metrics and identifying
                           page-specific selector performance patterns.
        """
        try:
            # In a full implementation, this would collect detailed monitoring data
            # from RobustSelector instances used during the session
            
            # For now, create a basic health record
            monitor_data = {}
            
            # Record the session with health monitor
            self.health_monitor.record_page_health(page_type, monitor_data)
            
            logger.debug(f"📈 Recorded selector health data for {page_type}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to record selector health: {str(e)}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report for selector performance.
        
        Provides detailed insights into selector health across scraping sessions,
        including success rates, failure patterns, and recommendations for
        improving scraping reliability.
        
        Returns:
            Dict[str, Any]: Comprehensive health report containing:
                - timestamp: When the report was generated
                - pages_monitored: Number of different page types monitored
                - overall_health: Aggregate health metrics
                - critical_issues: List of critical problems requiring attention
                - recommendations: Suggested actions for improving reliability
                
        Example:
            >>> report = scraper.get_health_report()
            >>> print(f"Overall success rate: {report['overall_health']['average_success_rate']:.1%}")
            >>> if report['critical_issues']:
            ...     print("Critical issues found:")
            ...     for issue in report['critical_issues']:
            ...         print(f"  - {issue}")
        """
        return self.health_monitor.get_health_report()


async def scrape_flights_async(
    origin: str,
    destination: str,
    departure_date: date,
    return_date: Optional[date] = None,
    max_results: int = 50,
    headless: bool = False
) -> ScrapingResult:
    """
    Convenience function to scrape flights asynchronously with simple parameters.
    
    This function provides a streamlined interface for flight scraping without
    requiring manual setup of SearchCriteria or scraper components. It handles
    all initialization and cleanup automatically.
    
    Args:
        origin (str): Origin airport code (e.g., "JFK", "NYC") or city name
        destination (str): Destination airport code (e.g., "LAX", "Los Angeles") or city name
        departure_date (date): Date of departure flight
        return_date (Optional[date]): Date of return flight for round-trip searches.
                                    If None, performs one-way search.
        max_results (int): Maximum number of flight results to return.
                          Defaults to 50. Range: 1-100 recommended.
        headless (bool): Whether to run browser in headless mode.
                        Defaults to False for debugging ease.
                        
    Returns:
        ScrapingResult: Complete scraping results with flight data and metadata
        
    Raises:
        ScrapingError: If scraping fails due to initialization or execution errors
        
    Example:
        >>> from datetime import date
        >>> result = await scrape_flights_async(
        ...     origin="NYC",
        ...     destination="SF",
        ...     departure_date=date(2024, 8, 15),
        ...     return_date=date(2024, 8, 22),
        ...     max_results=25,
        ...     headless=True
        ... )
        >>> if result.success:
        ...     print(f"Found {len(result.flights)} flights")
        ...     cheapest = min(result.flights, key=lambda f: float(f.price.replace('$', '').replace(',', '')))
        ...     print(f"Cheapest: {cheapest.price} on {cheapest.segments[0].airline}")
        ... else:
        ...     print(f"Scraping failed: {result.error_message}")
    """
    
    # Create search criteria from parameters
    criteria = SearchCriteria(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        trip_type=TripType.ROUND_TRIP if return_date else TripType.ONE_WAY,
        max_results=max_results
    )
    
    logger.info(f"🎯 Created search criteria: {criteria.model_dump()}")
    
    # Execute scraping with automatic cleanup
    async with GoogleFlightsScraper(headless=headless) as scraper:
        return await scraper.scrape_flights(criteria)
