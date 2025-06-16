#!/usr/bin/env python3
"""Diagnostic test script for robust selector fixes."""

import asyncio
from datetime import date, timedelta
from flight_scraper.core.scraper import GoogleFlightsScraper
from flight_scraper.core.models import SearchCriteria, TripType
from flight_scraper.utils import setup_logging, ROBUST_SELECTOR_CONFIGS

async def test_selector_diagnostics():
    """Test specific selector configurations and functionality."""
    
    setup_logging()
    
    print("🔧 ROBUST SELECTOR DIAGNOSTICS")
    print("=" * 50)
    
    # Test 1: Verify selector configuration fixes
    print("1️⃣ Testing Search Button Configuration:")
    search_config = ROBUST_SELECTOR_CONFIGS.get("search_button", {})
    
    print(f"   Semantic selectors: {search_config.get('semantic', [])}")
    print(f"   Structural selectors: {search_config.get('structural', [])}")
    print(f"   Content-based selectors: {search_config.get('content_based', [])}")
    
    # Check for problematic "Explore" selectors
    all_search_selectors = []
    for strategy_selectors in search_config.values():
        all_search_selectors.extend(strategy_selectors)
    
    explore_selectors = [s for s in all_search_selectors if "Explore" in s]
    if explore_selectors:
        print(f"   ❌ PROBLEM: Found 'Explore' selectors: {explore_selectors}")
    else:
        print(f"   ✅ FIXED: No 'Explore' selectors found")
    
    print("\n2️⃣ Testing Limited Scraper Run:")
    
    # Create minimal test criteria
    departure_date = date.today() + timedelta(days=30)
    criteria = SearchCriteria(
        origin="LAX",
        destination="JFK", 
        departure_date=departure_date,
        trip_type=TripType.ONE_WAY,  # Simplified to one-way
        max_results=5
    )
    
    print(f"   Search: {criteria.origin} → {criteria.destination}")
    print(f"   Date: {criteria.departure_date}")
    
    # Test with visible browser for debugging
    async with GoogleFlightsScraper(headless=False) as scraper:
        try:
            print("\n3️⃣ Testing Form Fill Process:")
            
            # Navigate
            await scraper.navigate_to_google_flights(criteria)
            print("   ✅ Navigation successful")
            
            # Test form filling step by step
            await scraper.fill_search_form(criteria)
            print("   ✅ Form filling successful")
            
            # Test search trigger with detailed logging
            print("\n4️⃣ Testing Search Button Detection:")
            
            # Before clicking, let's see what buttons are available
            buttons_info = await scraper.page.evaluate('''
            () => {
                const buttons = document.querySelectorAll('button');
                return Array.from(buttons).map(btn => ({
                    text: btn.innerText.substring(0, 20),
                    ariaLabel: btn.getAttribute('aria-label'),
                    type: btn.type,
                    visible: btn.offsetParent !== null
                })).filter(btn => btn.visible && btn.text);
            }
            ''')
            
            print(f"   Available buttons:")
            for i, btn in enumerate(buttons_info[:10]):  # Show first 10
                print(f"     {i+1}. Text: '{btn['text']}', Aria: '{btn['ariaLabel']}', Type: '{btn['type']}'")
            
            # Now try the search trigger
            await scraper.trigger_search()
            
            # Check URL after search attempt
            current_url = scraper.page.url
            print(f"\n5️⃣ Post-Search Analysis:")
            print(f"   Current URL: {current_url}")
            
            if "search?" in current_url:
                print("   ✅ SUCCESS: URL contains 'search?' - correct navigation")
            elif "explore?" in current_url:
                print("   ❌ PROBLEM: URL contains 'explore?' - wrong button clicked")
            else:
                print("   ⚠️ UNCLEAR: URL doesn't match expected patterns")
            
            print(f"\n📊 Health Report:")
            health_report = scraper.health_monitor.get_health_report()
            overall_health = health_report.get('overall_health', {})
            print(f"   Success Rate: {overall_health.get('average_success_rate', 0):.1%}")
            
            critical_issues = health_report.get('critical_issues', [])
            if critical_issues:
                print(f"   Critical Issues: {len(critical_issues)}")
                for issue in critical_issues:
                    print(f"     - {issue}")
            else:
                print("   ✅ No critical issues detected")
                
        except Exception as e:
            print(f"   ❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    """Run diagnostic tests."""
    print("🧪 Running Robust Selector Diagnostics")
    print("This will test the fixes for:")  
    print("• Search button selector configuration")
    print("• Form filling robustness")
    print("• Navigation accuracy")
    print("• Health monitoring functionality")
    print()
    
    asyncio.run(test_selector_diagnostics())

if __name__ == "__main__":
    main()