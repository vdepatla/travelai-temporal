"""
Pure LangGraph Multi-Agent Travel Planning System

This demonstrates how to build a complete multi-agent travel system
using only LangGraph, without Temporal orchestration.

Benefits:
- Simpler architecture
- AI-native features  
- Built-in state management
- Human-in-the-loop support
- Streaming capabilities
- Lower operational overhead
"""

import asyncio
import json
from typing import Dict, List, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemoryCheckpointSaver
from langgraph.checkpoint.postgres import PostgresCheckpointSaver
from pydantic import BaseModel
from src.models.travel_models import TravelRequest, FlightDetails, AccommodationDetails


class TravelAgentState(BaseModel):
    """Shared state for the travel planning multi-agent system"""
    request: TravelRequest
    flight_details: FlightDetails | None = None
    accommodation_details: AccommodationDetails | None = None
    itinerary: str | None = None
    messages: List[Dict[str, Any]] = []
    completed_tasks: List[str] = []
    errors: Dict[str, str] = {}
    next_action: str = "start"
    user_feedback: str | None = None
    
    class Config:
        arbitrary_types_allowed = True


class PureLangGraphTravelAgent:
    """
    Complete multi-agent travel planning system using only LangGraph
    
    Features:
    - Multi-agent coordination
    - Parallel execution
    - State persistence  
    - Error handling
    - Human-in-the-loop
    - Streaming responses
    """
    
    def __init__(self, use_postgres: bool = False):
        # Choose checkpointer based on production needs
        if use_postgres:
            # For production: persistent state across restarts
            self.checkpointer = PostgresCheckpointSaver.from_conn_string(
                "postgresql://user:pass@localhost/langgraph"
            )
        else:
            # For development: in-memory state
            self.checkpointer = MemoryCheckpointSaver()
        
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the multi-agent coordination graph"""
        workflow = StateGraph(TravelAgentState)
        
        # Add all agent nodes
        workflow.add_node("supervisor", self._supervisor_agent)
        workflow.add_node("flight_agent", self._flight_agent)
        workflow.add_node("accommodation_agent", self._accommodation_agent)
        workflow.add_node("itinerary_agent", self._itinerary_agent)
        workflow.add_node("coordinator", self._coordinator_agent)
        workflow.add_node("human_feedback", self._human_feedback_node)
        
        # Define the flow
        workflow.set_entry_point("supervisor")
        
        # Dynamic routing based on state
        workflow.add_conditional_edges(
            "supervisor",
            self._route_next_action,
            {
                "parallel_search": ["flight_agent", "accommodation_agent"],
                "create_itinerary": "itinerary_agent",
                "get_feedback": "human_feedback",
                "coordinate": "coordinator",
                "end": END
            }
        )
        
        # All agents flow to coordinator
        workflow.add_edge(["flight_agent", "accommodation_agent", "itinerary_agent"], "coordinator")
        workflow.add_edge("human_feedback", "supervisor")
        workflow.add_edge("coordinator", "supervisor")
        
        return workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["human_feedback"]  # Allow human intervention
        )
    
    def _route_next_action(self, state: TravelAgentState) -> str:
        """Dynamic routing based on current state"""
        completed = set(state.completed_tasks)
        
        # If nothing started, begin parallel search
        if not completed:
            return "parallel_search"
        
        # If searches done but no itinerary, create one
        if {"flight_search", "accommodation_search"}.issubset(completed):
            if "itinerary_creation" not in completed:
                return "create_itinerary"
        
        # If all done, check if we need user feedback
        if len(completed) >= 3:
            if not state.user_feedback:
                return "get_feedback"
            else:
                return "end"
        
        return "coordinate"
    
    async def _supervisor_agent(self, state: TravelAgentState) -> TravelAgentState:
        """
        Supervisor Agent: High-level coordination and decision making
        """
        print(f"🧠 Supervisor: Coordinating travel to {state.request.destination}")
        
        state.messages.append({
            "agent": "supervisor",
            "action": "coordinating",
            "message": f"Planning trip to {state.request.destination} for {state.request.number_of_travelers} travelers"
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
    
    async def _flight_agent(self, state: TravelAgentState) -> TravelAgentState:
        """
        Flight Agent: Specialized in flight search and booking
        """
        if "flight_search" in state.completed_tasks:
            return state
            
        print(f"✈️  Flight Agent: Searching flights to {state.request.destination}")
        
        try:
            # Simulate flight search with actual LLM call
            from src.workflow.search_flights_workflow import SearchFlightsAgentWorkflow
            workflow = SearchFlightsAgentWorkflow()
            state.flight_details = await workflow.run(state.request)
            
            state.completed_tasks.append("flight_search")
            state.messages.append({
                "agent": "flight_agent",
                "action": "completed",
                "result": f"Found {state.flight_details.airline} flight {state.flight_details.flight_number}"
            })
            print(f"✈️  Flight Agent: Found flight {state.flight_details.flight_number}")
            
        except Exception as e:
            state.errors["flight_agent"] = str(e)
            print(f"❌ Flight Agent Error: {e}")
        
        return state
    
    async def _accommodation_agent(self, state: TravelAgentState) -> TravelAgentState:
        """
        Accommodation Agent: Specialized in hotel booking
        """
        if "accommodation_search" in state.completed_tasks:
            return state
            
        print(f"🏨 Accommodation Agent: Searching hotels in {state.request.destination}")
        
        try:
            # Simulate accommodation search
            from src.workflow.book_accommodation_workflow import BookAccommodationAgentWorkflow
            workflow = BookAccommodationAgentWorkflow()
            state.accommodation_details = await workflow.run(state.request)
            
            state.completed_tasks.append("accommodation_search")
            state.messages.append({
                "agent": "accommodation_agent", 
                "action": "completed",
                "result": f"Booked {state.accommodation_details.hotel_name}"
            })
            print(f"🏨 Accommodation Agent: Booked {state.accommodation_details.hotel_name}")
            
        except Exception as e:
            state.errors["accommodation_agent"] = str(e)
            print(f"❌ Accommodation Agent Error: {e}")
        
        return state
    
    async def _itinerary_agent(self, state: TravelAgentState) -> TravelAgentState:
        """
        Itinerary Agent: Creates comprehensive travel plans
        """
        if "itinerary_creation" in state.completed_tasks:
            return state
            
        if not state.flight_details or not state.accommodation_details:
            print("📋 Itinerary Agent: Waiting for flight and accommodation details")
            return state
        
        print("📋 Itinerary Agent: Creating comprehensive itinerary")
        
        try:
            from src.workflow.create_itinerary_workflow import CreateItineraryAgentWorkflow
            workflow = CreateItineraryAgentWorkflow()
            state.itinerary = await workflow.run(
                state.request, 
                state.flight_details, 
                state.accommodation_details
            )
            
            state.completed_tasks.append("itinerary_creation")
            state.messages.append({
                "agent": "itinerary_agent",
                "action": "completed", 
                "result": "Comprehensive itinerary created"
            })
            print("📋 Itinerary Agent: Itinerary completed")
            
        except Exception as e:
            state.errors["itinerary_agent"] = str(e)
            print(f"❌ Itinerary Agent Error: {e}")
        
        return state
    
    async def _coordinator_agent(self, state: TravelAgentState) -> TravelAgentState:
        """
        Coordinator Agent: Manages agent communication and progress tracking
        """
        print(f"🔄 Coordinator: Tasks completed: {len(state.completed_tasks)}/3")
        
        state.messages.append({
            "agent": "coordinator",
            "action": "status_update",
            "completed_tasks": state.completed_tasks,
            "error_count": len(state.errors)
        })
        
        # Check if we need to wait for parallel tasks
        if "flight_search" in state.completed_tasks and "accommodation_search" in state.completed_tasks:
            print("🔄 Coordinator: Both search tasks complete, ready for itinerary")
        
        return state
    
    async def _human_feedback_node(self, state: TravelAgentState) -> TravelAgentState:
        """
        Human-in-the-Loop: Get user feedback on the travel plan
        """
        print("👤 Human Feedback: Waiting for user input on the travel plan")
        
        # In a real app, this would integrate with a UI
        # For demo, we'll simulate user approval
        state.user_feedback = "approved"
        
        state.messages.append({
            "agent": "human",
            "action": "feedback_provided",
            "feedback": state.user_feedback
        })
        
        return state
    
    async def run(self, request: TravelRequest, thread_id: str = None) -> Dict[str, Any]:
        """
        Run the complete travel planning workflow
        
        Args:
            request: Travel requirements
            thread_id: Conversation thread ID for state persistence
            
        Returns:
            Complete travel plan with agent execution details
        """
        if not thread_id:
            thread_id = f"travel-{hash(str(request))}"
        
        print(f"🚀 Starting travel planning for thread: {thread_id}")
        
        # Initialize state
        initial_state = TravelAgentState(request=request)
        
        # Run the workflow with checkpointing
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            return {
                "success": True,
                "flight_details": final_state.flight_details,
                "accommodation_details": final_state.accommodation_details,
                "itinerary": final_state.itinerary,
                "agent_messages": final_state.messages,
                "completed_tasks": final_state.completed_tasks,
                "errors": final_state.errors,
                "thread_id": thread_id,
                "execution_summary": {
                    "total_agents": 4,
                    "successful_tasks": len(final_state.completed_tasks),
                    "failed_tasks": len(final_state.errors),
                    "has_human_feedback": bool(final_state.user_feedback)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "thread_id": thread_id
            }
    
    async def stream(self, request: TravelRequest, thread_id: str = None):
        """
        Stream workflow execution for real-time updates
        """
        if not thread_id:
            thread_id = f"travel-{hash(str(request))}"
        
        initial_state = TravelAgentState(request=request)
        config = {"configurable": {"thread_id": thread_id}}
        
        async for chunk in self.graph.astream(initial_state, config=config):
            yield chunk
    
    def get_state(self, thread_id: str):
        """Get current state for a thread"""
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.get_state(config)
    
    async def resume_from_feedback(self, thread_id: str, user_input: str):
        """Resume workflow after human feedback"""
        config = {"configurable": {"thread_id": thread_id}}
        
        # Update state with user feedback
        current_state = self.graph.get_state(config)
        if current_state:
            current_state.values.user_feedback = user_input
            
        # Resume execution
        return await self.graph.ainvoke(None, config=config)


# Example usage
async def main():
    """Example of how to use the pure LangGraph travel agent"""
    
    # Create the travel agent
    agent = PureLangGraphTravelAgent(use_postgres=False)
    
    # Create a travel request
    request = TravelRequest(
        destination="Tokyo, Japan",
        start_date="2025-06-01", 
        end_date="2025-06-07",
        number_of_travelers=2
    )
    
    # Option 1: Run complete workflow
    result = await agent.run(request, thread_id="demo-trip-1")
    print(json.dumps(result, indent=2, default=str))
    
    # Option 2: Stream for real-time updates
    print("\n--- Streaming Execution ---")
    async for chunk in agent.stream(request, thread_id="demo-trip-2"):
        print(f"Agent Update: {chunk}")


if __name__ == "__main__":
    asyncio.run(main())
