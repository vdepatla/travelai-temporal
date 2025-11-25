"""
Pure LangGraph Accommodation Booking Agent

This agent handles accommodation booking operations using LangGraph workflows
without any Temporal dependencies.
"""

import os
from src.models.travel_models import TravelRequest, AccommodationDetails
from src.workflow.constants import DEFAULT_HOTEL_NAME, DEFAULT_HOTEL_PRICE_PER_NIGHT, DEFAULT_HOTEL_TOTAL_PRICE


class LangGraphAccommodationAgent:
    """
    Simplified accommodation booking agent without internal state graph
    """
    
    def __init__(self):
        self.goal = "Book the best accommodation for a user based on their travel requirements."
    
    async def run(self, request: TravelRequest) -> AccommodationDetails:
        """Run the accommodation booking workflow"""
        try:
            # Simplified mock implementation to avoid serialization issues
            # In a real implementation, this would call external hotel booking APIs
            return AccommodationDetails(
                hotel_name=DEFAULT_HOTEL_NAME,
                check_in_date=request.start_date,
                check_out_date=request.end_date,
                price_per_night=DEFAULT_HOTEL_PRICE_PER_NIGHT,
                total_price=DEFAULT_HOTEL_TOTAL_PRICE
            )
        except Exception as e:
            print(f"❌ Accommodation booking error: {e}")
            # Return default accommodation even on error to keep the workflow going
            return AccommodationDetails(
                hotel_name="Mock Hotel",
                check_in_date=request.start_date,
                check_out_date=request.end_date,
                price_per_night=89.99,
                total_price=450.00
            )
