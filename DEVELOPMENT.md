# Development Guide

This document provides comprehensive technical information for developers working on the Flight Search MCP project, including architecture details, debugging techniques, and performance optimization.

## 🏗️ Project Architecture

### System Overview

The Flight Search MCP uses a modular, component-based architecture designed for maintainability, testability, and extensibility.

```
┌─────────────────────────────────────────────────────────────┐
│                    GoogleFlightsScraper                     │
│                    (Main Orchestrator)                     │
├─────────────────────┬───────────────────┬───────────────────┤
│   BrowserManager   │   FormHandler     │   DataExtractor   │
│   - Browser setup  │   - Navigation    │   - Data parsing  │
│   - Stealth config │   - Form filling  │   - Multi-strategy│
│   - Resource mgmt  │   - Interaction   │   - Validation    │
└─────────────────────┴───────────────────┴───────────────────┘
```

### Core Components

#### 1. GoogleFlightsScraper ([`scraper.py`](flight_scraper/core/scraper.py:1))

The main orchestrator class that manages the complete scraping workflow.

**Key Responsibilities:**
- Component lifecycle management
- High-level scraping interface
- Error recovery and retries
- Health monitoring and reporting

**Public Interface:**
```python
class GoogleFlightsScraper:
    async def __aenter__(self) -> "GoogleFlightsScraper"
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None
    async def initialize(self) -> None
    async def scrape_flights(self, criteria: SearchCriteria) -> ScrapingResult
    async def cleanup(self) -> None
    def get_health_report(self) -> Dict[str, Any]
```

#### 2. BrowserManager ([`browser_manager.py`](flight_scraper/core/browser_manager.py:1))

Handles browser automation lifecycle with anti-detection capabilities.

**Features:**
- Playwright browser management
- Stealth configuration (custom user agents, disabled automation flags)
- Resource monitoring and cleanup
- Page context management

**Configuration:**
```python
BROWSER_CONFIG = {
    "headless": True,
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "stealth_mode": True,
    "timeout": 30000
}
```

#### 3. FormHandler ([`form_handler.py`](flight_scraper/core/form_handler.py:1))

Manages Google Flights navigation and form interactions.

**Capabilities:**
- Multi-strategy element location
- Dynamic form field detection
- Date picker handling
- Search execution with retries

**Selector Strategy:**
```python
# Uses RobustSelector system for resilient element detection
from flight_scraper.utils import ROBUST_SELECTORS

origin_input = ROBUST_SELECTORS["origin_input"]
# Contains multiple fallback selectors for the same element
```

#### 4. DataExtractor ([`data_extractor.py`](flight_scraper/core/data_extractor.py:1))

Extracts and parses flight data using multiple extraction strategies.

**Extraction Strategies:**
1. **Primary**: Standard flight cards
2. **Alternative**: List view format
3. **Fallback**: Generic content extraction

**Data Validation:**
- Price format validation
- Duration parsing with multiple formats
- Airline and flight number extraction
- Timestamp and metadata capture

### Data Models ([`models.py`](flight_scraper/core/models.py:1))

#### SearchCriteria
```python
@dataclass
class SearchCriteria:
    origin: str
    destination: str
    departure_date: date
    return_date: Optional[date] = None
    trip_type: TripType = TripType.ONE_WAY
    max_results: int = 10
    passengers: int = 1
```

#### FlightOffer
```python
@dataclass
class FlightOffer:
    price: str
    currency: str
    stops: int
    total_duration: str
    segments: List[FlightSegment]
    scraped_at: datetime
    booking_url: Optional[str] = None
```

#### ScrapingResult
```python
@dataclass
class ScrapingResult:
    success: bool
    flights: List[FlightOffer]
    total_results: int
    execution_time: float
    search_criteria: SearchCriteria
    error_message: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None
```

### Configuration System ([`config.py`](flight_scraper/core/config.py:1))

Hierarchical configuration with environment variables, files, and defaults.

```python
# Configuration hierarchy (highest to lowest priority):
# 1. Environment variables
# 2. Configuration file (config.json)
# 3. Default values

config = get_config(
    environment="production",
    scraper_timeout=60000,
    max_results=100
)
```

## 🔍 Component Documentation

### Robust Selector System

The scraper uses a multi-strategy selector system to handle Google Flights interface changes.

