"""
Pure LangGraph Accommodation Booking Agent

This agent handles accommodation booking operations using LangGraph workflows
without any Temporal dependencies.
"""

import openai
import os
import json
import requests
from typing import Dict, Any
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from src.models.travel_models import TravelRequest, AccommodationDetails
from src.workflow.constants import AGENTIC_GOAL, DEFAULT_LLM_MODEL, DEFAULT_HOTEL_NAME, DEFAULT_HOTEL_PRICE_PER_NIGHT, DEFAULT_HOTEL_TOTAL_PRICE


ECHO_SERVER_URL = os.getenv("ECHO_SERVER_URL", "http://localhost:8000/hotel-booking")


class AccommodationBookingState(BaseModel):
    """State for the accommodation booking workflow"""
    request: TravelRequest
    messages: list = []
    function_args: dict = {}
    accommodation_details: AccommodationDetails = None
    booking_payload: dict = {}
    booking_response: dict = {}
    error: str = None
    llm_response: Any = None

    class Config:
        arbitrary_types_allowed = True


class LangGraphAccommodationAgent:
    """
    Pure LangGraph accommodation booking agent
    """
    
    def __init__(self):
        self.goal = "Book the best accommodation for a user based on their travel requirements."
        self.function_definition = {
            "name": "book_accommodation",
            "description": "Book accommodation for a user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "number_of_travelers": {"type": "integer"}
                },
                "required": ["destination", "start_date", "end_date", "number_of_travelers"]
            }
        }
        self.workflow = self._create_workflow()

    def _create_workflow(self):
        """Create the LangGraph workflow for accommodation booking"""
        workflow = StateGraph(AccommodationBookingState)
        
        # Add nodes
        workflow.add_node("prepare_request", self._prepare_request)
        workflow.add_node("call_llm", self._call_llm)
        workflow.add_node("process_response", self._process_response)
        workflow.add_node("prepare_booking", self._prepare_booking)
        workflow.add_node("make_booking", self._make_booking)
        workflow.add_node("create_accommodation_details", self._create_accommodation_details)
        
        # Add edges
        workflow.set_entry_point("prepare_request")
        workflow.add_edge("prepare_request", "call_llm")
        workflow.add_edge("call_llm", "process_response")
        workflow.add_edge("process_response", "prepare_booking")
        workflow.add_edge("prepare_booking", "make_booking")
        workflow.add_edge("make_booking", "create_accommodation_details")
        workflow.add_edge("create_accommodation_details", END)
        
        return workflow.compile()

    def _prepare_request(self, state: AccommodationBookingState) -> AccommodationBookingState:
        """Prepare the request for LLM processing"""
        state.messages = [
            {"role": "system", "content": f"{AGENTIC_GOAL}\n\nSpecific goal: {self.goal}"},
            {"role": "user", "content": f"Book accommodation for {state.request.number_of_travelers} traveler(s) in {state.request.destination} from {state.request.start_date} to {state.request.end_date}."}
        ]
        return state

    def _call_llm(self, state: AccommodationBookingState) -> AccommodationBookingState:
        """Call the LLM with the prepared messages"""
        try:
            response = openai.ChatCompletion.create(
                model=DEFAULT_LLM_MODEL,
                messages=state.messages,
                functions=[self.function_definition],
                api_key=os.getenv("OPENAI_API_KEY")
            )
            state.llm_response = response
        except Exception as e:
            state.error = str(e)
        return state

    def _process_response(self, state: AccommodationBookingState) -> AccommodationBookingState:
        """Process the LLM response and extract function arguments"""
        if state.error:
            return state
            
        choice = state.llm_response.choices[0]
        if choice.finish_reason == "function_call":
            state.function_args = json.loads(choice.message.function_call.arguments)
        return state

    def _prepare_booking(self, state: AccommodationBookingState) -> AccommodationBookingState:
        """Prepare booking payload for external service"""
        if state.function_args:
            state.booking_payload = {
                "destination": state.function_args.get("destination", state.request.destination),
                "check_in": state.function_args.get("start_date", state.request.start_date),
                "check_out": state.function_args.get("end_date", state.request.end_date),
                "guests": state.function_args.get("number_of_travelers", state.request.number_of_travelers)
            }
        else:
            state.booking_payload = {
                "destination": state.request.destination,
                "check_in": state.request.start_date,
                "check_out": state.request.end_date,
                "guests": state.request.number_of_travelers
            }
        return state

    def _make_booking(self, state: AccommodationBookingState) -> AccommodationBookingState:
        """Make the booking request to external service"""
        try:
            response = requests.post(ECHO_SERVER_URL, json=state.booking_payload)
            state.booking_response = response.json()
        except Exception as e:
            state.error = str(e)
            state.booking_response = {}
        return state

    def _create_accommodation_details(self, state: AccommodationBookingState) -> AccommodationBookingState:
        """Create accommodation details from the booking response"""
        if state.error or not state.booking_response:
            # Return default accommodation details if there's an error
            fallback_args = state.function_args if state.function_args else {}
            state.accommodation_details = AccommodationDetails(
                hotel_name="No Hotel Found",
                check_in_date=fallback_args.get("start_date", state.request.start_date),
                check_out_date=fallback_args.get("end_date", state.request.end_date),
                price_per_night=0,
                total_price=0
            )
        else:
            # Use booking response data
            args = state.function_args if state.function_args else {}
            state.accommodation_details = AccommodationDetails(
                hotel_name=state.booking_response.get("hotel_name", DEFAULT_HOTEL_NAME),
                check_in_date=state.booking_response.get("check_in", args.get("start_date", state.request.start_date)),
                check_out_date=state.booking_response.get("check_out", args.get("end_date", state.request.end_date)),
                price_per_night=state.booking_response.get("price_per_night", DEFAULT_HOTEL_PRICE_PER_NIGHT),
                total_price=state.booking_response.get("total_price", DEFAULT_HOTEL_TOTAL_PRICE)
            )
        return state

    async def run(self, request: TravelRequest) -> AccommodationDetails:
        """Run the accommodation booking workflow"""
        initial_state = AccommodationBookingState(request=request)
        final_state = await self.workflow.ainvoke(initial_state)
        return final_state.accommodation_details
