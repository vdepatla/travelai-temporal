"""
Pure LangGraph Flight Search Agent

This agent handles flight search operations using LangGraph workflows
without any Temporal dependencies.
"""

import os
from src.models.travel_models import TravelRequest, FlightDetails
from src.workflow.constants import DEFAULT_AIRLINE, DEFAULT_FLIGHT_NUMBER, DEFAULT_FLIGHT_PRICE


class LangGraphFlightSearchAgent:
    """
    Simplified flight search agent without internal state graph
    """
    
    def __init__(self):
        self.goal = "Find the best flights for a user based on their travel requirements."
    
    async def run(self, request: TravelRequest) -> FlightDetails:
        """Run the flight search workflow"""
        try:
            # Simplified mock implementation to avoid serialization issues
            # In a real implementation, this would call external flight APIs
            return FlightDetails(
                airline=DEFAULT_AIRLINE,
                flight_number=DEFAULT_FLIGHT_NUMBER,
                departure_time=request.start_date,
                arrival_time=request.end_date,
                price=DEFAULT_FLIGHT_PRICE
            )
        except Exception as e:
            print(f"❌ Flight search error: {e}")
            # Return default flight even on error to keep the workflow going
            return FlightDetails(
                airline="MockAir",
                flight_number="MOCK123",
                departure_time=request.start_date,
                arrival_time=request.end_date,
                price=299.99
            )