#### RobustSelector Class
```python
class RobustSelector:
    def __init__(self, selectors: List[str], description: str = "", timeout: int = 10000):
        self.selectors = selectors
        self.description = description
        self.timeout = timeout
        self.success_count = 0
        self.failure_count = 0
        self.last_successful_index = 0
```

#### Usage Pattern
```python
async def find_element_robustly(page: Page, robust_selector: RobustSelector) -> Optional[ElementHandle]:
    """Try multiple selectors until one succeeds."""
    for i, selector in enumerate(robust_selector.selectors):
        try:
            element = await page.wait_for_selector(selector, timeout=robust_selector.timeout)
            if element:
                robust_selector.success_count += 1
                robust_selector.last_successful_index = i
                return element
        except Exception as e:
            continue
    
    robust_selector.failure_count += 1
    return None
```

### Health Monitoring System

#### Health Metrics Collection
```python
def get_health_report(self) -> Dict[str, Any]:
    """Generate comprehensive health report."""
    selector_health = {}
    for name, selector in ROBUST_SELECTORS.items():
        total_attempts = selector.success_count + selector.failure_count
        success_rate = selector.success_count / total_attempts if total_attempts > 0 else 0
        selector_health[name] = {
            "success_rate": success_rate,
            "total_attempts": total_attempts,
            "last_successful_selector": selector.selectors[selector.last_successful_index]
        }
    
    return {
        "overall_health": self._calculate_overall_health(selector_health),
        "selector_health": selector_health,
        "critical_issues": self._identify_critical_issues(selector_health)
    }
```

#### Health Monitoring Usage
```python
async with GoogleFlightsScraper() as scraper:
    result = await scraper.scrape_flights(criteria)
    health = scraper.get_health_report()
    
    # Check for issues
    if health["overall_health"]["average_success_rate"] < 0.7:
        logger.warning("Low success rate detected")
        for issue in health["critical_issues"]:
            logger.error(f"Critical issue: {issue}")
```

## 🔧 Advanced Configuration

### Environment-Specific Configuration

#### Development Environment
```bash
# .env.development
FLIGHT_SCRAPER_HEADLESS=false
FLIGHT_SCRAPER_LOG_LEVEL=DEBUG
FLIGHT_SCRAPER_TIMEOUT=60000
FLIGHT_SCRAPER_ENABLE_MONITORING=true
FLIGHT_SCRAPER_SELECTOR_DIAGNOSTICS=true
```

#### Production Environment
```bash
# .env.production
FLIGHT_SCRAPER_HEADLESS=true
FLIGHT_SCRAPER_LOG_LEVEL=INFO
FLIGHT_SCRAPER_TIMEOUT=30000
FLIGHT_SCRAPER_MAX_RESULTS=50
FLIGHT_SCRAPER_ENABLE_MONITORING=true
```

### Advanced Browser Configuration

```python
ADVANCED_BROWSER_CONFIG = {
    "chromium_args": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-accelerated-2d-canvas",
        "--no-first-run",
        "--no-zygote",
        "--disable-gpu"
    ],
    "stealth_settings": {
        "user_agent_override": True,
        "webgl_vendor_override": True,
        "navigator_languages_override": ["en-US", "en"],
        "navigator_platform_override": "Win32"
    }
}
```

### Custom Selector Configuration

```python
# Add custom selectors for new Google Flights layouts
CUSTOM_SELECTORS = {
    "flight_card_new": RobustSelector([
        '[data-testid="flight-offer"]',
        '.flight-result-card',
        '[class*="flight-offer"]'
    ], "New flight card format"),
    
    "price_element_new": RobustSelector([
        '[data-testid="flight-price"]',
        '.price-display',
        '[class*="price"]'
    ], "New price element format")
}

# Merge with existing selectors
ROBUST_SELECTORS.update(CUSTOM_SELECTORS)
```

## 🐛 Debugging and Troubleshooting

### Debug Logging Configuration

```python
import logging
from loguru import logger

# Configure comprehensive debug logging
def setup_debug_logging():
    logger.remove()
    logger.add(
        "debug.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="7 days"
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level="DEBUG",
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | {message}"
    )

setup_debug_logging()
```

### Visual Debugging

