"""
Pure LangGraph Multi-Agent Travel Planning System

This is the main travel planning system that coordinates multiple specialized agents
using only LangGraph, with no Temporal dependencies.

Features:
- Multi-agent coordination
- Parallel execution where possible
- State persistence with checkpointing
- Human-in-the-loop support
- Streaming capabilities
- Error handling and recovery
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Literal, Optional
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.models.travel_models import TravelRequest, FlightDetails, AccommodationDetails
from src.agents.flight_search_agent import LangGraphFlightSearchAgent
from src.agents.accommodation_agent import LangGraphAccommodationAgent
from src.agents.itinerary_agent import LangGraphItineraryAgent


class TravelPlanningState(BaseModel):
    """Shared state for the entire travel planning system"""
    request: Dict[str, Any]  # Changed from TravelRequest to dict for serialization
    flight_details: Dict[str, Any] = {}  # Changed from FlightDetails to dict
    accommodation_details: Dict[str, Any] = {}  # Changed from AccommodationDetails to dict
    itinerary: Optional[str] = None
    agent_messages: List[Dict[str, Any]] = []
    completed_tasks: List[str] = []
    errors: Dict[str, str] = {}
    next_action: str = "start"
    user_feedback: Optional[str] = None
    parallel_tasks_running: bool = False

    class Config:
        arbitrary_types_allowed = True


class LangGraphTravelAgent:
    """
    Complete multi-agent travel planning system using only LangGraph
    
    This system coordinates multiple specialized agents to provide
    comprehensive travel planning services.
    """
    
    def __init__(self, use_postgres: bool = False, connection_string: str = None):
        """
        Initialize the travel agent with configurable durability
        
        Args:
            use_postgres: Whether to use PostgreSQL for persistent state
            connection_string: PostgreSQL connection string if use_postgres=True
                              Format: "postgresql://user:password@host:port/dbname"
        
        Durability Options:
            - Memory: Fast, in-memory checkpointing for development
            - PostgreSQL: Persistent, production-ready checkpointing
        """
        # Initialize specialized agents
        self.flight_agent = LangGraphFlightSearchAgent()
        self.accommodation_agent = LangGraphAccommodationAgent()
        self.itinerary_agent = LangGraphItineraryAgent()
        
        # Choose checkpointer based on configuration
        self.use_postgres = use_postgres
        if use_postgres:
            if not connection_string:
                # Default to environment variable or local PostgreSQL
                connection_string = os.getenv(
                    "POSTGRES_CONNECTION_STRING",
                    "postgresql://postgres:password@localhost:5432/langgraph_checkpoints"
                )
            
            try:
                # Try to import and use PostgreSQL checkpointer only when needed
                from langgraph.checkpoint.postgres import PostgresCheckpointSaver
                self.checkpointer = PostgresCheckpointSaver.from_conn_string(connection_string)
                print("✅ Using PostgreSQL for state persistence")
            except ImportError:
                print("⚠️  PostgreSQL checkpointer not available, using memory checkpointer")
                self.checkpointer = MemorySaver()
                self.use_postgres = False
            except Exception as e:
                print(f"⚠️  PostgreSQL connection failed, falling back to memory: {str(e)}")
                self.checkpointer = MemorySaver()
                self.use_postgres = False
        else:
            self.checkpointer = MemorySaver()
            print("📝 Using in-memory checkpointer (development mode)")
        
        # Build the coordination workflow
        self.workflow = self._build_coordination_workflow()
    
    def _build_coordination_workflow(self):
        """Build the main coordination workflow"""
        workflow = StateGraph(TravelPlanningState)
        
        # Add coordination nodes
        workflow.add_node("supervisor", self._supervisor)
        workflow.add_node("flight_coordinator", self._flight_coordinator)
        workflow.add_node("accommodation_coordinator", self._accommodation_coordinator)
        workflow.add_node("itinerary_coordinator", self._itinerary_coordinator)
        workflow.add_node("result_aggregator", self._result_aggregator)
        workflow.add_node("human_feedback", self._human_feedback)
        
        # Define the workflow flow
        workflow.set_entry_point("supervisor")
        
        # Dynamic routing from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_from_supervisor,
            {
                "flight_search": "flight_coordinator",
                "accommodation_search": "accommodation_coordinator",
                "create_itinerary": "itinerary_coordinator",
                "get_feedback": "human_feedback",
                "complete": "result_aggregator",
                "end": END
            }
        )
        
        # All coordinators flow back to supervisor
        workflow.add_edge(["flight_coordinator", "accommodation_coordinator", "itinerary_coordinator"], "supervisor")
        workflow.add_edge("result_aggregator", END)
        workflow.add_edge("human_feedback", "supervisor")
        
        return workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["human_feedback"]  # Allow human intervention
        )
    
    def _route_from_supervisor(self, state: TravelPlanningState) -> str:
        """Route decisions from the supervisor"""
        completed = set(state.completed_tasks)
        
        # If nothing started, begin with flight search
        if not completed:
            return "flight_search"
        
        # If flight done but not accommodation, do accommodation
        if "flight_search" in completed and "accommodation_search" not in completed:
            return "accommodation_search"
        
        # If searches done but no itinerary, create one
        if {"flight_search", "accommodation_search"}.issubset(completed):
            if "itinerary_creation" not in completed:
                return "create_itinerary"
        
        # If all core tasks done, check if we need user feedback
        if len(completed) >= 3:
            if not state.user_feedback:
                return "get_feedback"
            else:
                return "complete"
        
        return "end"
    
    async def _supervisor(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Supervisor Agent: High-level coordination and decision making
        """
        destination = state.request["destination"]
        print(f"🧠 Supervisor: Coordinating travel to {destination}")
        
        state.agent_messages.append({
            "agent": "supervisor",
            "action": "coordinating",
            "message": f"Planning trip to {destination} for {state.request['number_of_travelers']} travelers",
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Determine what needs to be done
        remaining = []
        if "flight_search" not in state.completed_tasks:
            remaining.append("flight_search")
        if "accommodation_search" not in state.completed_tasks:
            remaining.append("accommodation_search")
        if len(state.completed_tasks) >= 2 and "itinerary_creation" not in state.completed_tasks:
            remaining.append("itinerary_creation")
        
        print(f"🧠 Supervisor: Remaining tasks: {remaining}")
        return state
    
    async def _flight_coordinator(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Coordinate flight search operations
        """
        if "flight_search" in state.completed_tasks:
            return state
        
        destination = state.request["destination"]
        print(f"✈️ Flight Coordinator: Searching flights to {destination}")
        
        try:
            # Convert dict back to TravelRequest for the agent
            request = TravelRequest(
                destination=state.request["destination"],
                start_date=state.request["start_date"],
                end_date=state.request["end_date"],
                number_of_travelers=state.request["number_of_travelers"]
            )
            
            flight_details = await self.flight_agent.run(request)
            state.flight_details = {
                "airline": flight_details.airline,
                "flight_number": flight_details.flight_number,
                "departure_time": flight_details.departure_time,
                "arrival_time": flight_details.arrival_time,
                "price": flight_details.price
            }
            state.completed_tasks.append("flight_search")
            
            state.agent_messages.append({
                "agent": "flight_coordinator",
                "action": "completed",
                "result": f"Found {flight_details.airline} flight {flight_details.flight_number}",
                "details": state.flight_details
            })
            
            print(f"✈️ Flight Coordinator: Found flight {flight_details.flight_number}")
            
        except Exception as e:
            state.errors["flight_search"] = str(e)
            state.agent_messages.append({
                "agent": "flight_coordinator",
                "action": "error",
                "message": str(e)
            })
            print(f"❌ Flight Coordinator Error: {e}")
        
        return state
    
    async def _accommodation_coordinator(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Coordinate accommodation booking operations
        """
        if "accommodation_search" in state.completed_tasks:
            return state
        
        destination = state.request["destination"]
        print(f"🏨 Accommodation Coordinator: Searching hotels in {destination}")
        
        try:
            # Convert dict back to TravelRequest for the agent
            request = TravelRequest(
                destination=state.request["destination"],
                start_date=state.request["start_date"],
                end_date=state.request["end_date"],
                number_of_travelers=state.request["number_of_travelers"]
            )
            
            accommodation_details = await self.accommodation_agent.run(request)
            state.accommodation_details = {
                "hotel_name": accommodation_details.hotel_name,
                "check_in_date": accommodation_details.check_in_date,
                "check_out_date": accommodation_details.check_out_date,
                "price_per_night": accommodation_details.price_per_night,
                "total_price": accommodation_details.total_price
            }
            state.completed_tasks.append("accommodation_search")
            
            state.agent_messages.append({
                "agent": "accommodation_coordinator",
                "action": "completed",
                "result": f"Booked {accommodation_details.hotel_name}",
                "details": state.accommodation_details
            })
            
            print(f"🏨 Accommodation Coordinator: Booked {accommodation_details.hotel_name}")
            
        except Exception as e:
            state.errors["accommodation_search"] = str(e)
            state.agent_messages.append({
                "agent": "accommodation_coordinator",
                "action": "error",
                "message": str(e)
            })
            print(f"❌ Accommodation Coordinator Error: {e}")
        
        return state
    
    async def _itinerary_coordinator(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Coordinate itinerary creation
        """
        if "itinerary_creation" in state.completed_tasks:
            return state
        
        if not state.flight_details or not state.accommodation_details:
            print("📋 Itinerary Coordinator: Waiting for flight and accommodation details")
            return state
        
        print("📋 Itinerary Coordinator: Creating comprehensive itinerary")
        
        try:
            # Convert dicts back to model objects for the agent
            request = TravelRequest(
                destination=state.request["destination"],
                start_date=state.request["start_date"],
                end_date=state.request["end_date"],
                number_of_travelers=state.request["number_of_travelers"]
            )
            
            flight_details = FlightDetails(
                airline=state.flight_details["airline"],
                flight_number=state.flight_details["flight_number"],
                departure_time=state.flight_details["departure_time"],
                arrival_time=state.flight_details["arrival_time"],
                price=state.flight_details["price"]
            )
            
            accommodation_details = AccommodationDetails(
                hotel_name=state.accommodation_details["hotel_name"],
                check_in_date=state.accommodation_details["check_in_date"],
                check_out_date=state.accommodation_details["check_out_date"],
                price_per_night=state.accommodation_details["price_per_night"],
                total_price=state.accommodation_details["total_price"]
            )
            
            state.itinerary = await self.itinerary_agent.run(
                request, 
                flight_details, 
                accommodation_details
            )
            state.completed_tasks.append("itinerary_creation")
            
            state.agent_messages.append({
                "agent": "itinerary_coordinator",
                "action": "completed",
                "result": "Comprehensive itinerary created",
                "details": {
                    "itinerary_length": len(state.itinerary),
                    "includes_activities": "activities" in state.itinerary.lower(),
                    "includes_dining": "dining" in state.itinerary.lower()
                }
            })
            
            print("📋 Itinerary Coordinator: Itinerary completed")
            
        except Exception as e:
            state.errors["itinerary_creation"] = str(e)
            state.agent_messages.append({
                "agent": "itinerary_coordinator",
                "action": "error",
                "message": str(e)
            })
            print(f"❌ Itinerary Coordinator Error: {e}")
        
        return state
    
    async def _result_aggregator(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Aggregate final results
        """
        print("📊 Result Aggregator: Compiling final travel plan")
        
        state.agent_messages.append({
            "agent": "result_aggregator",
            "action": "finalizing",
            "message": "Compiling comprehensive travel plan",
            "summary": {
                "completed_tasks": len(state.completed_tasks),
                "total_errors": len(state.errors),
                "has_flight": bool(state.flight_details),
                "has_accommodation": bool(state.accommodation_details),
                "has_itinerary": bool(state.itinerary),
                "user_feedback_provided": bool(state.user_feedback)
            }
        })
        
        return state
    
    async def _human_feedback(self, state: TravelPlanningState) -> TravelPlanningState:
        """
        Human-in-the-Loop: Get user feedback on the travel plan
        """
        print("👤 Human Feedback: Waiting for user input on the travel plan")
        
        state.agent_messages.append({
            "agent": "human_feedback",
            "action": "requesting_feedback",
            "message": "Please review the travel plan and provide feedback"
        })
        
        # In a real application, this would pause for user input
        # For now, we'll simulate user approval
        state.user_feedback = "approved"
        
        return state
    
    async def run(self, request: TravelRequest, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the complete travel planning workflow
        
        Args:
            request: Travel requirements
            thread_id: Conversation thread ID for state persistence
            
        Returns:
            Complete travel plan with execution details
        """
        if not thread_id:
            # Create a safe thread ID from request properties
            import uuid
            request_str = f"{request.destination}-{request.start_date}-{request.end_date}-{request.number_of_travelers}"
            thread_id = f"travel-{hash(request_str) % 10000}"  # Limit to 4 digits
        
        print(f"🚀 Starting travel planning for thread: {thread_id}")
        
        # Initialize state
        initial_state = TravelPlanningState(
            request={
                "destination": request.destination,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "number_of_travelers": request.number_of_travelers
            }
        )
        
        # Run the workflow with checkpointing
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            final_state = await self.workflow.ainvoke(initial_state, config=config)
            
            # Convert dictionaries back to model objects for the return value
            flight_details = None
            if final_state.flight_details:
                flight_details = FlightDetails(
                    airline=final_state.flight_details.get("airline"),
                    flight_number=final_state.flight_details.get("flight_number"),
                    departure_time=final_state.flight_details.get("departure_time"),
                    arrival_time=final_state.flight_details.get("arrival_time"),
                    price=final_state.flight_details.get("price")
                )
            
            accommodation_details = None
            if final_state.accommodation_details:
                accommodation_details = AccommodationDetails(
                    hotel_name=final_state.accommodation_details.get("hotel_name"),
                    check_in_date=final_state.accommodation_details.get("check_in_date"),
                    check_out_date=final_state.accommodation_details.get("check_out_date"),
                    price_per_night=final_state.accommodation_details.get("price_per_night"),
                    total_price=final_state.accommodation_details.get("total_price")
                )
            
            return {
                "success": True,
                "thread_id": thread_id,
                "flight_details": flight_details,
                "accommodation_details": accommodation_details,
                "itinerary": final_state.itinerary,
                "agent_messages": final_state.agent_messages,
                "completed_tasks": final_state.completed_tasks,
                "errors": final_state.errors,
                "user_feedback": final_state.user_feedback,
                "execution_summary": {
                    "total_agents_used": 4,
                    "successful_tasks": len(final_state.completed_tasks),
                    "failed_tasks": len(final_state.errors),
                    "parallel_execution": final_state.parallel_tasks_running,
                    "human_interaction": bool(final_state.user_feedback)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "thread_id": thread_id
            }
    
    async def stream(self, request: TravelRequest, thread_id: Optional[str] = None):
        """
        Stream workflow execution for real-time updates
        """
        if not thread_id:
            # Create a safe thread ID from request properties
            import uuid
            request_str = f"{request.destination}-{request.start_date}-{request.end_date}-{request.number_of_travelers}"
            thread_id = f"travel-{hash(request_str) % 10000}"  # Limit to 4 digits
        
        initial_state = TravelPlanningState(
            request={
                "destination": request.destination,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "number_of_travelers": request.number_of_travelers
            }
        )
        config = {"configurable": {"thread_id": thread_id}}
        
        async for chunk in self.workflow.astream(initial_state, config=config):
            yield {
                "thread_id": thread_id,
                "chunk": chunk,
                "timestamp": asyncio.get_event_loop().time()
            }
    
    def get_state(self, thread_id: str):
        """Get current state for a thread"""
        config = {"configurable": {"thread_id": thread_id}}
        return self.workflow.get_state(config)
    
    async def get_state_history(self, thread_id: str, limit: int = 10):
        """Get state history for a thread"""
        config = {"configurable": {"thread_id": thread_id}}
        history = []
        
        async for state in self.workflow.aget_state_history(config, limit=limit):
            history.append({
                "config": state.config,
                "created_at": state.created_at,
                "parent_config": state.parent_config,
                "values": state.values,
                "next": state.next,
                "tasks": state.tasks
            })
        
        return history
    
    def update_state(self, thread_id: str, values: Dict[str, Any]):
        """Update state for a thread"""
        config = {"configurable": {"thread_id": thread_id}}
        self.workflow.update_state(config, values)
    
    async def resume_from_feedback(self, thread_id: str, user_input: str):
        """Resume workflow after human feedback"""
        config = {"configurable": {"thread_id": thread_id}}
        
        # Update state with user feedback
        self.update_state(thread_id, {"user_feedback": user_input})
        
        # Resume execution
        result = None
        async for chunk in self.workflow.astream(None, config=config):
            result = chunk
        
        return result
    
    async def get_checkpointer_info(self):
        """Get information about the current checkpointer"""
        return {
            "type": "PostgreSQL" if self.use_postgres else "Memory",
            "persistent": self.use_postgres,
            "production_ready": self.use_postgres,
            "survives_restart": self.use_postgres,
            "concurrent_safe": self.use_postgres
        }
    
    async def list_active_threads(self):
        """List all active threads (PostgreSQL only)"""
        if not self.use_postgres:
            return {"error": "Thread listing only available with PostgreSQL checkpointer"}
        
        try:
            # This would require direct database access
            # Implementation depends on specific PostgreSQL setup
            return {"message": "Active thread listing requires direct database query"}
        except Exception as e:
            return {"error": f"Failed to list threads: {str(e)}"}
    
    async def cleanup_old_checkpoints(self, days_old: int = 30):
        """Clean up old checkpoints (PostgreSQL only)"""
        if not self.use_postgres:
            return {"message": "Cleanup not needed for memory checkpointer"}
        
        try:
            # This would require direct database access
            return {"message": f"Would clean checkpoints older than {days_old} days"}
        except Exception as e:
            return {"error": f"Failed to cleanup: {str(e)}"}

# Example usage and testing
async def main():
    """Example of how to use the pure LangGraph travel agent"""
    
    # Create the travel agent (using memory checkpointer for demo)
    agent = LangGraphTravelAgent(use_postgres=False)
    
    # Create a travel request
    request = TravelRequest(
        destination="Tokyo, Japan",
        start_date="2025-06-01",
        end_date="2025-06-07",
        number_of_travelers=2
    )
    
    # Option 1: Run complete workflow
    print("=== Running Complete Workflow ===")
    result = await agent.run(request, thread_id="demo-trip-1")
    print(json.dumps(result, indent=2, default=str))
    
    # Option 2: Stream for real-time updates
    print("\n=== Streaming Execution ===")
    async for update in agent.stream(request, thread_id="demo-trip-2"):
        print(f"Stream Update: {update}")


if __name__ == "__main__":
    asyncio.run(main())
