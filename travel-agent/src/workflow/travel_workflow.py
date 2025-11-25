"""
Simple Sequential Travel Workflow

This is a basic pipeline approach where agents run sequentially.
For a true multi-agent system, see multi_agent_travel_workflow.py
"""

from datetime import timedelta
from temporalio import workflow
from src.models.travel_models import TravelRequest, FlightDetails, AccommodationDetails
from src.activities.llm_activities import search_flights, book_accommodation, create_itinerary

@workflow.defn
class TravelAgentWorkflow:
    """
    Sequential Travel Workflow - Pipeline Pattern
    
    Flow: Flight Search → Accommodation Booking → Itinerary Creation
    Each step waits for the previous to complete.
    """
    
    @workflow.run
    async def run(self, request: TravelRequest) -> dict:
        # Sequential execution - each step waits for the previous
        flight = await workflow.execute_activity(search_flights, request, schedule_to_close_timeout=timedelta(seconds=30))
        accommodation = await workflow.execute_activity(book_accommodation, request, schedule_to_close_timeout=timedelta(seconds=30))
        itinerary = await workflow.execute_activity(create_itinerary, request, flight, accommodation, schedule_to_close_timeout=timedelta(seconds=30))
        
        return {
            "flights": flight,
            "accommodation": accommodation,
            "itinerary": itinerary,
        }
