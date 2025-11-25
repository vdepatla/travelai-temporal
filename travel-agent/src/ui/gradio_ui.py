"""
Pure LangGraph Travel Agent Gradio UI

This provides a web interface for the travel agent system
using only LangGraph, with no Temporal dependencies.
"""

import gradio as gr
import asyncio
import json
import re
import os
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
                    return agent, "PostgreSQL"
            except Exception:
                continue
    
    return LangGraphTravelAgent(use_postgres=False), "Memory"

# Initialize agent
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
travel_agent, checkpointer_type = loop.run_until_complete(initialize_agent())
loop.close()


def parse_travel_request(message: str) -> Tuple[str, str, str, int]:
    """
    Parse natural language travel request into structured data
    
    Args:
        message: Natural language travel request
        
    Returns:
        Tuple of (destination, start_date, end_date, number_of_travelers)
    """
    destination = None
    start_date = None
    end_date = None
    number_of_travelers = 1
    
    # Example: "Book a trip to Paris for 2 people from Jan 5 to Jan 10"
    dest_match = re.search(r'to ([A-Za-z ]+)', message, re.IGNORECASE)
    if dest_match:
        destination = dest_match.group(1).strip()
    
    num_match = re.search(r'for (\d+) (?:people|person|travelers?|travellers?)', message, re.IGNORECASE)
    if num_match:
        number_of_travelers = int(num_match.group(1))
    
    date_match = re.search(r'from ([A-Za-z0-9 -]+) to ([A-Za-z0-9 -]+)', message, re.IGNORECASE)
    if date_match:
        start_date = date_match.group(1).strip()
        end_date = date_match.group(2).strip()
    
    # Fallbacks
    if not destination:
        destination = "Paris, France"  # Default destination
    if not start_date:
        start_date = "2025-06-01"
    if not end_date:
        end_date = "2025-06-07"
    
    return destination, start_date, end_date, number_of_travelers


async def run_travel_planning(destination: str, start_date: str, end_date: str, number_of_travelers: int) -> str:
    """
    Run the travel planning workflow
    
    Args:
        destination: Travel destination
        start_date: Trip start date
        end_date: Trip end date
        number_of_travelers: Number of travelers
        
    Returns:
        Formatted travel plan result
    """
    try:
        # Create travel request
        request = TravelRequest(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            number_of_travelers=number_of_travelers
        )
        
        # Run the travel agent
        result = await travel_agent.run(request)
        
        if result["success"]:
            # Format the response nicely
            response = f"""
🎉 **Travel Plan Successfully Created!**

✈️ **Flight Details:**
- Airline: {result['flight_details'].airline}
- Flight Number: {result['flight_details'].flight_number}
- Departure: {result['flight_details'].departure_date}
- Return: {result['flight_details'].return_date}
- Price: ${result['flight_details'].price}

🏨 **Accommodation:**
- Hotel: {result['accommodation_details'].hotel_name}
- Check-in: {result['accommodation_details'].check_in_date}
- Check-out: {result['accommodation_details'].check_out_date}
- Price per night: ${result['accommodation_details'].price_per_night}
- Total price: ${result['accommodation_details'].total_price}

📋 **Itinerary:**
{result['itinerary']}

📊 **Execution Summary:**
- Total agents used: {result['execution_summary']['total_agents_used']}
- Successful tasks: {result['execution_summary']['successful_tasks']}
- Failed tasks: {result['execution_summary']['failed_tasks']}
- Parallel execution: {'Yes' if result['execution_summary']['parallel_execution'] else 'No'}

🔍 **Agent Activity:**
"""
            
            # Add agent messages
            for msg in result['agent_messages'][-5:]:  # Show last 5 messages
                response += f"\n- {msg['agent']}: {msg['action']} - {msg.get('message', 'N/A')}"
            
            if result['errors']:
                response += f"\n\n⚠️ **Errors encountered:**\n"
                for agent, error in result['errors'].items():
                    response += f"- {agent}: {error}\n"
            
            return response
            
        else:
            return f"❌ **Error:** {result['error']}"
            
    except Exception as e:
        return f"❌ **System Error:** {str(e)}"


def natural_language_travel_agent(message: str) -> str:
    """
    Main interface function for Gradio
    
    Args:
        message: Natural language travel request
        
    Returns:
        Formatted travel plan or error message
    """
    try:
        # Parse the message
        destination, start_date, end_date, number_of_travelers = parse_travel_request(message)
        
        # Show what we understood
        parsing_result = f"""
📝 **Understanding your request:**
- Destination: {destination}
- Start Date: {start_date}
- End Date: {end_date}
- Number of Travelers: {number_of_travelers}

🔄 **Planning your trip...**

"""
        
        # Run the travel planning (synchronously for Gradio)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            run_travel_planning(destination, start_date, end_date, number_of_travelers)
        )
        loop.close()
        
        return parsing_result + result
        
    except Exception as e:
        return f"❌ **Error processing request:** {str(e)}"


async def stream_travel_planning(message: str):
    """
    Streaming version for real-time updates (for future use)
    """
    destination, start_date, end_date, number_of_travelers = parse_travel_request(message)
    
    request = TravelRequest(
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        number_of_travelers=number_of_travelers
    )
    
    async for update in travel_agent.stream(request):
        yield f"🔄 Update: {json.dumps(update, indent=2, default=str)}\n"


