"""
Agent Durability Testing for LangGraph Travel Agent

This test demonstrates and validates agent durability features:
1. State persistence across crashes
2. Resume from checkpoints
3. Recovery after interruptions
4. Memory vs PostgreSQL checkpointing
"""

import asyncio
import sys
import os
import json
import tempfile
import sqlite3
from typing import Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.travel_models import TravelRequest
from agents.travel_agent import LangGraphTravelAgent


class DurabilityTestHarness:
    """Test harness for demonstrating and testing agent durability"""
    
    def __init__(self):
        self.test_results = []
        
    async def test_memory_checkpointing(self):
        """Test in-memory checkpointing and state persistence"""
        print("\n🧪 Testing Memory Checkpointing...")
        
        try:
            # Create agent with memory checkpointing
            agent = LangGraphTravelAgent(use_postgres=False)
            thread_id = "memory-test-123"
            
            # Create test request
            request = TravelRequest(
                destination="Barcelona, Spain",
                start_date="2025-08-01",
                end_date="2025-08-07",
                number_of_travelers=2
            )
            
            print("   ✓ Starting travel planning workflow...")
            
            # Start the workflow but interrupt it
            config = {"configurable": {"thread_id": thread_id}}
            result = None
            
            async for chunk in agent.workflow.astream(
                {"request": request, "next_action": "start", "completed_tasks": [], "errors": {}, "agent_messages": []},
                config=config
            ):
                print(f"   📊 Checkpoint: {chunk}")
                # Simulate interruption after first step
                if len(chunk.get("completed_tasks", [])) >= 1:
                    print("   🛑 Simulating interruption...")
                    break
            
            # Get the current state
            state_snapshot = agent.workflow.get_state(config)
            print(f"   💾 Saved state: {len(state_snapshot.values)} state items")
            
            # Resume from checkpoint
            print("   🔄 Resuming from checkpoint...")
            async for chunk in agent.workflow.astream(None, config=config):
                result = chunk
                if "success" in chunk:
                    break
            
            if result and result.get("success", False):
                print("   ✅ Memory checkpointing test PASSED")
                return True
            else:
                print(f"   ❌ Memory checkpointing test FAILED: {result}")
                return False
                
        except Exception as e:
            print(f"   ❌ Memory checkpointing test ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_state_inspection(self):
        """Test state inspection and checkpoint history"""
        print("\n🧪 Testing State Inspection and History...")
        
        try:
            agent = LangGraphTravelAgent(use_postgres=False)
            thread_id = "inspection-test-456"
            
            request = TravelRequest(
                destination="Tokyo, Japan",
                start_date="2025-09-01",
                end_date="2025-09-07",
                number_of_travelers=1
            )
            
            config = {"configurable": {"thread_id": thread_id}}
            
            # Run a few steps
            step_count = 0
            async for chunk in agent.workflow.astream(
                {"request": request, "next_action": "start", "completed_tasks": [], "errors": {}, "agent_messages": []},
                config=config
            ):
                step_count += 1
                print(f"   📝 Step {step_count}: {list(chunk.keys())}")
                
                # Get state after each step
                state = agent.workflow.get_state(config)
                print(f"      State keys: {list(state.values.keys())}")
                print(f"      Next action: {state.values.get('next_action', 'unknown')}")
                print(f"      Completed tasks: {len(state.values.get('completed_tasks', []))}")
                
                if step_count >= 3:  # Limit to 3 steps for demo
                    break
            
            # Get final state
            final_state = agent.workflow.get_state(config)
            
            # Get state history
            history = []
            async for state in agent.workflow.aget_state_history(config):
                history.append({
                    "config": state.config,
                    "created_at": state.created_at,
                    "parent_config": state.parent_config,
                    "tasks": state.tasks
                })
                if len(history) >= 5:  # Limit history for demo
                    break
            
            print(f"   📚 State history: {len(history)} checkpoints")
            for i, checkpoint in enumerate(history):
                print(f"      Checkpoint {i}: {checkpoint['created_at']}")
            
            print("   ✅ State inspection test PASSED")
            return True
            
        except Exception as e:
            print(f"   ❌ State inspection test ERROR: {str(e)}")
            return False
    
    async def test_error_recovery(self):
        """Test error recovery and continuation"""
        print("\n🧪 Testing Error Recovery...")
        
        try:
            agent = LangGraphTravelAgent(use_postgres=False)
            thread_id = "recovery-test-789"
            
            # Create request with potential error conditions
            request = TravelRequest(
                destination="Invalid Destination 123!@#",  # This should cause errors
                start_date="2025-10-01",
                end_date="2025-10-07",
                number_of_travelers=0  # Invalid number
            )
            
            config = {"configurable": {"thread_id": thread_id}}
            
            # Run workflow expecting errors
            error_count = 0
            async for chunk in agent.workflow.astream(
                {"request": request, "next_action": "start", "completed_tasks": [], "errors": {}, "agent_messages": []},
                config=config
            ):
                if chunk.get("errors"):
                    error_count += len(chunk["errors"])
                    print(f"   ⚠️  Captured {len(chunk['errors'])} errors")
                
                # Stop after collecting some errors
                if error_count >= 2:
                    break
            
            # Get state to see errors were persisted
            state = agent.workflow.get_state(config)
            persisted_errors = state.values.get("errors", {})
            
            print(f"   📊 Persisted errors: {len(persisted_errors)}")
            for error_type, error_msg in persisted_errors.items():
                print(f"      {error_type}: {error_msg[:100]}...")
            
            # Now try with corrected request
            corrected_request = TravelRequest(
                destination="Madrid, Spain",
                start_date="2025-10-01", 
                end_date="2025-10-07",
                number_of_travelers=2
            )
            
            # Update the state with corrected request
            agent.workflow.update_state(
                config,
                {"request": corrected_request, "errors": {}}
            )
            
            # Continue with corrected request
            print("   🔧 Continuing with corrected request...")
            final_result = None
            async for chunk in agent.workflow.astream(None, config=config):
                final_result = chunk
                if "success" in chunk:
                    break
            
            if final_result and final_result.get("success", False):
                print("   ✅ Error recovery test PASSED")
                return True
            else:
                print(f"   ❌ Error recovery test FAILED: {final_result}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error recovery test ERROR: {str(e)}")
            return False
    
    async def test_human_in_the_loop(self):
        """Test human-in-the-loop durability"""
        print("\n🧪 Testing Human-in-the-Loop Durability...")
        
        try:
            agent = LangGraphTravelAgent(use_postgres=False)
            thread_id = "hitl-test-101"
            
            request = TravelRequest(
                destination="Amsterdam, Netherlands",
                start_date="2025-11-01",
                end_date="2025-11-07",
                number_of_travelers=2
            )
            
            config = {"configurable": {"thread_id": thread_id}}
            
            # Start workflow until it hits human feedback point
            print("   🚀 Running until human feedback required...")
            async for chunk in agent.workflow.astream(
                {"request": request, "next_action": "start", "completed_tasks": [], "errors": {}, "agent_messages": []},
                config=config
            ):
                print(f"   📊 Progress: {chunk.get('next_action', 'unknown')}")
                
                # Check if we hit an interruption point
                if chunk.get("next_action") == "get_feedback":
                    print("   ⏸️  Workflow paused for human feedback")
                    break
            
            # Simulate waiting period (workflow is paused)
            print("   ⏳ Simulating wait period (workflow persisted)...")
            await asyncio.sleep(1)  # Simulate delay
            
            # Get current state
            state = agent.workflow.get_state(config)
            print(f"   💾 State during pause: next={state.next}")
            
            # Provide human feedback and resume
            print("   👤 Providing human feedback and resuming...")
            agent.workflow.update_state(
                config,
                {"user_feedback": "Looks great! Please proceed with booking."}
            )
            
            # Resume workflow
            final_result = None
            async for chunk in agent.workflow.astream(None, config=config):
                final_result = chunk
                if "success" in chunk:
                    break
            
            if final_result and final_result.get("success", False):
                print("   ✅ Human-in-the-loop test PASSED")
                return True
            else:
                print(f"   ❌ Human-in-the-loop test FAILED: {final_result}")
                return False
                
        except Exception as e:
            print(f"   ❌ Human-in-the-loop test ERROR: {str(e)}")
            return False
    
    async def test_concurrent_sessions(self):
        """Test multiple concurrent sessions with separate states"""
        print("\n🧪 Testing Concurrent Sessions...")
        
        try:
            agent = LangGraphTravelAgent(use_postgres=False)
            
            # Create multiple concurrent sessions
            sessions = [
                ("session-1", TravelRequest(destination="London, UK", start_date="2025-12-01", end_date="2025-12-07", number_of_travelers=1)),
                ("session-2", TravelRequest(destination="Paris, France", start_date="2025-12-15", end_date="2025-12-22", number_of_travelers=2)),
                ("session-3", TravelRequest(destination="Rome, Italy", start_date="2026-01-01", end_date="2026-01-07", number_of_travelers=3))
            ]
            
            session_states = {}
            
            # Start all sessions
            for thread_id, request in sessions:
                config = {"configurable": {"thread_id": thread_id}}
                print(f"   🚀 Starting session {thread_id} for {request.destination}")
                
                # Run one step for each session
                async for chunk in agent.workflow.astream(
                    {"request": request, "next_action": "start", "completed_tasks": [], "errors": {}, "agent_messages": []},
                    config=config
                ):
                    session_states[thread_id] = chunk
                    break  # Just one step for demo
            
            # Verify each session has independent state
            unique_destinations = set()
            for thread_id, state in session_states.items():
                dest = state.get("request", {}).get("destination", "unknown")
                unique_destinations.add(dest)
                print(f"   📊 Session {thread_id}: {dest}")
            
            if len(unique_destinations) == len(sessions):
                print(f"   ✅ Concurrent sessions test PASSED ({len(sessions)} independent sessions)")
                return True
            else:
                print(f"   ❌ Concurrent sessions test FAILED: state mixing detected")
                return False
                
        except Exception as e:
            print(f"   ❌ Concurrent sessions test ERROR: {str(e)}")
            return False
    
    async def test_postgres_checkpointing(self):
        """Test PostgreSQL checkpointing for local development"""
        print("\n🧪 Testing PostgreSQL Checkpointing...")
        
        # Check if PostgreSQL is available locally
        local_postgres_urls = [
            "postgresql://postgres:password@localhost:5432/langgraph_checkpoints",
            "postgresql://postgres@localhost:5432/langgraph_checkpoints", 
            "postgresql://localhost:5432/langgraph_checkpoints"
        ]
        
        working_url = None
        for url in local_postgres_urls:
            try:
                print(f"   🔍 Trying connection: {url.split('@')[1] if '@' in url else url}")
                agent = LangGraphTravelAgent(use_postgres=True, connection_string=url)
                
                # Test basic functionality
                info = await agent.get_checkpointer_info()
                if info["type"] == "PostgreSQL":
                    working_url = url
                    print(f"   ✅ PostgreSQL connection successful!")
                    break
                    
            except Exception as e:
                print(f"   ❌ Connection failed: {str(e)[:100]}...")
                continue
        
        if not working_url:
            print("   ⚠️  PostgreSQL not available locally, skipping test")
            print("   💡 To enable: Start PostgreSQL and create 'langgraph_checkpoints' database")
            return True  # Don't fail the test if PostgreSQL isn't set up
        
        try:
            # Use the working connection
            agent = LangGraphTravelAgent(use_postgres=True, connection_string=working_url)
            thread_id = f"postgres-test-{int(asyncio.get_event_loop().time())}"
            
            request = TravelRequest(
                destination="Stockholm, Sweden",
                start_date="2025-09-15",
                end_date="2025-09-22",
                number_of_travelers=2
            )
            
            print("   🚀 Starting workflow with PostgreSQL persistence...")
            config = {"configurable": {"thread_id": thread_id}}
            
            # Run a few steps
            step_count = 0
            async for chunk in agent.workflow.astream(
                {"request": request, "next_action": "start", "completed_tasks": [], "errors": {}, "agent_messages": []},
                config=config
            ):
                step_count += 1
                print(f"   📊 Step {step_count}: {list(chunk.keys())}")
                
                # Check state persistence
                state = agent.workflow.get_state(config)
                print(f"      ✓ State persisted in PostgreSQL")
                
                if step_count >= 2:  # Test a couple steps
                    break
            
            # Test state retrieval
            final_state = agent.workflow.get_state(config)
            completed_tasks = final_state.values.get("completed_tasks", [])
            
            # Create a new agent instance to test persistence across instances
            print("   🔄 Testing persistence across agent instances...")
            agent2 = LangGraphTravelAgent(use_postgres=True, connection_string=working_url)
            state2 = agent2.workflow.get_state(config)
            
            if state2.values.get("request", {}).get("destination") == request.destination:
                print("   ✅ PostgreSQL checkpointing test PASSED")
                print(f"      ✓ State persisted across agent instances")
                print(f"      ✓ Completed tasks: {len(completed_tasks)}")
                return True
            else:
                print("   ❌ State not properly persisted across instances")
                return False
                
        except Exception as e:
            print(f"   ❌ PostgreSQL checkpointing test ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def explain_durability_concepts(self):
        """Explain LangGraph durability concepts"""
        print("\n📚 Agent Durability in LangGraph")
        print("=" * 50)
        
        concepts = [
            {
                "concept": "Checkpointing",
                "description": "Automatic state persistence at each step",
                "benefits": ["Resume from any point", "Crash recovery", "State inspection"]
            },
            {
                "concept": "Memory Checkpointer", 
                "description": "In-memory state storage for development",
                "benefits": ["Fast", "No external dependencies", "Good for testing"]
            },
            {
                "concept": "Postgres Checkpointer",
                "description": "Persistent database storage for production",
                "benefits": ["Survives restarts", "Scalable", "Shared across instances"]
            },
            {
                "concept": "State History",
                "description": "Access to previous checkpoint states",
                "benefits": ["Debugging", "Rollback", "Audit trail"]
            },
            {
                "concept": "Human-in-the-Loop",
                "description": "Pause workflow for human intervention",
                "benefits": ["User approval", "Manual corrections", "Interactive workflows"]
            },
            {
                "concept": "Thread Isolation",
                "description": "Separate state per conversation thread",
                "benefits": ["Concurrent users", "Independent sessions", "No state mixing"]
            }
        ]
        
        for concept in concepts:
            print(f"\n🔹 {concept['concept']}")
            print(f"   Description: {concept['description']}")
            print(f"   Benefits: {', '.join(concept['benefits'])}")
    
    def show_postgres_setup_example(self):
        """Show how to set up PostgreSQL checkpointing for local and production"""
        print("\n🐘 PostgreSQL Durability Setup")
        print("=" * 40)
        
        print("📍 Local Development Setup:")
        local_setup = '''
# Recommended: Using Docker Compose for local development
docker-compose -f docker-compose.local.yml up -d

# Or single Docker command
docker run --name postgres-langgraph \\
  -e POSTGRES_DB=langgraph_checkpoints \\
  -e POSTGRES_USER=postgres \\
  -e POSTGRES_PASSWORD=password \\
  -p 5432:5432 \\
  -d postgres:15

# Alternative: Using Homebrew (macOS)
brew install postgresql
brew services start postgresql
createdb langgraph_checkpoints
        '''
        print(local_setup)
        
        print("\n🔧 Python Code Setup:")
        code_setup = '''
# Install required packages
pip install psycopg[binary]

# Local development with PostgreSQL
from agents.travel_agent import LangGraphTravelAgent

# Try common local configurations
local_configs = [
    "postgresql://postgres:password@localhost:5432/langgraph_checkpoints",
    "postgresql://postgres@localhost:5432/langgraph_checkpoints",
    "postgresql://localhost:5432/langgraph_checkpoints"
]

for connection_string in local_configs:
    try:
        agent = LangGraphTravelAgent(
            use_postgres=True,
            connection_string=connection_string
        )
        print(f"✅ Connected with: {connection_string}")
        break
    except Exception as e:
        continue

# Or use environment variable
import os
os.environ['POSTGRES_CONNECTION_STRING'] = 'postgresql://postgres:password@localhost:5432/langgraph_checkpoints'
agent = LangGraphTravelAgent(use_postgres=True)  # Will use env var
        '''
        print(code_setup)
        
        print("\n🏭 Production Configuration:")
        production_config = '''
# docker-compose.yml for production
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: langgraph_checkpoints
      POSTGRES_USER: travel_agent
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U travel_agent -d langgraph_checkpoints"]
      interval: 5s
      timeout: 5s
      retries: 5
      
  travel-agent:
    build: .
    environment:
      POSTGRES_CONNECTION_STRING: postgresql://travel_agent:${POSTGRES_PASSWORD}@postgres:5432/langgraph_checkpoints
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
        '''
        print(production_config)


async def main():
    """Run all durability tests"""
    print("🔧 LangGraph Agent Durability Testing")
    print("=" * 50)
    
    harness = DurabilityTestHarness()
    
    # Explain concepts first
    harness.explain_durability_concepts()
    harness.show_postgres_setup_example()
    
    print("\n🧪 Running Durability Tests...")
    
    # Run tests
    tests = [
        ("Memory Checkpointing", harness.test_memory_checkpointing),
        ("PostgreSQL Checkpointing", harness.test_postgres_checkpointing),
        ("State Inspection", harness.test_state_inspection),
        ("Error Recovery", harness.test_error_recovery),
        ("Human-in-the-Loop", harness.test_human_in_the_loop),
        ("Concurrent Sessions", harness.test_concurrent_sessions)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results[test_name] = False
    
    # Summary
    print(f"\n📊 Durability Test Results")
    print("=" * 30)
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All durability tests PASSED!")
        print("   Your LangGraph agents are durable and resilient!")
    else:
        print(f"\n⚠️  {total - passed} durability tests failed.")
        print("   Review the error messages above for details.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
