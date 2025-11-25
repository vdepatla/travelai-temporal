# TravelAI Chatbot - LangGraph

An intelligent AI travel assistant chatbot built entirely with **LangGraph**. This conversational AI system demonstrates how to create sophisticated multi-agent chatbots with memory, context awareness, and seamless user interactions using LangGraph's state management and coordination capabilities.

## 🌟 Overview

This repository contains a complete AI travel chatbot that showcases:

- **Conversational AI Interface**: Natural language travel planning through chat
- **Multi-Agent Architecture**: Specialized AI agents working together behind the scenes
- **Persistent Memory**: Remembers your preferences and conversation history
- **Real-time Responses**: Streaming responses as the chatbot thinks and plans
- **Context Awareness**: Understands complex travel requests and user intent
- **Interactive Planning**: Ask questions, get suggestions, and refine your trip
- **Modern Chat UI**: Beautiful web interface for seamless conversations

## 🏗️ Architecture

### Multi-Agent Chatbot System
- **Flight Search Agent**: Finds and compares flight options through conversation
- **Accommodation Agent**: Searches and books hotels based on your preferences  
- **Itinerary Agent**: Creates detailed travel itineraries from your chat input
- **Conversation Coordinator**: Manages the chat flow and agent collaboration

### Key Chatbot Features
- **Memory Persistence**: Remembers your conversation across sessions
- **Context Understanding**: Follows complex, multi-turn conversations
- **Smart Interruptions**: Pause to ask clarifying questions
- **Multiple Users**: Concurrent conversations with isolated memory
- **Graceful Recovery**: Handles errors without losing conversation context
- **Streaming Responses**: Real-time typing as the AI thinks

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL (optional, for production durability)
- OpenAI API key

### Installation

**Quick Setup (Recommended):**
```bash
# Clone the repository
git clone https://github.com/your-username/travelai-langgraph.git
cd travelai-langgraph/travel-agent

# Run automated setup script
./setup.sh

# Activate the virtual environment
source venv/bin/activate

# Set your OpenAI API key
export OPENAI_API_KEY="your-openai-api-key"
```

**Manual Setup:**
```bash
# Clone the repository
git clone https://github.com/your-username/travelai-langgraph.git
cd travelai-langgraph

# Navigate to travel-agent directory
cd travel-agent

# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL (optional but recommended)
docker-compose -f docker-compose.local.yml up -d

# Set up environment variables
export OPENAI_API_KEY="your-openai-api-key"
```

### Alternative Installation Methods

If you encounter issues with the virtual environment:

**Option 1: Using pipx (recommended for macOS with Homebrew)**
```bash
brew install pipx
pipx install --include-deps -r requirements.txt
```

**Option 2: System-wide installation (not recommended)**
```bash
pip3 install --user -r requirements.txt
# or if needed:
pip3 install --break-system-packages -r requirements.txt
```

**Option 3: Using conda**
```bash
conda create -n travelai python=3.9
conda activate travelai
pip install -r requirements.txt
```

### Running the Chatbot

```bash
# Start the interactive chatbot (recommended)
python main.py web

# Quick single conversation
python main.py single --destination "Tokyo, Japan" --start-date "2025-06-01" --end-date "2025-06-07" --travelers 2

# Performance testing
python main.py benchmark
```

## 💬 Chat with Your Travel AI

### Quick Start - Start Chatting

1. **One-command setup:**
   ```bash
   cd travel-agent
   python test_locally.py
   ```
   This interactive script will guide you through:
   - Starting PostgreSQL (optional but recommended)
   - Running basic tests
   - Launching the enhanced chat interface

2. **Direct chat interface:**
   ```bash
   cd travel-agent
   
   # If you haven't installed dependencies yet:
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Start chatting with the AI
   python main.py web
   ```
   Open: `http://localhost:7860`

### With Persistent Memory (Recommended)

For conversations that remember across sessions:

```bash
# Terminal 1: Start PostgreSQL for memory persistence
cd travel-agent
docker-compose -f docker-compose.local.yml up -d

# Terminal 2: Start the chatbot
python main.py web

# The UI will show: "✅ Using PostgreSQL for conversation memory"
```

### Chat Testing Features

The enhanced chat interface provides:

- **💬 Natural Conversation**: Chat in plain English about your travel plans
- **� Memory Persistence**: The AI remembers your preferences and past conversations
- **⚡ Real-time Responses**: Watch the AI think and respond in real-time
- **🎯 Smart Suggestions**: Get personalized recommendations based on your style
- **🔄 Interactive Planning**: Ask follow-up questions and refine your plans
- **📱 Modern Chat UI**: Beautiful, responsive interface for seamless conversations

### Conversation Examples

Try these natural language queries with your AI travel assistant:

1. **Simple Trip Planning:**
   - "I want to plan a weekend trip to Paris"
   - "Find me flights to Tokyo for next month"
   - "What's the best time to visit Italy?"

2. **Complex Multi-turn Conversations:**
   - "Plan a 2-week honeymoon in Europe"
   - "Actually, let's focus on romantic destinations"
   - "What about adding a few days in Switzerland?"

3. **Follow-up Questions:**
   - "Show me cheaper flight options"
   - "What about hotels near the city center?"
   - "Can you add some restaurant recommendations?"

4. **Memory Testing** (with PostgreSQL):
   - Start a conversation about a trip
   - Refresh the page
   - Continue the conversation - the AI remembers!

### Automated Testing

```bash
# Test basic chatbot functionality
python test_langgraph_agent.py

# Test conversation memory and persistence
python test_agent_durability.py
```

### Chat Features

- **🌍 Travel Planning**: Chat naturally about any travel destination
- **🔄 Real-time Responses**: Watch the AI think and respond live
- **💾 Conversation Memory**: Your chat history persists across sessions (with PostgreSQL)
- **📊 Agent Coordination**: See how multiple AI agents work together behind the scenes
- **🛡️ Smart Error Handling**: The chatbot gracefully handles misunderstandings

## 🧪 Testing Your Chatbot

```bash
# Test basic conversation functionality
python test_langgraph_agent.py

# Test memory persistence and conversation continuity
python test_agent_durability.py
```

## 📚 Documentation

- **[Chatbot Architecture](travel-agent/README.md)**: Detailed system documentation
- **[Conversation Memory](travel-agent/AGENT_DURABILITY.md)**: How the chatbot remembers conversations
- **[Architecture Comparison](travel-agent/ARCHITECTURE_COMPARISON.md)**: LangGraph vs other chatbot frameworks

## 🔧 Configuration

### Development (In-Memory Conversations)
```python
chatbot = LangGraphTravelAgent(use_postgres=False)
```

### Production (Persistent Conversation Memory)
```python
chatbot = LangGraphTravelAgent(
    use_postgres=True,
    connection_string="postgresql://user:password@localhost/langgraph_checkpoints"
)
```

## 🌐 Chat Interface

The chatbot includes a modern web interface built with Gradio:

- Interactive chat interface
- Real-time response streaming
- Conversation history
- Agent coordination visualization

Access at: http://localhost:7860

## 🏭 Production Deployment

For production chatbot deployments with PostgreSQL:
