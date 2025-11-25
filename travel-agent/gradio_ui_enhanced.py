"""
Natural Language Travel Chatbot - Gradio UI

This provides a conversational chat interface for the LangGraph travel agent.
Features:
- Natural language chat interface
- Real-time conversation with AI travel assistant
- Memory persistence across chat sessions
- Quick examples and structured fallback
"""

import gradio as gr
import asyncio
import json
import re
import os
import time
import uuid
from typing import List, Tuple, Dict, Any
from src.models.travel_models import TravelRequest
from src.agents.travel_agent import LangGraphTravelAgent

# Global variables for agent and chat state
travel_agent = None
checkpointer_type = "Memory"
db_info = "N/A"

def get_or_create_agent():
    """Get or create the travel agent lazily"""
    global travel_agent, checkpointer_type, db_info
    
    if travel_agent is None:
        try:
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
                        travel_agent = agent
                        checkpointer_type = "PostgreSQL"
                        db_info = conn_str.split('@')[1] if '@' in conn_str else "localhost"
                        return travel_agent, checkpointer_type, db_info
                    except Exception:
                        continue
            
            # Fallback to memory
            travel_agent = LangGraphTravelAgent(use_postgres=False)
            checkpointer_type = "Memory"
            db_info = "N/A"
        except Exception as e:
            print(f"❌ Error initializing agent: {e}")
            travel_agent = None
    
    return travel_agent, checkpointer_type, db_info

def extract_travel_details(message: str) -> Dict[str, Any]:
    """Extract travel details from natural language message"""
    details = {
        "destination": None,
        "start_date": None,
        "end_date": None,
        "travelers": 1
    }
    
    # Simple regex patterns for common travel queries
    dest_patterns = [
        r"to\s+([^,\n]+)",
        r"visit\s+([^,\n]+)",
        r"trip\s+to\s+([^,\n]+)",
        r"going\s+to\s+([^,\n]+)",
        r"travel\s+to\s+([^,\n]+)"
    ]
    
    for pattern in dest_patterns:
        match = re.search(pattern, message.lower())
        if match:
            details["destination"] = match.group(1).strip().title()
            break
    
    # Look for dates
    date_patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{1,2}/\d{1,2}/\d{4})",
        r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}[,\s]*\d{4}"
    ]
    
    dates_found = []
    for pattern in date_patterns:
        matches = re.findall(pattern, message.lower())
        dates_found.extend(matches)
    
    if len(dates_found) >= 2:
        details["start_date"] = dates_found[0]
        details["end_date"] = dates_found[1]
    elif len(dates_found) == 1:
        details["start_date"] = dates_found[0]
    
    # Look for number of travelers
    traveler_patterns = [
        r"(\d+)\s+(?:people|travelers|persons|guests)",
        r"for\s+(\d+)",
        r"(\d+)\s+of\s+us"
    ]
    
    for pattern in traveler_patterns:
        match = re.search(pattern, message.lower())
        if match:
            details["travelers"] = int(match.group(1))
            break
    
    return details

async def chat_with_agent(message: str, history: List[Tuple[str, str]], session_id: str) -> Tuple[List[Tuple[str, str]], str]:
    """
    Process chat message and return updated history
    """
    if not message.strip():
        return history, ""
    
    try:
        agent, _, _ = get_or_create_agent()
        if agent is None:
            error_response = "❌ Sorry, I'm having trouble starting up. Please try again."
            history.append((message, error_response))
            return history, ""
        
        # Extract travel details from the message
        travel_details = extract_travel_details(message)
        
        # Determine if this is a travel planning request
        travel_keywords = ["trip", "travel", "vacation", "holiday", "visit", "flight", "hotel", "itinerary", "plan"]
        is_travel_request = any(keyword in message.lower() for keyword in travel_keywords)
        
        if is_travel_request and travel_details["destination"]:
            # This looks like a travel planning request
            start_date_display = travel_details.get('start_date', 'I will use default dates')
            end_date_display = travel_details.get('end_date', 'I will use default dates')
            thinking_response = f"""🤔 I understand you want to plan a trip! Let me help you with that.

📍 **Destination**: {travel_details['destination']}
📅 **Dates**: {start_date_display} to {end_date_display}
👥 **Travelers**: {travel_details['travelers']}

🔄 Let me search for flights, hotels, and create an itinerary for you..."""
            
            history.append((message, thinking_response))
            
            # Create travel request
            request = TravelRequest(
                destination=travel_details["destination"],
                start_date=travel_details.get("start_date") or "2025-06-01",
                end_date=travel_details.get("end_date") or "2025-06-07",
                number_of_travelers=travel_details["travelers"]
            )
            
            # Process with travel agent
            result = await agent.run(request, thread_id=session_id)
            
            if result["success"]:
                flight_airline = result['flight_details'].airline if result.get('flight_details') else 'Not found'
                flight_number = result['flight_details'].flight_number if result.get('flight_details') else 'N/A'
                flight_price = result['flight_details'].price if result.get('flight_details') else 'N/A'
                
                hotel_name = result['accommodation_details'].hotel_name if result.get('accommodation_details') else 'Not found'
                hotel_checkin = result['accommodation_details'].check_in_date if result.get('accommodation_details') else 'N/A'
                hotel_price = result['accommodation_details'].total_price if result.get('accommodation_details') else 'N/A'
                
                itinerary_text = result.get('itinerary', 'Detailed itinerary will be provided upon booking confirmation.')
                
                response = f"""✅ **Perfect! I've planned your trip to {travel_details['destination']}!**

✈️ **Flight Details:**
• Airline: {flight_airline}
• Flight: {flight_number}
• Price: ${flight_price}

🏨 **Hotel Details:**
• Hotel: {hotel_name}
• Check-in: {hotel_checkin}
• Price: ${hotel_price}

📋 **Your Itinerary:**
{itinerary_text}

💬 **What would you like to do next?**
• Modify any part of this plan
• Get more details about activities
• Ask about local recommendations
• Start planning another trip"""
                
                # Update the last response
                history[-1] = (history[-1][0], response)
                
            else:
                error_response = f"❌ I encountered an issue planning your trip: {result.get('error', 'Unknown error')}"
                history[-1] = (history[-1][0], error_response)
        
        else:
            # General travel chat or question
            if any(word in message.lower() for word in ["hello", "hi", "hey", "start"]):
                response = """👋 **Hello! I'm your AI Travel Assistant!**

I can help you plan amazing trips around the world! Just tell me:

💭 **Try saying something like:**
• "I want to plan a trip to Paris for 2 people"
• "Help me visit Tokyo from June 1st to June 7th"
• "Plan a vacation to Rome for 3 travelers"
• "I need a weekend getaway to Barcelona"

🌍 **I can help you with:**
• ✈️ Finding flights
• 🏨 Booking hotels
• 📋 Creating detailed itineraries
• 🎯 Local recommendations

**What destination are you dreaming of visiting?**"""
                
            elif any(word in message.lower() for word in ["help", "what", "how"]):
                response = """🤝 **How I Can Help You:**

🗣️ **Just talk naturally!** Tell me about your travel plans in plain English.

**Examples of what you can say:**
• "I want to go to Japan next month"
• "Plan a romantic trip to Paris for 2 people"
• "Help me visit New York from December 15 to 20"
• "I need a family vacation to Orlando for 4 people"

🎯 **I'll automatically:**
• Find the best flights
• Recommend great hotels
• Create a personalized itinerary
• Suggest local activities

**Ready to start planning? Just tell me where you'd like to go!**"""
                
            else:
                # Generic helpful response
                response = """🤔 I'd love to help you with your travel plans! 

To get started, try telling me:
• Where you want to go
• When you'd like to travel
• How many people are traveling

For example: *"I want to plan a trip to Barcelona for 2 people in July"*

**What destination interests you?** ✈️"""
        
            history.append((message, response))
    
    except Exception as e:
        error_response = f"❌ Sorry, I encountered an error: {str(e)}"
        history.append((message, error_response))
    
    return history, ""

def start_new_session():
    """Start a new chat session"""
    session_id = str(uuid.uuid4())
    welcome_message = """🌍 **Welcome to your AI Travel Assistant!**

I'm here to help you plan amazing trips around the world!

💭 **Just tell me about your travel plans in natural language:**
• "I want to visit Paris next month"
• "Plan a trip to Tokyo for 2 people" 
• "Help me find a weekend getaway to Rome"

**Where would you like to travel?** ✈️"""
    
    return [("👋 Start Planning", welcome_message)], session_id

