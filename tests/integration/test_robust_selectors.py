#!/usr/bin/env python3
"""Integration test script for the robust selector system."""

import asyncio
from datetime import date, timedelta
from flight_scraper.core.scraper import GoogleFlightsScraper
from flight_scraper.core.models import SearchCriteria, TripType
from flight_scraper.utils import setup_logging

async def test_robust_selectors():
    """Test the robust selector system with a sample flight search."""
    
    # Setup logging
    setup_logging()
    
    print("🚀 Testing Robust Selector System")
    print("=" * 50)
    
    # Create test search criteria
    departure_date = date.today() + timedelta(days=30)
    return_date = departure_date + timedelta(days=7)
    
    criteria = SearchCriteria(
        origin="LAX",
        destination="JFK", 
        departure_date=departure_date,
        return_date=return_date,
        trip_type=TripType.ROUND_TRIP,
        max_results=10
    )
    
    print(f"📋 Search Criteria:")
    print(f"   Origin: {criteria.origin}")
    print(f"   Destination: {criteria.destination}")
    print(f"   Departure: {criteria.departure_date}")
    print(f"   Return: {criteria.return_date}")
    print(f"   Trip Type: {criteria.trip_type}")
    print()
    
    # Test the scraper with robust selectors
    async with GoogleFlightsScraper(headless=False) as scraper:
        print("🔍 Starting flight search with robust selectors...")
        
        try:
            result = await scraper.scrape_flights(criteria)
            
            print("\n📊 SCRAPING RESULTS")
            print("=" * 30)
            print(f"✅ Success: {result.success}")
            print(f"⏱️  Execution Time: {result.execution_time:.2f}s")
            print(f"🎯 Flights Found: {result.total_results}")
            
            if result.success and result.flights:
                print(f"\n🛫 First 3 Flight Results:")
                for i, flight in enumerate(result.flights[:3], 1):
                    print(f"   {i}. {flight.price} - {flight.segments[0].airline}")
                    print(f"      {flight.segments[0].departure_time} → {flight.segments[0].arrival_time}")
                    print(f"      Duration: {flight.total_duration}, Stops: {flight.stops}")
                    print()
            
            # Display selector health information
            print("🔧 SELECTOR HEALTH MONITORING")
            print("=" * 35)
            health_report = scraper.health_monitor.get_health_report()
            
            if health_report.get('overall_health'):
                oh = health_report['overall_health']
                print(f"📈 Average Success Rate: {oh.get('average_success_rate', 0):.1%}")
                print(f"📉 Worst Success Rate: {oh.get('worst_success_rate', 0):.1%}")
                print(f"📈 Best Success Rate: {oh.get('best_success_rate', 0):.1%}")
            
            if health_report.get('critical_issues'):
                print(f"🚨 Critical Issues: {len(health_report['critical_issues'])}")
                for issue in health_report['critical_issues']:
                    print(f"   - {issue}")
            
            if health_report.get('recommendations'):
                print(f"💡 Recommendations:")
                for rec in health_report['recommendations']:
                    print(f"   - {rec}")
            
            if result.error_message:
                print(f"\n❌ Error: {result.error_message}")
                
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    """Run the test."""
    print("🧪 Robust Selector System Integration Test")
    print("This test will demonstrate:")
    print("• Hierarchical selector strategies (semantic → structural → class-based → content-based)")
    print("• Intelligent fallback systems")
    print("• Selector failure detection and monitoring") 
    print("• Health reporting and alerting")
    print()
    
    asyncio.run(test_robust_selectors())

if __name__ == "__main__":
    main()