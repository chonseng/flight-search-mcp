"""Data models for flight information."""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TripType(str, Enum):
    """Flight trip type enumeration."""
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


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