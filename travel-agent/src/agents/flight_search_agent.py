"""
Pure LangGraph Flight Search Agent

This agent handles flight search operations using LangGraph workflows
without any Temporal dependencies.
"""

import openai
import os
import json
from typing import Dict, Any
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from src.models.travel_models import TravelRequest, FlightDetails
from src.workflow.constants import AGENTIC_GOAL, DEFAULT_LLM_MODEL, DEFAULT_AIRLINE, DEFAULT_FLIGHT_NUMBER, DEFAULT_FLIGHT_PRICE


class FlightSearchState(BaseModel):
    """State for the flight search workflow"""
    request: TravelRequest
    messages: list = []
    function_args: dict = {}
    flight_details: FlightDetails = None
    error: str = None
    llm_response: Any = None

    class Config:
        arbitrary_types_allowed = True


class LangGraphFlightSearchAgent:
    """
    Pure LangGraph flight search agent
    """
    
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

    def _create_workflow(self):
        """Create the LangGraph workflow for flight search"""
        workflow = StateGraph(FlightSearchState)
        
        # Add nodes
        workflow.add_node("prepare_request", self._prepare_request)
        workflow.add_node("call_llm", self._call_llm)
        workflow.add_node("process_response", self._process_response)
        workflow.add_node("create_flight_details", self._create_flight_details)
        
        # Add edges
        workflow.set_entry_point("prepare_request")
        workflow.add_edge("prepare_request", "call_llm")
        workflow.add_edge("call_llm", "process_response")
        workflow.add_edge("process_response", "create_flight_details")
        workflow.add_edge("create_flight_details", END)
        
        return workflow.compile()

    def _prepare_request(self, state: FlightSearchState) -> FlightSearchState:
        """Prepare the request for LLM processing"""
        state.messages = [
            {"role": "system", "content": f"{AGENTIC_GOAL}\n\nSpecific goal: {self.goal}"},
            {"role": "user", "content": f"Find the best flights for {state.request.number_of_travelers} traveler(s) to {state.request.destination} from {state.request.start_date} to {state.request.end_date}."}
        ]
        return state

    def _call_llm(self, state: FlightSearchState) -> FlightSearchState:
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

    def _process_response(self, state: FlightSearchState) -> FlightSearchState:
        """Process the LLM response and extract function arguments"""
        if state.error:
            return state
            
        choice = state.llm_response.choices[0]
        if choice.finish_reason == "function_call":
            state.function_args = json.loads(choice.message.function_call.arguments)
        return state

    def _create_flight_details(self, state: FlightSearchState) -> FlightSearchState:
        """Create flight details from the processed response"""
        if state.error:
            # Return default flight details if there's an error
            state.flight_details = FlightDetails(
                DEFAULT_AIRLINE, 
                DEFAULT_FLIGHT_NUMBER, 
                state.request.start_date, 
                state.request.end_date, 
                DEFAULT_FLIGHT_PRICE
            )
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
            state.flight_details = FlightDetails(
                DEFAULT_AIRLINE, 
                DEFAULT_FLIGHT_NUMBER, 
                state.request.start_date, 
                state.request.end_date, 
                DEFAULT_FLIGHT_PRICE
            )
        return state

    async def run(self, request: TravelRequest) -> FlightDetails:
        """Run the flight search workflow"""
        initial_state = FlightSearchState(request=request)
        final_state = await self.workflow.ainvoke(initial_state)
        return final_state.flight_details