async def plan_trip_structured(destination: str, start_date: str, end_date: str, travelers: int, thread_id: str = "") -> str:
    """
    Structured travel planning interface
    """
    if not destination or not start_date or not end_date:
        return "❌ **Error:** Please fill in all required fields"
    
    if travelers <= 0:
        return "❌ **Error:** Number of travelers must be greater than 0"
    
    try:
        # Use provided thread ID or generate one
        if not thread_id:
            import time
            thread_id = f"ui-session-{int(time.time())}"
        
        # Create travel request
        request = TravelRequest(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            number_of_travelers=travelers
        )
        
        # Run the travel planning
        result = await travel_agent.run(request, thread_id=thread_id)
        
        if result.get("success", False):
            response = f"""
✅ **Travel Plan Complete!**

🎯 **Trip Summary:**
- **Destination:** {destination}
- **Dates:** {start_date} to {end_date}
- **Travelers:** {travelers}
- **Thread ID:** {thread_id}

✈️ **Flight Details:**
- **Airline:** {result['flight_details'].airline}
- **Flight:** {result['flight_details'].flight_number}
- **Departure:** {result['flight_details'].departure_time}
- **Return:** {result['flight_details'].return_time}
- **Price:** ${result['flight_details'].price}

🏨 **Accommodation:**
- **Hotel:** {result['accommodation_details'].hotel_name}
- **Address:** {result['accommodation_details'].address}
- **Check-in:** {result['accommodation_details'].checkin_date}
- **Check-out:** {result['accommodation_details'].checkout_date}
- **Price:** ${result['accommodation_details'].price_per_night}/night

📋 **Itinerary:**
{result['itinerary']}

📊 **Agent Activity:**
- **Completed Tasks:** {', '.join(result['completed_tasks'])}
- **Total Agent Messages:** {len(result.get('agent_messages', []))}
"""
            
            if result['errors']:
                response += f"\n\n⚠️ **Errors encountered:**\n"
                for agent, error in result['errors'].items():
                    response += f"- {agent}: {error}\n"
            
            return response
            
        else:
            return f"❌ **Error:** {result.get('error', 'Unknown error occurred')}"
            
    except Exception as e:
        return f"❌ **System Error:** {str(e)}"


# Create the Gradio interface
with gr.Blocks(title="LangGraph Travel Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🌍 LangGraph Travel Agent
    
    Welcome to your AI-powered travel planning assistant! This system uses multiple specialized agents
    working together to plan your perfect trip.
    
    **Features:**
    - ✈️ Flight search and booking
    - 🏨 Accommodation recommendations
    - 📋 Comprehensive itinerary creation
    - 🤖 Multi-agent coordination
    - 🔄 Parallel processing for faster results
    
    **How to use:** Just describe your travel plans in natural language!
    """)
    
    with gr.Row():
        with gr.Column():
            message_input = gr.Textbox(
                label="Tell me about your trip",
                lines=3,
                placeholder="e.g., 'Book a trip to Tokyo for 2 people from June 1st to June 7th'",
                info="Describe your travel plans in natural language"
            )
            
            submit_btn = gr.Button("Plan My Trip 🚀", variant="primary")
            
        with gr.Column():
            gr.Markdown("""
            ### Example Requests:
            - "Plan a trip to Paris for 2 people from June 1 to June 7"
            - "I want to visit Tokyo for 4 travelers from Dec 15 to Dec 22"
            - "Book a vacation to Bali for 1 person from March 10 to March 17"
            """)
    
    output = gr.Textbox(
        label="Your Travel Plan",
        lines=20,
        max_lines=30,
        show_copy_button=True,
        interactive=False
    )
    
    # Examples for quick testing
    gr.Examples(
        examples=[
            ["Plan a trip to Paris for 2 people from June 1 to June 7"],
            ["I want to visit Tokyo for 4 travelers from December 15 to December 22"],
            ["Book a vacation to Bali for 1 person from March 10 to March 17"],
            ["Plan a family trip to London for 3 people from August 5 to August 12"]
        ],
        inputs=message_input,
        label="Try these examples:"
    )
    
    # Connect the interface
    submit_btn.click(
        fn=natural_language_travel_agent,
        inputs=message_input,
        outputs=output
    )
    
    message_input.submit(
        fn=natural_language_travel_agent,
        inputs=message_input,
        outputs=output
    )
    
    gr.Markdown("""
    ---
    ### 🔧 System Architecture
    This travel agent uses **pure LangGraph** for multi-agent coordination:
    - **Flight Agent**: Specialized in flight search and booking
    - **Accommodation Agent**: Expert in hotel recommendations and booking
    - **Itinerary Agent**: Creates comprehensive travel itineraries
    - **Supervisor Agent**: Coordinates all agents and manages workflow
    
    **Benefits of LangGraph:**
    - ✅ AI-native workflow management
    - ✅ Built-in state persistence
    - ✅ Parallel agent execution
    - ✅ Human-in-the-loop support
    - ✅ Real-time streaming capabilities
    """)


def launch_ui(share: bool = False, server_port: int = 7860):
    """
    Launch the Gradio interface
    
    Args:
        share: Whether to create a public sharing link
        server_port: Port to run the server on
    """
    demo.launch(
        share=share,
        server_port=server_port,
        show_error=True,
        show_tips=True
    )


if __name__ == "__main__":
    launch_ui(share=False, server_port=7860)