```python
async def debug_scraping_with_screenshots():
    """Debug scraping with visual feedback."""
    async with GoogleFlightsScraper(headless=False) as scraper:
        # Take screenshot before search
        await scraper.browser_manager.page.screenshot(path="debug_before.png")
        
        result = await scraper.scrape_flights(criteria)
        
        # Take screenshot after search
        await scraper.browser_manager.page.screenshot(path="debug_after.png")
        
        # Highlight found elements
        flight_elements = await scraper.browser_manager.page.query_selector_all('[data-testid="flight"]')
        for i, element in enumerate(flight_elements):
            await element.evaluate('el => el.style.border = "2px solid red"')
        
        await scraper.browser_manager.page.screenshot(path="debug_highlighted.png")
```

### Selector Diagnostics

```python
async def diagnose_selector_issues():
    """Comprehensive selector diagnostics."""
    async with GoogleFlightsScraper(headless=False) as scraper:
        await scraper.initialize()
        page = scraper.browser_manager.page
        
        # Test all selectors
        for name, robust_selector in ROBUST_SELECTORS.items():
            print(f"\n🔍 Testing {name}:")
            print(f"  Description: {robust_selector.description}")
            
            for i, selector in enumerate(robust_selector.selectors):
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"  ✅ Selector {i}: {selector} - Found {len(elements)} elements")
                        # Highlight first element
                        await elements[0].evaluate('el => el.style.border = "3px solid green"')
                    else:
                        print(f"  ❌ Selector {i}: {selector} - No elements found")
                except Exception as e:
                    print(f"  ❌ Selector {i}: {selector} - Error: {e}")
            
            await asyncio.sleep(1)  # Visual delay for debugging
```

### Memory and Performance Debugging

```python
import psutil
import tracemalloc
import gc

async def profile_scraping_performance():
    """Profile memory and performance during scraping."""
    tracemalloc.start()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    async with GoogleFlightsScraper(headless=True) as scraper:
        start_time = time.time()
        
        result = await scraper.scrape_flights(criteria)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"Execution Time: {end_time - start_time:.2f}s")
        print(f"Memory Usage: {end_memory - start_memory:.1f} MB")
        print(f"Peak Memory: {peak / 1024 / 1024:.1f} MB")
        print(f"Results Found: {len(result.flights)}")
        
        # Force garbage collection and check for leaks
        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        print(f"Memory After GC: {final_memory:.1f} MB")
```

### Error Recovery Patterns

```python
class ErrorRecoveryMixin:
    """Mixin for implementing error recovery patterns."""
    
    async def execute_with_retry(self, operation, max_retries=3, delay=1.0):
        """Execute operation with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                wait_time = delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
    
    async def execute_with_fallback(self, primary_operation, fallback_operations):
        """Execute operation with fallback strategies."""
        try:
            return await primary_operation()
        except Exception as primary_error:
            logger.warning(f"Primary operation failed: {primary_error}")
            
            for i, fallback in enumerate(fallback_operations):
                try:
                    logger.info(f"Trying fallback strategy {i + 1}")
                    return await fallback()
                except Exception as fallback_error:
                    logger.warning(f"Fallback {i + 1} failed: {fallback_error}")
            
            raise Exception("All operations failed")
```

## 🚀 Performance Optimization

### Browser Optimization

```python
PERFORMANCE_BROWSER_CONFIG = {
    "headless": True,
    "args": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-accelerated-2d-canvas",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",  # Skip image loading for faster page loads
        "--disable-javascript",  # Disable JS if not needed for specific operations
        "--memory-pressure-off"
    ]
}
```

### Concurrent Processing

```python
import asyncio
from asyncio import Semaphore

async def batch_scrape_with_concurrency(search_criteria_list, max_concurrent=3):
    """Scrape multiple searches concurrently with rate limiting."""
    semaphore = Semaphore(max_concurrent)
    
    async def scrape_single(criteria):
        async with semaphore:
            async with GoogleFlightsScraper(headless=True) as scraper:
                return await scraper.scrape_flights(criteria)
    
    tasks = [scrape_single(criteria) for criteria in search_criteria_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results
```

### Memory Optimization

```python
async def memory_efficient_scraping():
    """Implement memory-efficient scraping patterns."""
    # Use context managers for automatic cleanup
    async with GoogleFlightsScraper(headless=True) as scraper:
        # Process results in batches to avoid memory buildup
        batch_size = 10
        all_results = []
        
        for i in range(0, len(search_criteria), batch_size):
            batch = search_criteria[i:i + batch_size]
            batch_results = []
            
            for criteria in batch:
                result = await scraper.scrape_flights(criteria)
                batch_results.append(result)
            
            # Process batch results immediately
            all_results.extend(process_results(batch_results))
            
            # Clear batch from memory
            del batch_results
            gc.collect()
    
    return all_results
```

