"""Browser lifecycle management for flight scraping."""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Playwright
from loguru import logger

from .config import SCRAPER_CONFIG
from .models import ScrapingError


class BrowserManager:
    """
    Manages browser lifecycle, initialization, and cleanup for flight scraping.
    
    This class encapsulates all browser-related operations including launching browsers,
    creating contexts with stealth settings, and proper resource cleanup.
    
    Attributes:
        headless (bool): Whether to run browser in headless mode
        browser (Optional[Browser]): The Playwright browser instance
        context (Optional[BrowserContext]): The browser context with stealth settings
        page (Optional[Page]): The active page for scraping
        playwright (Optional[Playwright]): The Playwright instance
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize the BrowserManager.
        
        Args:
            headless (bool): Whether to run the browser in headless mode. 
                           Defaults to False for debugging purposes.
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright: Optional[Playwright] = None
        
    async def __aenter__(self):
        """
        Async context manager entry.
        
        Returns:
            BrowserManager: The initialized browser manager instance
            
        Raises:
            ScrapingError: If browser initialization fails
        """
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit with proper cleanup.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred  
            exc_tb: Exception traceback if an exception occurred
        """
        await self.cleanup()
        
    async def initialize(self) -> None:
        """
        Initialize the browser, context, and page with stealth settings.
        
        Sets up a Chromium browser with anti-detection measures including:
        - Custom user agent to appear as a regular browser
        - Disabled automation flags
        - Stealth JavaScript injection
        - Proper viewport configuration
        
        Raises:
            ScrapingError: If any step of browser initialization fails
        """
        try:
            logger.info("Initializing browser with stealth settings...")
            
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser with anti-detection args
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with realistic user agent and viewport
            self.context = await self.browser.new_context(
                user_agent=SCRAPER_CONFIG["user_agent"],
                viewport=SCRAPER_CONFIG["viewport"]
            )
            
            # Add stealth JavaScript to hide automation indicators
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Create page with configured timeouts
            self.page = await self.context.new_page()
            self.page.set_default_timeout(SCRAPER_CONFIG["timeout"])
            self.page.set_default_navigation_timeout(SCRAPER_CONFIG["navigation_timeout"])
            
            logger.info("✅ Browser initialized successfully with stealth settings")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize browser: {str(e)}")
            await self.cleanup()  # Clean up any partial initialization
            raise ScrapingError(f"Browser initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """
        Clean up all browser resources in proper order.
        
        Performs cleanup in the correct sequence:
        1. Close browser context (which closes all pages)
        2. Close browser instance
        3. Stop Playwright
        
        This method is safe to call multiple times and handles partial cleanup scenarios.
        """
        try:
            logger.info("🧹 Starting browser cleanup...")
            
            if self.context:
                await self.context.close()
                logger.debug("✅ Browser context closed")
                
            if self.browser:
                await self.browser.close()
                logger.debug("✅ Browser closed")
                
            if self.playwright:
                await self.playwright.stop()
                logger.debug("✅ Playwright stopped")
                
            logger.info("✅ Browser cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"⚠️ Error during browser cleanup: {str(e)}")
    
    def get_page(self) -> Page:
        """
        Get the active page instance.
        
        Returns:
            Page: The active Playwright page instance
            
        Raises:
            ScrapingError: If browser is not initialized or page is not available
        """
        if not self.page:
            raise ScrapingError("Browser not initialized. Call initialize() first.")
        return self.page
    
    def is_initialized(self) -> bool:
        """
        Check if the browser is properly initialized.
        
        Returns:
            bool: True if browser, context, and page are all initialized
        """
        return all([self.browser, self.context, self.page])