"""Data models for flight information."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TripType(str, Enum):
    """Flight trip type enumeration."""
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


class SelectorFailureType(str, Enum):
    """Types of selector failures."""
    NOT_FOUND = "not_found"
    UNINTERACTABLE = "uninteractable"
    STRUCTURE_CHANGED = "structure_changed"
    TIMING_ISSUE = "timing_issue"
    STALE_ELEMENT = "stale_element"
    PERMISSION_DENIED = "permission_denied"


class SelectorStrategy(str, Enum):
    """Selector identification strategies."""
    SEMANTIC = "semantic"  # roles, aria-labels, data attributes
    STRUCTURAL = "structural"  # tag combinations, position-based
    CLASS_BASED = "class_based"  # CSS classes (current approach)
    CONTENT_BASED = "content_based"  # text matching, pattern recognition


class SelectorAttempt(BaseModel):
    """Record of a selector attempt."""
    selector: str = Field(..., description="The selector that was attempted")
    strategy: SelectorStrategy = Field(..., description="Strategy used for this selector")
    success: bool = Field(..., description="Whether the attempt succeeded")
    failure_type: Optional[SelectorFailureType] = Field(None, description="Type of failure if unsuccessful")
    error_message: Optional[str] = Field(None, description="Detailed error message")
    dom_context: Optional[str] = Field(None, description="Surrounding DOM context for debugging")
    execution_time: float = Field(..., description="Time taken for this attempt in seconds")
    attempted_at: datetime = Field(default_factory=datetime.now, description="When this attempt occurred")


class SelectorMonitoring(BaseModel):
    """Comprehensive selector monitoring data."""
    element_type: str = Field(..., description="Type of element being selected (e.g., 'origin_input', 'search_button')")
    attempts: List[SelectorAttempt] = Field(default_factory=list, description="All selector attempts made")
    successful_selector: Optional[str] = Field(None, description="The selector that ultimately succeeded")
    successful_strategy: Optional[SelectorStrategy] = Field(None, description="Strategy that succeeded")
    total_attempts: int = Field(default=0, description="Total number of attempts made")
    total_time: float = Field(default=0.0, description="Total time spent on selector attempts")
    final_success: bool = Field(default=False, description="Whether any selector ultimately succeeded")


class PageSelectorHealth(BaseModel):
    """Overall health of selectors on a page."""
    page_type: str = Field(..., description="Type of page being scraped")
    selector_monitoring: Dict[str, SelectorMonitoring] = Field(default_factory=dict, description="Monitoring for each element type")
    overall_success_rate: float = Field(default=0.0, description="Overall success rate across all selectors")
    critical_failures: List[str] = Field(default_factory=list, description="Critical selector failures")
    page_structure_changed: bool = Field(default=False, description="Whether page structure appears to have changed")
    scraping_timestamp: datetime = Field(default_factory=datetime.now, description="When this page was scraped")


class FlightSegment(BaseModel):
    """Individual flight segment information."""
    airline: str = Field(..., description="Airline name")
    flight_number: Optional[str] = Field(None, description="Flight number")
    departure_airport: str = Field(..., description="Departure airport code")
    arrival_airport: str = Field(..., description="Arrival airport code")
    departure_time: str = Field(..., description="Departure time")
    arrival_time: str = Field(..., description="Arrival time")
    duration: str = Field(..., description="Flight duration")
    aircraft: Optional[str] = Field(None, description="Aircraft type")


class FlightOffer(BaseModel):
    """Complete flight offer information."""
    price: str = Field(..., description="Total price")
    currency: str = Field(default="USD", description="Price currency")
    stops: int = Field(..., description="Number of stops")
    total_duration: str = Field(..., description="Total travel duration")
    segments: List[FlightSegment] = Field(..., description="Flight segments")
    booking_link: Optional[str] = Field(None, description="Booking URL")
    scraped_at: datetime = Field(default_factory=datetime.now, description="When this data was scraped")


class SearchCriteria(BaseModel):
    """Flight search parameters."""
    origin: str = Field(..., description="Origin airport code or city")
    destination: str = Field(..., description="Destination airport code or city")
    departure_date: date = Field(..., description="Departure date")
    return_date: Optional[date] = Field(None, description="Return date for round-trip")
    trip_type: TripType = Field(default=TripType.ONE_WAY, description="Type of trip")
    max_results: int = Field(default=50, description="Maximum number of results to return")


class ScrapingResult(BaseModel):
    """Complete scraping operation result."""
    search_criteria: SearchCriteria = Field(..., description="Original search parameters")
    flights: List[FlightOffer] = Field(..., description="Found flight offers")
    total_results: int = Field(..., description="Total number of results found")
    success: bool = Field(..., description="Whether scraping was successful")
    error_message: Optional[str] = Field(None, description="Error message if scraping failed")
    scraped_at: datetime = Field(default_factory=datetime.now, description="Scraping timestamp")
    execution_time: float = Field(..., description="Time taken to complete scraping (seconds)")


class ScrapingError(Exception):
    """Custom exception for scraping errors."""
    pass


class NavigationError(ScrapingError):
    """Exception for navigation-related errors."""
    pass


class ElementNotFoundError(ScrapingError):
    """Exception for when required elements are not found."""
    pass


class TimeoutError(ScrapingError):
    """Exception for timeout-related errors."""
    pass


class SelectorFailureAlert(BaseModel):
    """Alert for selector failures requiring attention."""
    alert_id: str = Field(..., description="Unique identifier for this alert")
    severity: str = Field(..., description="Alert severity: critical, warning, info")
    element_type: str = Field(..., description="Type of element that failed")
    failure_patterns: List[str] = Field(..., description="Patterns observed in failures")
    recommended_actions: List[str] = Field(..., description="Recommended actions to resolve")
    failure_count: int = Field(..., description="Number of consecutive failures")
    first_failure: datetime = Field(..., description="When failures started")
    last_failure: datetime = Field(..., description="Most recent failure")
    dom_changes_detected: bool = Field(default=False, description="Whether DOM changes were detected")