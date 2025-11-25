import openai
import os
import json
import requests
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from src.models.travel_models import TravelRequest, AccommodationDetails
from src.workflow.constants import AGENTIC_GOAL, DEFAULT_LLM_MODEL, DEFAULT_HOTEL_NAME, DEFAULT_HOTEL_PRICE_PER_NIGHT, DEFAULT_HOTEL_TOTAL_PRICE


ECHO_SERVER_URL = os.getenv("ECHO_SERVER_URL", "http://localhost:8000/hotel-booking")


class AccommodationBookingState:
    """State for the accommodation booking workflow"""
    def __init__(self):
        self.request: TravelRequest = None
        self.messages: list = []
        self.function_args: dict = {}
        self.accommodation_details: AccommodationDetails = None
        self.booking_payload: dict = {}
        self.booking_response: dict = {}
        self.error: str = None


class BookAccommodationAgentWorkflow:
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

    def _create_workflow(self) -> CompiledStateGraph:
        """Create the LangGraph workflow for accommodation booking"""
        graph = StateGraph(AccommodationBookingState)
        
        # Add nodes
        graph.add_node("prepare_request", self._prepare_request)
        graph.add_node("call_llm", self._call_llm)
        graph.add_node("process_response", self._process_response)
        graph.add_node("prepare_booking", self._prepare_booking)
        graph.add_node("make_booking", self._make_booking)
        graph.add_node("create_accommodation_details", self._create_accommodation_details)
        
        # Add edges
        graph.set_entry_point("prepare_request")
        graph.add_edge("prepare_request", "call_llm")
        graph.add_edge("call_llm", "process_response")
        graph.add_edge("process_response", "prepare_booking")
        graph.add_edge("prepare_booking", "make_booking")
        graph.add_edge("make_booking", "create_accommodation_details")
        graph.add_edge("create_accommodation_details", END)
        
        return graph.compile()

    async def _prepare_request(self, state: AccommodationBookingState) -> AccommodationBookingState:
        """Prepare the request for LLM processing"""
        state.messages = [
            {"role": "system", "content": f"{AGENTIC_GOAL}\n\nSpecific goal: {self.goal}"},
            {"role": "user", "content": f"Book accommodation for {state.request.number_of_travelers} traveler(s) in {state.request.destination} from {state.request.start_date} to {state.request.end_date}."}
        ]
        return state

    async def _call_llm(self, state: AccommodationBookingState) -> AccommodationBookingState:
        """Call the LLM with the prepared messages"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=DEFAULT_LLM_MODEL,
                messages=state.messages,
                functions=[self.function_definition],
                api_key=os.getenv("OPENAI_API_KEY")
            )
            state.llm_response = response
        except Exception as e:
            state.error = str(e)
        return state

    async def _process_response(self, state: AccommodationBookingState) -> AccommodationBookingState:
        """Process the LLM response and extract function arguments"""
        if state.error:
            return state
            
        choice = state.llm_response.choices[0]
        if choice.finish_reason == "function_call":
            state.function_args = json.loads(choice.message.function_call.arguments)
        return state

    async def _prepare_booking(self, state: AccommodationBookingState) -> AccommodationBookingState:
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

    async def _make_booking(self, state: AccommodationBookingState) -> AccommodationBookingState:
        """Make the booking request to external service"""
        try:
            response = requests.post(ECHO_SERVER_URL, json=state.booking_payload)
            state.booking_response = response.json()
        except Exception as e:
            state.error = str(e)
            state.booking_response = {}
        return state

    async def _create_accommodation_details(self, state: AccommodationBookingState) -> AccommodationBookingState:
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
        state = AccommodationBookingState()
        state.request = request
        
        final_state = await self.workflow.ainvoke(state)
        return final_state.accommodation_details
