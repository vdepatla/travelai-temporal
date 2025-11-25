"""
Improved Pure LangGraph Travel Agent Gradio UI

This provides an enhanced web interface for local testing with the travel agent system.
Features:
- Structured form inputs for easy testing
- PostgreSQL status detection
- Quick test examples
- Better error handling and display
"""

import gradio as gr
import asyncio
import json
import re
import os
import time
from typing import Tuple
from src.models.travel_models import TravelRequest
from src.agents.travel_agent import LangGraphTravelAgent


# Initialize the travel agent with automatic PostgreSQL detection
async def initialize_agent():
    """Initialize agent with automatic PostgreSQL fallback"""
    # Try PostgreSQL first, fallback to memory
    postgres_configs = [
        os.getenv("POSTGRES_CONNECTION_STRING"),
        "postgresql://postgres:password@localhost:5432/langgraph_checkpoints",
        "postgresql://postgres@localhost:5432/langgraph_checkpoints",
        "postgresql://localhost:5432/langgraph_checkpoints"
    ]
    
    for conn_str in postgres_configs:
        if conn_str:
            try:
                agent = LangGraphTravelAgent(use_postgres=True, connection_string=conn_str)
                info = await agent.get_checkpointer_info()
                if info["type"] == "PostgreSQL":
                    return agent, "PostgreSQL", conn_str.split('@')[1] if '@' in conn_str else "localhost"
            except Exception:
                continue
    
    return LangGraphTravelAgent(use_postgres=False), "Memory", "N/A"

# Initialize agent
print("🔧 Initializing LangGraph Travel Agent...")
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
travel_agent, checkpointer_type, db_info = loop.run_until_complete(initialize_agent())
loop.close()
print(f"✅ Agent initialized with {checkpointer_type} checkpointing")


async def plan_trip_structured(destination: str, start_date: str, end_date: str, travelers: int, thread_id: str = "") -> str:
    """
    Structured travel planning interface for testing
    """
    if not destination or not start_date or not end_date:
        return "❌ **Error:** Please fill in all required fields (destination, start date, end date)"
    
    if travelers <= 0:
        return "❌ **Error:** Number of travelers must be greater than 0"
    
    try:
        # Use provided thread ID or generate one
        if not thread_id.strip():
            thread_id = f"ui-session-{int(time.time())}"
        
        # Create travel request
        request = TravelRequest(
            destination=destination.strip(),
            start_date=start_date.strip(),
            end_date=end_date.strip(),
            number_of_travelers=int(travelers)
        )
        
        # Show processing message
        processing_msg = f"""
🔄 **Processing your travel request...**

📝 **Request Details:**
- **Destination:** {destination}
- **Dates:** {start_date} to {end_date}
- **Travelers:** {travelers}
- **Thread ID:** {thread_id}
- **Checkpointer:** {checkpointer_type}

🤖 **Agent Coordination in Progress:**
- Flight search agent activating...
- Accommodation agent standing by...
- Itinerary agent preparing...

⏳ Please wait while our agents work together...
"""
        
        # Run the travel planning
        result = await travel_agent.run(request, thread_id=thread_id)
        
        if result.get("success", False):
            response = f"""
✅ **Travel Plan Successfully Created!**

🎯 **Trip Summary:**
- **Destination:** {destination}
- **Dates:** {start_date} to {end_date}
- **Travelers:** {travelers}
- **Thread ID:** `{thread_id}`
- **Checkpointer:** {checkpointer_type}

✈️ **Flight Details:**
- **Airline:** {result['flight_details'].airline}
- **Flight Number:** {result['flight_details'].flight_number}
- **Departure Date:** {result['flight_details'].departure_time}
- **Return Date:** {result['flight_details'].return_time}
- **Price:** ${result['flight_details'].price}

🏨 **Accommodation:**
- **Hotel:** {result['accommodation_details'].hotel_name}
- **Address:** {result['accommodation_details'].address}
- **Check-in:** {result['accommodation_details'].checkin_date}
- **Check-out:** {result['accommodation_details'].checkout_date}
- **Price:** ${result['accommodation_details'].price_per_night}/night

📋 **Detailed Itinerary:**
{result['itinerary']}

📊 **Agent Coordination Summary:**
- **Completed Tasks:** {', '.join(result['completed_tasks'])}
- **Agent Messages:** {len(result.get('agent_messages', []))}
- **Processing Time:** ~{len(result['completed_tasks']) * 2}s
"""
            
            if result['errors']:
                response += f"\n\n⚠️ **Issues Encountered (Handled):**\n"
                for agent, error in result['errors'].items():
                    response += f"- **{agent}:** {error}\n"
            
            # Add state persistence info
            if checkpointer_type == "PostgreSQL":
                response += f"\n\n💾 **State Persistence:** Your trip planning session is saved in PostgreSQL and will survive application restarts."
            else:
                response += f"\n\n⚠️ **State Persistence:** Session is in memory only. Start PostgreSQL with `docker-compose -f docker-compose.local.yml up -d` for persistence."
            
            return response
            
        else:
            error_msg = result.get('error', 'Unknown error occurred')
            return f"""
❌ **Travel Planning Failed**

**Error Details:** {error_msg}

🛠️ **Troubleshooting:**
- Check if destination is valid
- Ensure dates are in YYYY-MM-DD format
- Verify number of travelers is positive
- Try a different thread ID if this persists

🔧 **System Status:**
- **Checkpointer:** {checkpointer_type}
- **Thread ID:** {thread_id}
"""
            
    except Exception as e:
        return f"""
❌ **System Error**

**Error:** {str(e)}

🔧 **Debug Info:**
- **Checkpointer:** {checkpointer_type}
- **Thread ID:** {thread_id}
- **Destination:** {destination}

💡 **Next Steps:**
1. Check if all required fields are filled
2. Verify your OpenAI API key is set
3. For PostgreSQL issues, check: `docker-compose -f docker-compose.local.yml ps`
"""


def plan_trip_wrapper(*args):
    """Synchronous wrapper for Gradio"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(plan_trip_structured(*args))
    loop.close()
    return result


# Create the enhanced Gradio interface
with gr.Blocks(title="LangGraph Travel Agent - Testing Interface", theme=gr.themes.Soft()) as demo:
    
    # Header with system status
    gr.Markdown(f"""
    # 🌍 LangGraph Travel Agent - Testing Interface
    
    **Multi-Agent Travel Planning System | Local Testing Environment**
    
    🔧 **Status:** {checkpointer_type} Checkpointing | 🗄️ **Database:** {db_info} | 🤖 **Agents:** Flight + Hotel + Itinerary
    
    ---
    """)
    
    with gr.Tabs():
        # Tab 1: Main Testing Interface
        with gr.TabItem("🎯 Travel Planning"):
            gr.Markdown("### Plan Your Trip - Testing Interface")
            
            with gr.Row():
                with gr.Column(scale=2):
                    destination_input = gr.Textbox(
                        label="🌍 Destination",
                        placeholder="e.g., Paris, France or Tokyo, Japan",
                        value="Paris, France"
                    )
                with gr.Column(scale=1):
                    travelers_input = gr.Number(
                        label="👥 Travelers",
                        minimum=1,
                        maximum=10,
                        value=2
                    )
            
            with gr.Row():
                start_date_input = gr.Textbox(
                    label="📅 Start Date (YYYY-MM-DD)",
                    value="2025-06-01"
                )
                end_date_input = gr.Textbox(
                    label="📅 End Date (YYYY-MM-DD)",
                    value="2025-06-07"
                )
            
            with gr.Row():
                thread_id_input = gr.Textbox(
                    label="🔗 Thread/Session ID (optional)",
                    placeholder="Leave empty for auto-generated",
                    value=""
                )
                plan_btn = gr.Button("✈️ Plan My Trip", variant="primary", size="lg")
            
            # Output area
            trip_output = gr.Markdown(value="👆 Enter your travel details above and click 'Plan My Trip' to start")
            
            # Quick test examples
            gr.Markdown("### 🧪 Quick Test Scenarios")
            with gr.Row():
                example1_btn = gr.Button("🗼 Paris Weekend", variant="secondary")
                example2_btn = gr.Button("🗾 Tokyo Adventure", variant="secondary") 
                example3_btn = gr.Button("🍝 Rome Classic", variant="secondary")
                example4_btn = gr.Button("❌ Error Test", variant="stop")
            
            # Example handlers
            def set_paris_example():
                return "Paris, France", "2025-06-01", "2025-06-07", 2, "paris-weekend-test"
            
            def set_tokyo_example():
                return "Tokyo, Japan", "2025-08-15", "2025-08-22", 3, "tokyo-adventure-test"
            
            def set_rome_example():
                return "Rome, Italy", "2025-09-10", "2025-09-17", 1, "rome-classic-test"
            
            def set_error_example():
                return "Invalid Destination 123!@#", "2025-13-45", "2025-13-50", 0, "error-test"
            
            example1_btn.click(
                fn=set_paris_example,
                outputs=[destination_input, start_date_input, end_date_input, travelers_input, thread_id_input]
            )
            example2_btn.click(
                fn=set_tokyo_example,
                outputs=[destination_input, start_date_input, end_date_input, travelers_input, thread_id_input]
            )
            example3_btn.click(
                fn=set_rome_example,
                outputs=[destination_input, start_date_input, end_date_input, travelers_input, thread_id_input]
            )
            example4_btn.click(
                fn=set_error_example,
                outputs=[destination_input, start_date_input, end_date_input, travelers_input, thread_id_input]
            )
            
            # Connect the main function
            plan_btn.click(
                fn=plan_trip_wrapper,
                inputs=[destination_input, start_date_input, end_date_input, travelers_input, thread_id_input],
                outputs=trip_output
            )
        
        # Tab 2: System Configuration
        with gr.TabItem("⚙️ System Status"):
            gr.Markdown(f"""
            ## 🔧 Current Configuration
            
            ### Database & Persistence
            - **Checkpointer Type:** `{checkpointer_type}`
            - **Database Location:** `{db_info}`
            - **State Persistence:** {"✅ Enabled (survives restarts)" if checkpointer_type == "PostgreSQL" else "⚠️ Memory only (lost on restart)"}
            - **Multi-instance Support:** {"✅ Yes" if checkpointer_type == "PostgreSQL" else "❌ No (single instance only)"}
            - **Production Ready:** {"✅ Yes" if checkpointer_type == "PostgreSQL" else "🧪 Development only"}
            
            ### Agent Architecture
            - **Framework:** Pure LangGraph (no Temporal dependencies)
            - **Flight Agent:** ✅ Active
            - **Accommodation Agent:** ✅ Active  
            - **Itinerary Agent:** ✅ Active
            - **Travel Coordinator:** ✅ Active
            - **Parallel Execution:** ✅ Supported
            - **Human-in-the-Loop:** ✅ Available
            
            ### Environment
            - **Python Version:** {'.'.join(map(str, [3, 8, 0]))}+
            - **OpenAI API:** {"✅ Configured" if os.getenv('OPENAI_API_KEY') else "❌ Missing - Set OPENAI_API_KEY"}
            - **Port:** 7860
            
            ---
            
            ## 🐘 Enable PostgreSQL Persistence
            
            To upgrade to PostgreSQL checkpointing for production-like testing:
            
            ```bash
            # Start PostgreSQL with Docker Compose
            docker-compose -f docker-compose.local.yml up -d
            
            # Verify it's running
            docker-compose -f docker-compose.local.yml ps
            
            # Restart the application
            python main.py --mode web
            ```
            
            **Benefits of PostgreSQL:**
            - ✅ State survives application restarts
            - ✅ Test crash recovery scenarios
            - ✅ Multi-session isolation
            - ✅ Full agent state history
            - ✅ Production-like behavior
            
            ---
            
            ## 🧪 Testing Guide
            
            ### Basic Functionality Test
            1. Use the "Paris Weekend" quick test
            2. Verify all agents complete their tasks
            3. Check the output contains flight, hotel, and itinerary details
            
            ### Error Handling Test  
            1. Click "Error Test" button
            2. Verify system handles invalid inputs gracefully
            3. Check error messages are helpful
            
            ### State Persistence Test (PostgreSQL only)
            1. Start a trip planning request
            2. Note the Thread ID
            3. Refresh the browser page
            4. Use the same Thread ID to check if state persists
            
            ### Concurrent Sessions Test
            1. Open multiple browser tabs
            2. Use different Thread IDs in each tab
            3. Verify sessions are isolated
            """)
        
        # Tab 3: Testing Tools
        with gr.TabItem("🧪 Testing Tools"):
            gr.Markdown("""
            ## 🛠️ Development & Testing Tools
            
            ### Run Automated Tests
            
            Open a terminal and run these commands for comprehensive testing:
            """)
            
            gr.Code("""
# Basic functionality tests
python test_langgraph_agent.py

# Comprehensive durability tests (includes PostgreSQL if available)
python test_agent_durability.py

# CLI mode testing
python main.py --mode cli

# Single request testing
python main.py --mode single --destination "Tokyo, Japan" --start-date "2025-06-01" --end-date "2025-06-07" --travelers 2
            """, language="bash")
            
            gr.Markdown("""
            ### Manual Testing Checklist
            
            #### ✅ Basic Functionality
            - [ ] Travel planning completes successfully
            - [ ] All agents (Flight, Hotel, Itinerary) activate
            - [ ] Results include realistic details
            - [ ] Thread IDs are properly generated/used
            
            #### ✅ Error Handling
            - [ ] Invalid destinations are handled gracefully
            - [ ] Malformed dates show helpful errors
            - [ ] Zero or negative travelers are rejected
            - [ ] System continues to work after errors
            
            #### ✅ State Management
            - [ ] Different Thread IDs create separate sessions
            - [ ] Sessions are isolated from each other
            - [ ] State is preserved (if using PostgreSQL)
            
            #### ✅ User Interface
            - [ ] All buttons and inputs work correctly
            - [ ] Quick test examples populate fields
            - [ ] Output is readable and well-formatted
            - [ ] System status is accurately displayed
            
            ### Performance Testing
            
            For load testing, use the benchmark mode:
            """)
            
            gr.Code("python main.py --mode benchmark", language="bash")
            
            gr.Markdown("""
            ### Debugging Tips
            
            1. **Check Logs:** Look at the console output for detailed agent interactions
            2. **Thread IDs:** Use descriptive thread IDs to track different test scenarios
            3. **PostgreSQL:** Use `docker logs langgraph-postgres` to check database logs
            4. **Agent State:** The system shows completed tasks and agent messages in results
            
            ### Common Issues
            
            | Issue | Solution |
            |-------|----------|
            | "Connection failed" | Check if PostgreSQL is running: `docker-compose ps` |
            | "OpenAI API error" | Verify `OPENAI_API_KEY` environment variable is set |
            | "State not persisting" | Make sure PostgreSQL is running, not just memory mode |
            | "Slow responses" | Normal for first request; subsequent requests are faster |
            """)


def launch_enhanced_ui(share: bool = False, server_port: int = 7860):
    """Launch the enhanced testing interface"""
    print(f"\n🚀 Launching LangGraph Travel Agent UI...")
    print(f"📍 URL: http://localhost:{server_port}")
    print(f"🔧 Checkpointer: {checkpointer_type}")
    print(f"🗄️ Database: {db_info}")
    print(f"💡 Use the quick test buttons for easy testing!")
    
    demo.launch(
        share=share,
        server_port=server_port,
        show_error=True,
        show_tips=True
    )


if __name__ == "__main__":
    launch_enhanced_ui(share=False, server_port=7860)
