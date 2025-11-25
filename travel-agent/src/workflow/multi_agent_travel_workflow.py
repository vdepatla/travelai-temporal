"""
Multi-Agent Travel Planning System using LangGraph and Temporal

This implements a true multi-agent architecture where:
1. A Supervisor Agent coordinates multiple specialized agents
2. Agents can communicate with each other
3. Agents run in parallel when possible
4. Shared state is managed across agents
"""

from typing import Dict, List, Any, Literal
from datetime import timedelta
from temporalio import workflow
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from src.models.travel_models import TravelRequest, FlightDetails, AccommodationDetails
from src.activities.llm_activities import search_flights, book_accommodation, create_itinerary


class MultiAgentState:
    """Shared state across all agents"""
    def __init__(self):
        self.request: TravelRequest = None
        self.flight_details: FlightDetails = None
        self.accommodation_details: AccommodationDetails = None
        self.itinerary: str = None
        self.messages: List[Dict[str, Any]] = []
        self.next_agent: str = ""
        self.completed_tasks: List[str] = []
        self.errors: Dict[str, str] = {}
        self.parallel_tasks: List[str] = []


@workflow.defn
class MultiAgentTravelWorkflow:
    """
    Multi-Agent Travel Planning Workflow
    Uses a supervisor pattern to coordinate specialized agents
    """
    
    def __init__(self):
        self.agent_graph = self._create_agent_graph()
    
    def _create_agent_graph(self) -> CompiledStateGraph:
        """Create the multi-agent coordination graph"""
        graph = StateGraph(MultiAgentState)
        
        # Add agent nodes
        graph.add_node("supervisor", self._supervisor_agent)
        graph.add_node("flight_agent", self._flight_agent)
        graph.add_node("accommodation_agent", self._accommodation_agent) 
        graph.add_node("itinerary_agent", self._itinerary_agent)
        graph.add_node("coordinator", self._coordinator_agent)
        
        # Define the flow
        graph.set_entry_point("supervisor")
        
        # Supervisor decides which agents to activate
        graph.add_conditional_edges(
            "supervisor",
            self._route_to_agents,
            {
                "parallel_search": ["flight_agent", "accommodation_agent"],
                "flight_only": "flight_agent", 
                "accommodation_only": "accommodation_agent",
                "itinerary": "itinerary_agent",
                "end": END
            }
        )
        
        # Agents report back to coordinator
        graph.add_edge("flight_agent", "coordinator")
        graph.add_edge("accommodation_agent", "coordinator")
        graph.add_edge("itinerary_agent", "coordinator")
        
        # Coordinator decides next step
        graph.add_conditional_edges(
            "coordinator",
            self._coordinate_next_step,
            {
                "continue": "supervisor",
                "create_itinerary": "itinerary_agent",
                "end": END
            }
        )
        
        return graph.compile()
    
    def _route_to_agents(self, state: MultiAgentState) -> str:
        """Supervisor decides which agents to activate next"""
        completed = set(state.completed_tasks)
        
        # If nothing completed, start with parallel search
        if not completed:
            state.parallel_tasks = ["flight_search", "accommodation_search"]
            return "parallel_search"
        
        # If both search tasks done, create itinerary
        if {"flight_search", "accommodation_search"}.issubset(completed):
            return "itinerary"
        
        # If only one search task done, wait for the other
        if "flight_search" in completed and "accommodation_search" not in completed:
            return "accommodation_only"
        elif "accommodation_search" in completed and "flight_search" not in completed:
            return "flight_only"
        
        return "end"
    
    def _coordinate_next_step(self, state: MultiAgentState) -> str:
        """Coordinator determines the next step based on agent results"""
        completed = set(state.completed_tasks)
        
        # Check if we have both flight and accommodation
        if {"flight_search", "accommodation_search"}.issubset(completed):
            if "itinerary_creation" not in completed:
                return "create_itinerary"
        
        # If we're missing some tasks, continue with supervisor
        if len(completed) < 3:  # We expect 3 tasks total
            return "continue"
        
        return "end"
    
    async def _supervisor_agent(self, state: MultiAgentState) -> MultiAgentState:
        """
        Supervisor Agent: Orchestrates the overall travel planning process
        Decides which agents to activate and monitors progress
        """
        state.messages.append({
            "agent": "supervisor",
            "action": "planning_coordination", 
            "message": f"Coordinating travel planning for {state.request.destination}"
        })
        
        # Analyze what needs to be done
        remaining_tasks = []
        if "flight_search" not in state.completed_tasks:
            remaining_tasks.append("flight_search")
        if "accommodation_search" not in state.completed_tasks:
            remaining_tasks.append("accommodation_search")
        if "itinerary_creation" not in state.completed_tasks and len(state.completed_tasks) >= 2:
            remaining_tasks.append("itinerary_creation")
        
        state.messages.append({
            "agent": "supervisor",
            "action": "task_analysis",
            "remaining_tasks": remaining_tasks
        })
        
        return state
    
    async def _flight_agent(self, state: MultiAgentState) -> MultiAgentState:
        """Flight Search Agent: Specialized in finding flights"""
        try:
            state.messages.append({
                "agent": "flight_agent", 
                "action": "starting_search",
                "message": f"Searching flights to {state.request.destination}"
            })
            
            # Execute flight search via Temporal activity
            state.flight_details = await workflow.execute_activity(
                search_flights, 
                state.request, 
                schedule_to_close_timeout=timedelta(seconds=30)
            )
            
            state.completed_tasks.append("flight_search")
            state.messages.append({
                "agent": "flight_agent",
                "action": "search_completed", 
                "result": f"Found flight {state.flight_details.flight_number}"
            })
            
        except Exception as e:
            state.errors["flight_agent"] = str(e)
            state.messages.append({
                "agent": "flight_agent",
                "action": "error",
                "message": str(e)
            })
        
        return state
    
    async def _accommodation_agent(self, state: MultiAgentState) -> MultiAgentState:
        """Accommodation Agent: Specialized in booking accommodations"""
        try:
            state.messages.append({
                "agent": "accommodation_agent",
                "action": "starting_search", 
                "message": f"Searching accommodation in {state.request.destination}"
            })
            
            # Execute accommodation booking via Temporal activity
            state.accommodation_details = await workflow.execute_activity(
                book_accommodation,
                state.request,
                schedule_to_close_timeout=timedelta(seconds=30)
            )
            
            state.completed_tasks.append("accommodation_search")
            state.messages.append({
                "agent": "accommodation_agent",
                "action": "search_completed",
                "result": f"Booked {state.accommodation_details.hotel_name}"
            })
            
        except Exception as e:
            state.errors["accommodation_agent"] = str(e)
            state.messages.append({
                "agent": "accommodation_agent", 
                "action": "error",
                "message": str(e)
            })
        
        return state
    
    async def _itinerary_agent(self, state: MultiAgentState) -> MultiAgentState:
        """Itinerary Agent: Creates comprehensive travel itineraries"""
        try:
            # Wait for dependencies
            if not state.flight_details or not state.accommodation_details:
                state.messages.append({
                    "agent": "itinerary_agent",
                    "action": "waiting_dependencies",
                    "message": "Waiting for flight and accommodation details"
                })
                return state
            
            state.messages.append({
                "agent": "itinerary_agent",
                "action": "creating_itinerary",
                "message": "Creating comprehensive travel itinerary"
            })
            
            # Execute itinerary creation via Temporal activity
            state.itinerary = await workflow.execute_activity(
                create_itinerary,
                state.request,
                state.flight_details, 
                state.accommodation_details,
                schedule_to_close_timeout=timedelta(seconds=30)
            )
            
            state.completed_tasks.append("itinerary_creation")
            state.messages.append({
                "agent": "itinerary_agent",
                "action": "itinerary_completed",
                "result": "Comprehensive itinerary created"
            })
            
        except Exception as e:
            state.errors["itinerary_agent"] = str(e)
            state.messages.append({
                "agent": "itinerary_agent",
                "action": "error", 
                "message": str(e)
            })
        
        return state
    
    async def _coordinator_agent(self, state: MultiAgentState) -> MultiAgentState:
        """
        Coordinator Agent: Manages agent communication and synchronization
        Ensures all agents have the information they need
        """
        state.messages.append({
            "agent": "coordinator",
            "action": "synchronizing",
            "completed_tasks": state.completed_tasks,
            "errors": list(state.errors.keys())
        })
        
        # Share information between agents
        if state.flight_details and state.accommodation_details:
            state.messages.append({
                "agent": "coordinator", 
                "action": "information_sharing",
                "message": "Flight and accommodation details available for itinerary creation"
            })
        
        return state

    @workflow.run
    async def run(self, request: TravelRequest) -> Dict[str, Any]:
        """
        Main workflow execution with multi-agent coordination
        """
        # Initialize shared state
        state = MultiAgentState()
        state.request = request
        
        # Run the multi-agent workflow
        final_state = await self.agent_graph.ainvoke(state)
        
        # Return comprehensive results
        return {
            "flights": final_state.flight_details,
            "accommodation": final_state.accommodation_details, 
            "itinerary": final_state.itinerary,
            "agent_messages": final_state.messages,
            "completed_tasks": final_state.completed_tasks,
            "errors": final_state.errors,
            "execution_summary": {
                "total_agents": 4,
                "successful_tasks": len(final_state.completed_tasks),
                "failed_tasks": len(final_state.errors),
                "parallel_execution": len(final_state.parallel_tasks) > 1
            }
        }