def clear_chat():
    """Clear the chat and start fresh"""
    return start_new_session()

# Create the chat interface
def create_chat_interface():
    """Create the main chat interface"""
    with gr.Blocks(title="AI Travel Assistant - Chat") as demo:
        gr.Markdown("""
        # 🌍 AI Travel Assistant - Natural Language Chat
        
        **Talk to your personal AI travel agent in natural language!**
        
        🔧 **Status:** Memory Checkpointing | 🤖 **Multi-Agent System:** Flight + Hotel + Itinerary
        """)
        
        with gr.Row():
            with gr.Column(scale=4):
                # Chat interface
                chatbot = gr.Chatbot(
                    value=[],
                    height=500,
                    show_label=False,
                    container=True
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="💭 Tell me about your travel plans... (e.g., 'I want to visit Paris next month')",
                        show_label=False,
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary")
                
                with gr.Row():
                    clear_btn = gr.Button("🗑️ Clear Chat", size="sm")
                    new_session_btn = gr.Button("🔄 New Session", size="sm")
            
            with gr.Column(scale=1):
                gr.Markdown("### 💡 Quick Examples")
                
                example1 = gr.Button("🗼 'Plan a trip to Paris'", size="sm")
                example2 = gr.Button("🍕 'Visit Italy for a week'", size="sm") 
                example3 = gr.Button("🌸 'Japan trip for 2 people'", size="sm")
                example4 = gr.Button("🏖️ 'Beach vacation to Bali'", size="sm")
                
                gr.Markdown("### ℹ️ How to Chat")
                gr.Markdown("""
                **Just talk naturally!**
                
                ✅ "I want to go to Tokyo"
                ✅ "Plan a romantic trip to Paris"
                ✅ "Family vacation for 4 to Orlando"
                ✅ "Weekend in Barcelona"
                
                I'll understand and help plan your perfect trip!
                """)
        
        # Session state
        session_state = gr.State()
        
        # Initialize session on load
        demo.load(lambda: start_new_session(), outputs=[chatbot, session_state])
        
        # Chat functionality
        def handle_message(message, history, session_id):
            if not session_id:
                session_id = str(uuid.uuid4())
            return asyncio.run(chat_with_agent(message, history, session_id)), session_id
        
        msg.submit(handle_message, [msg, chatbot, session_state], [chatbot, session_state])
        send_btn.click(handle_message, [msg, chatbot, session_state], [chatbot, session_state])
        
        # Clear message after sending
        msg.submit(lambda: "", outputs=msg)
        send_btn.click(lambda: "", outputs=msg)
        
        # Clear chat
        clear_btn.click(clear_chat, outputs=[chatbot, session_state])
        new_session_btn.click(clear_chat, outputs=[chatbot, session_state])
        
        # Example buttons
        def send_example(example_text, history, session_id):
            return handle_message(example_text, history, session_id)
        
        example1.click(lambda h, s: send_example("Plan a trip to Paris", h, s), [chatbot, session_state], [chatbot, session_state])
        example2.click(lambda h, s: send_example("Visit Italy for a week", h, s), [chatbot, session_state], [chatbot, session_state])
        example3.click(lambda h, s: send_example("Japan trip for 2 people", h, s), [chatbot, session_state], [chatbot, session_state])
        example4.click(lambda h, s: send_example("Beach vacation to Bali", h, s), [chatbot, session_state], [chatbot, session_state])
        
        return demo


def launch_enhanced_ui(share: bool = False, server_port: int = 7860):
    """
    Launch the enhanced natural language chat UI
    """
    agent, checkpointer_type, db_info = get_or_create_agent()
    
    print("🌐 Starting AI Travel Assistant Chat Interface...")
    print(f"📍 URL: http://localhost:{server_port}")
    print(f"🔧 Checkpointer: {checkpointer_type}")
    print(f"🗄️ Database: {db_info}")
    print(f"💬 Ready for natural language travel conversations!")
    
    demo = create_chat_interface()
    demo.launch(
        share=share,
        server_port=server_port,
        show_error=True
    )


if __name__ == "__main__":
    launch_enhanced_ui(share=False, server_port=7860)