### Caching Strategy

```python
from functools import lru_cache
import hashlib
import pickle
from pathlib import Path

class ResultCache:
    """Cache scraping results to reduce repeated requests."""
    
    def __init__(self, cache_dir="cache", ttl=3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = ttl
    
    def _get_cache_key(self, criteria: SearchCriteria) -> str:
        """Generate cache key from search criteria."""
        key_data = f"{criteria.origin}-{criteria.destination}-{criteria.departure_date}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, criteria: SearchCriteria) -> Optional[ScrapingResult]:
        """Get cached result if available and not expired."""
        cache_key = self._get_cache_key(criteria)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if cache_file.exists():
            stat = cache_file.stat()
            if time.time() - stat.st_mtime < self.ttl:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        
        return None
    
    def set(self, criteria: SearchCriteria, result: ScrapingResult):
        """Cache scraping result."""
        cache_key = self._get_cache_key(criteria)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)

# Usage
cache = ResultCache()

async def scrape_with_cache(criteria: SearchCriteria) -> ScrapingResult:
    # Check cache first
    cached_result = cache.get(criteria)
    if cached_result:
        logger.info("Using cached result")
        return cached_result
    
    # Scrape if not cached
    async with GoogleFlightsScraper(headless=True) as scraper:
        result = await scraper.scrape_flights(criteria)
        cache.set(criteria, result)
        return result
```

## 🔄 Testing and Quality Assurance

### Custom Test Fixtures

```python
# tests/conftest.py
import pytest
from flight_scraper.core import GoogleFlightsScraper, SearchCriteria
from datetime import date, timedelta

@pytest.fixture
async def scraper():
    """Provide initialized scraper for tests."""
    scraper = GoogleFlightsScraper(headless=True)
    await scraper.initialize()
    yield scraper
    await scraper.cleanup()

@pytest.fixture
def sample_criteria():
    """Provide sample search criteria for tests."""
    return SearchCriteria(
        origin="NYC",
        destination="LAX",
        departure_date=date.today() + timedelta(days=30),
        max_results=5
    )

@pytest.fixture
def mock_flight_data():
    """Provide mock flight data for unit tests."""
    return [
        {
            "price": "$299",
            "airline": "American Airlines",
            "duration": "5h 30m",
            "stops": 0
        }
    ]
```

### Integration Test Patterns

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_scraping_workflow(scraper, sample_criteria):
    """Test complete scraping workflow."""
    result = await scraper.scrape_flights(sample_criteria)
    
    # Verify result structure
    assert isinstance(result, ScrapingResult)
    assert result.success is not None
    assert isinstance(result.flights, list)
    assert result.execution_time > 0
    
    # Verify health reporting
    health = scraper.get_health_report()
    assert "overall_health" in health
    assert "selector_health" in health

@pytest.mark.browser
@pytest.mark.slow
async def test_selector_resilience():
    """Test selector system resilience."""
    async with GoogleFlightsScraper(headless=True) as scraper:
        # Test each selector independently
        for name, robust_selector in ROBUST_SELECTORS.items():
            success = False
            for selector in robust_selector.selectors:
                try:
                    element = await scraper.browser_manager.page.query_selector(selector)
                    if element:
                        success = True
                        break
                except:
                    continue
            
            # At least one selector should work
            if name in ["origin_input", "destination_input"]:  # Critical selectors
                assert success, f"Critical selector {name} failed completely"
```

### Performance Testing

```python
@pytest.mark.performance
async def test_memory_usage():
    """Test memory usage stays within acceptable limits."""
    import psutil
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024
    
    async with GoogleFlightsScraper(headless=True) as scraper:
        for _ in range(5):  # Multiple searches
            result = await scraper.scrape_flights(sample_criteria)
            current_memory = process.memory_info().rss / 1024 / 1024
            
            # Memory should not grow excessively
            assert current_memory - initial_memory < 100, "Memory usage exceeded 100MB"

@pytest.mark.performance
async def test_execution_time():
    """Test execution time stays within acceptable limits."""
    async with GoogleFlightsScraper(headless=True) as scraper:
        start_time = time.time()
        result = await scraper.scrape_flights(sample_criteria)
        execution_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert execution_time < 60, f"Execution took {execution_time:.2f}s, expected < 60s"
