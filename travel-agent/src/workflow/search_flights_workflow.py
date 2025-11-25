import openai
import os
import json
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from src.models.travel_models import TravelRequest, FlightDetails
from src.workflow.constants import AGENTIC_GOAL, DEFAULT_LLM_MODEL, DEFAULT_AIRLINE, DEFAULT_FLIGHT_NUMBER, DEFAULT_FLIGHT_PRICE


class FlightSearchState:
    """State for the flight search workflow"""
    def __init__(self):
        self.request: TravelRequest = None
        self.messages: list = []
        self.function_args: dict = {}
        self.flight_details: FlightDetails = None
        self.error: str = None


class SearchFlightsAgentWorkflow:
    def __init__(self):
        self.goal = "Find the best flights for a user based on their travel requirements."
        self.function_definition = {
            "name": "search_flights",
            "description": "Search for flights for a user.",
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
        """Create the LangGraph workflow for flight search"""
        graph = StateGraph(FlightSearchState)
        
        # Add nodes
        graph.add_node("prepare_request", self._prepare_request)
        graph.add_node("call_llm", self._call_llm)
        graph.add_node("process_response", self._process_response)
        graph.add_node("create_flight_details", self._create_flight_details)
        
        # Add edges
        graph.set_entry_point("prepare_request")
        graph.add_edge("prepare_request", "call_llm")
        graph.add_edge("call_llm", "process_response")
        graph.add_edge("process_response", "create_flight_details")
        graph.add_edge("create_flight_details", END)
        
        return graph.compile()

    async def _prepare_request(self, state: FlightSearchState) -> FlightSearchState:
        """Prepare the request for LLM processing"""
        state.messages = [
            {"role": "system", "content": f"{AGENTIC_GOAL}\n\nSpecific goal: {self.goal}"},
            {"role": "user", "content": f"Find the best flights for {state.request.number_of_travelers} traveler(s) to {state.request.destination} from {state.request.start_date} to {state.request.end_date}."}
        ]
        return state

    async def _call_llm(self, state: FlightSearchState) -> FlightSearchState:
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

    async def _process_response(self, state: FlightSearchState) -> FlightSearchState:
        """Process the LLM response and extract function arguments"""
        if state.error:
            return state
            
        choice = state.llm_response.choices[0]
        if choice.finish_reason == "function_call":
            state.function_args = json.loads(choice.message.function_call.arguments)
        return state

    async def _create_flight_details(self, state: FlightSearchState) -> FlightSearchState:
        """Create flight details from the processed response"""
        if state.error:
            # Return default flight details if there's an error
            state.flight_details = FlightDetails(DEFAULT_AIRLINE, DEFAULT_FLIGHT_NUMBER, state.request.start_date, state.request.end_date, DEFAULT_FLIGHT_PRICE)
        elif state.function_args:
            # Use function arguments if available
            state.flight_details = FlightDetails(
                DEFAULT_AIRLINE, 
                DEFAULT_FLIGHT_NUMBER, 
                state.function_args.get("start_date", state.request.start_date),
                state.function_args.get("end_date", state.request.end_date), 
                DEFAULT_FLIGHT_PRICE
            )
        else:
            # Fallback to request data
            state.flight_details = FlightDetails(DEFAULT_AIRLINE, DEFAULT_FLIGHT_NUMBER, state.request.start_date, state.request.end_date, DEFAULT_FLIGHT_PRICE)
        return state

    async def run(self, request: TravelRequest) -> FlightDetails:
        """Run the flight search workflow"""
        state = FlightSearchState()
        state.request = request
        
        final_state = await self.workflow.ainvoke(state)
        return final_state.flight_details
