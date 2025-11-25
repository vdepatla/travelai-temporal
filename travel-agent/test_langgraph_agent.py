"""
Simple test to verify the LangGraph travel agent works correctly
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.travel_models import TravelRequest
from agents.travel_agent import LangGraphTravelAgent


async def test_basic_functionality():
    """Test basic travel agent functionality"""
    print("🧪 Testing LangGraph Travel Agent...")
    
    try:
        # Initialize agent
        agent = LangGraphTravelAgent(use_postgres=False)
        print("✅ Agent initialized successfully")
        
        # Create test request
        request = TravelRequest(
            destination="Tokyo, Japan",
            start_date="2025-06-01",
            end_date="2025-06-07", 
            number_of_travelers=2
        )
        print("✅ Test request created")
        
        # Run the workflow
        print("🔄 Running travel planning workflow...")
        result = await agent.run(request, thread_id="test-trip")
        
        # Check results
        if result["success"]:
            print("✅ Workflow completed successfully!")
            print(f"   - Flight: {result['flight_details'].airline} {result['flight_details'].flight_number}")
            print(f"   - Hotel: {result['accommodation_details'].hotel_name}")
            print(f"   - Completed tasks: {len(result['completed_tasks'])}")
            print(f"   - Errors: {len(result['errors'])}")
            return True
        else:
            print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_individual_agents():
    """Test individual agents"""
    print("\n🧪 Testing Individual Agents...")
    
    try:
        from agents.flight_search_agent import LangGraphFlightSearchAgent
        from agents.accommodation_agent import LangGraphAccommodationAgent
        from agents.itinerary_agent import LangGraphItineraryAgent
        
        request = TravelRequest(
            destination="Paris, France",
            start_date="2025-07-01", 
            end_date="2025-07-07",
            number_of_travelers=1
        )
        
        # Test flight agent
        print("✈️ Testing flight agent...")
        flight_agent = LangGraphFlightSearchAgent()
        flight_result = await flight_agent.run(request)
        print(f"   Flight: {flight_result.airline} {flight_result.flight_number}")
        
        # Test accommodation agent
        print("🏨 Testing accommodation agent...")
        accommodation_agent = LangGraphAccommodationAgent()
        accommodation_result = await accommodation_agent.run(request)
        print(f"   Hotel: {accommodation_result.hotel_name}")
        
        # Test itinerary agent
        print("📋 Testing itinerary agent...")
        itinerary_agent = LangGraphItineraryAgent()
        itinerary_result = await itinerary_agent.run(request, flight_result, accommodation_result)
        print(f"   Itinerary length: {len(itinerary_result)} characters")
        
        print("✅ All individual agents working!")
        return True
        
    except Exception as e:
        print(f"❌ Individual agent test failed: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting LangGraph Travel Agent Tests\n")
    
    # Test basic functionality
    basic_test = await test_basic_functionality()
    
    # Test individual agents
    individual_test = await test_individual_agents()
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"   Basic workflow: {'✅ PASS' if basic_test else '❌ FAIL'}")
    print(f"   Individual agents: {'✅ PASS' if individual_test else '❌ FAIL'}")
    
    if basic_test and individual_test:
        print("\n🎉 All tests passed! The LangGraph travel agent is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
