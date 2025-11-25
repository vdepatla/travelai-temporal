import openai
import os
import json
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from src.models.travel_models import TravelRequest, FlightDetails, AccommodationDetails
from src.workflow.constants import AGENTIC_GOAL, DEFAULT_LLM_MODEL


class ItineraryCreationState:
    """State for the itinerary creation workflow"""
    def __init__(self):
        self.request: TravelRequest = None
        self.flight: FlightDetails = None
        self.accommodation: AccommodationDetails = None
        self.messages: list = []
        self.function_args: dict = {}
        self.itinerary: str = None
        self.error: str = None


class CreateItineraryAgentWorkflow:
    def __init__(self):
        self.goal = "Create a comprehensive and personalized travel itinerary for a user."
        self.function_definition = {
            "name": "create_itinerary",
            "description": "Create a travel itinerary for a user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "number_of_travelers": {"type": "integer"},
                    "flight": {"type": "string"},
                    "accommodation": {"type": "string"}
                },
                "required": ["destination", "start_date", "end_date", "number_of_travelers", "flight", "accommodation"]
            }
        }
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> CompiledStateGraph:
        """Create the LangGraph workflow for itinerary creation"""
        graph = StateGraph(ItineraryCreationState)
        
        # Add nodes
        graph.add_node("prepare_request", self._prepare_request)
        graph.add_node("call_llm", self._call_llm)
        graph.add_node("process_response", self._process_response)
        graph.add_node("finalize_itinerary", self._finalize_itinerary)
        
        # Add edges
        graph.set_entry_point("prepare_request")
        graph.add_edge("prepare_request", "call_llm")
        graph.add_edge("call_llm", "process_response")
        graph.add_edge("process_response", "finalize_itinerary")
        graph.add_edge("finalize_itinerary", END)
        
        return graph.compile()

    async def _prepare_request(self, state: ItineraryCreationState) -> ItineraryCreationState:
        """Prepare the request for LLM processing"""
        state.messages = [
            {"role": "system", "content": f"{AGENTIC_GOAL}\n\nSpecific goal: {self.goal}"},
            {"role": "user", "content": f"Create a comprehensive travel itinerary for {state.request.number_of_travelers} traveler(s) to {state.request.destination} from {state.request.start_date} to {state.request.end_date}, including flight {state.flight.flight_number} and stay at {state.accommodation.hotel_name}. Please include suggested activities, dining recommendations, and daily schedules."}
        ]
        return state

    async def _call_llm(self, state: ItineraryCreationState) -> ItineraryCreationState:
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

    async def _process_response(self, state: ItineraryCreationState) -> ItineraryCreationState:
        """Process the LLM response and extract the itinerary"""
        if state.error:
            return state
            
        choice = state.llm_response.choices[0]
        if choice.finish_reason == "function_call":
            state.function_args = json.loads(choice.message.function_call.arguments)
        
        # Get the itinerary content from the LLM response
        state.itinerary = choice.message.content if choice.message.content else "No itinerary generated"
        return state

    async def _finalize_itinerary(self, state: ItineraryCreationState) -> ItineraryCreationState:
        """Finalize the itinerary with fallback if needed"""
        if state.error or not state.itinerary:
            # Create a basic fallback itinerary
            state.itinerary = f"""
Travel Itinerary for {state.request.destination}

**Trip Details:**
- Destination: {state.request.destination}
- Dates: {state.request.start_date} to {state.request.end_date}
- Travelers: {state.request.number_of_travelers}

**Flight:** {state.flight.airline} {state.flight.flight_number}
**Accommodation:** {state.accommodation.hotel_name}

**Daily Schedule:**
Day 1: Arrival and check-in
Day 2: City exploration and local attractions
Day 3: Cultural activities and dining
Day 4: Departure

Note: This is a basic itinerary. For a more detailed plan, please try again or consult a travel agent.
"""
        return state

    async def run(self, request: TravelRequest, flight: FlightDetails, accommodation: AccommodationDetails) -> str:
        """Run the itinerary creation workflow"""
        state = ItineraryCreationState()
        state.request = request
        state.flight = flight
        state.accommodation = accommodation
        
        final_state = await self.workflow.ainvoke(state)
        return final_state.itinerary