```

## 📊 Monitoring and Observability

### Metrics Collection

```python
import time
from dataclasses import dataclass
from typing import Dict, List
from collections import defaultdict

@dataclass
class OperationMetric:
    operation_name: str
    duration: float
    success: bool
    timestamp: float
    metadata: Dict[str, Any] = None

class MetricsCollector:
    """Collect and analyze scraping metrics."""
    
    def __init__(self):
        self.metrics: List[OperationMetric] = []
        self.counters = defaultdict(int)
    
    def record_operation(self, operation_name: str, duration: float, success: bool, **metadata):
        """Record operation metrics."""
        metric = OperationMetric(
            operation_name=operation_name,
            duration=duration,
            success=success,
            timestamp=time.time(),
            metadata=metadata
        )
        self.metrics.append(metric)
        self.counters[f"{operation_name}_total"] += 1
        if success:
            self.counters[f"{operation_name}_success"] += 1
    
    def get_summary(self, hours=24) -> Dict[str, Any]:
        """Get metrics summary for the last N hours."""
        cutoff = time.time() - (hours * 3600)
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff]
        
        summary = {
            "total_operations": len(recent_metrics),
            "success_rate": sum(1 for m in recent_metrics if m.success) / len(recent_metrics) if recent_metrics else 0,
            "average_duration": sum(m.duration for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0,
            "operations_by_type": defaultdict(int)
        }
        
        for metric in recent_metrics:
            summary["operations_by_type"][metric.operation_name] += 1
        
        return summary

# Global metrics collector
metrics_collector = MetricsCollector()

# Usage in scraper
async def scrape_with_metrics(criteria: SearchCriteria) -> ScrapingResult:
    start_time = time.time()
    try:
        async with GoogleFlightsScraper(headless=True) as scraper:
            result = await scraper.scrape_flights(criteria)
            
            metrics_collector.record_operation(
                "flight_search",
                time.time() - start_time,
                result.success,
                origin=criteria.origin,
                destination=criteria.destination,
                flights_found=len(result.flights)
            )
            
            return result
    except Exception as e:
        metrics_collector.record_operation(
            "flight_search",
            time.time() - start_time,
            False,
            error=str(e)
        )
        raise
```

### Health Check Endpoints

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    try:
        # Quick test of core functionality
        criteria = SearchCriteria(
            origin="NYC",
            destination="LAX",
            departure_date=date.today() + timedelta(days=30),
            max_results=1
        )
        
        async with GoogleFlightsScraper(headless=True) as scraper:
            result = await scraper.scrape_flights(criteria)
            health = scraper.get_health_report()
        
        return {
            "status": "healthy",
            "last_search_success": result.success,
            "selector_health": health["overall_health"]["average_success_rate"],
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/metrics")
async def get_metrics():
    """Get scraping metrics."""
    return metrics_collector.get_summary()
```

## 🔐 Security and Best Practices

### Security Considerations

```python
# Secure configuration management
import os
from cryptography.fernet import Fernet

class SecureConfig:
    """Manage sensitive configuration securely."""
    
    def __init__(self):
        self.encryption_key = os.environ.get('ENCRYPTION_KEY')
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt sensitive configuration value."""
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive configuration value."""
        return self.cipher.decrypt(encrypted_value.encode()).decode()

# Rate limiting implementation
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    """Implement rate limiting for scraping requests."""
    
    def __init__(self, max_requests: int = 60, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def acquire(self):
        """Acquire permission to make a request."""
        now = datetime.now()
        
        # Remove old requests outside time window
        cutoff = now - timedelta(seconds=self.time_window)
        self.requests = [req_time for req_time in self.requests if req_time > cutoff]
        
        if len(self.requests) >= self.max_requests:
            wait_time = (self.requests[0] + timedelta(seconds=self.time_window) - now).total_seconds()
            await asyncio.sleep(wait_time)
        
        self.requests.append(now)

# Usage
rate_limiter = RateLimiter(max_requests=30, time_window=3600)

async def rate_limited_scraping(criteria: SearchCriteria):
    await rate_limiter.acquire()
    
    async with GoogleFlightsScraper(headless=True) as scraper:
        return await scraper.scrape_flights(criteria)
```

---

This comprehensive development guide provides the technical depth needed for advanced development, debugging, and optimization of the Flight Search MCP. For basic usage and contribution guidelines, refer to [README.md](README.md) and [CONTRIBUTING.md](CONTRIBUTING.md).