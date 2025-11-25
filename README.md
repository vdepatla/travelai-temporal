# travelai-langgraph

A sophisticated multi-agent travel planning system built entirely with **LangGraph**. This project demonstrates how to create resilient, scalable AI agent systems using LangGraph's state management, checkpointing, and multi-agent coordination capabilities.

## 🌟 Overview

This repository contains a complete travel planning system that showcases:

- **Pure LangGraph Architecture**: No external orchestration frameworks needed
- **Multi-Agent Coordination**: Specialized agents for flights, accommodations, and itinerary planning
- **Agent Durability**: State persistence, crash recovery, and resumable workflows
- **Production Ready**: PostgreSQL checkpointing, concurrent user support, error handling
- **Modern UI**: Web interface built with Gradio

## 🏗️ Architecture

### Multi-Agent System
- **Flight Search Agent**: Finds and compares flight options
- **Accommodation Agent**: Searches and books hotels
- **Itinerary Agent**: Creates detailed travel itineraries
- **Travel Coordinator**: Orchestrates all agents and manages workflow

### Key Features
- **State Persistence**: Workflows survive application restarts
- **Checkpointing**: Resume from any point in the workflow
- **Human-in-the-Loop**: Pause for user approval and feedback
- **Concurrent Sessions**: Multiple users with isolated state
- **Error Recovery**: Graceful handling of failures and retries

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

### Running the Application

```bash
# Web UI (recommended for interactive use)
python main.py --mode web

# CLI mode
python main.py --mode cli

# Single request mode
python main.py --mode single --destination "Tokyo, Japan" --start-date "2025-06-01" --end-date "2025-06-07" --travelers 2

# Benchmarking mode
python main.py --mode benchmark
```

## 🧪 Local Testing with Gradio UI

### Quick Start - Interactive Testing

1. **One-command setup:**
   ```bash
   cd travel-agent
   python test_locally.py
   ```
   This interactive script will guide you through:
   - Starting PostgreSQL (optional but recommended)
   - Running basic tests
   - Launching the enhanced web interface

2. **Direct web interface:**
   ```bash
   cd travel-agent
   
   # If you haven't installed dependencies yet:
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Start the application
   python main.py --mode web
   ```
   Open: `http://localhost:7860`

### With PostgreSQL (Recommended)

For testing state persistence and durability:

```bash
# Terminal 1: Start PostgreSQL
cd travel-agent
docker-compose -f docker-compose.local.yml up -d

# Terminal 2: Start the application
python main.py --mode web

# The UI will show: "✅ Using PostgreSQL for state persistence"
```

### Testing Features

The enhanced UI provides:

- **🎯 Structured Testing Form**: Easy input fields for destination, dates, travelers
- **🧪 Quick Test Examples**: One-click buttons for Paris, Tokyo, Rome, and error scenarios  
- **📊 Real-time System Status**: Shows PostgreSQL vs Memory checkpointing
- **🔧 System Information**: Detailed configuration and troubleshooting tips
- **⚙️ Testing Tools**: Links to automated tests and debugging guide

### Test Scenarios

1. **Basic Travel Planning:**
   - Click "🗼 Paris Weekend" → "✈️ Plan My Trip"
   - Watch real-time agent coordination
   - Verify all agents complete successfully

2. **State Persistence** (with PostgreSQL):
   - Start a trip planning request
   - Note the Thread ID in results
   - Refresh the browser page
   - The session state should be preserved

3. **Error Handling:**
   - Click "❌ Error Test" → "✈️ Plan My Trip"  
   - Verify graceful error handling
   - Check system continues to work

4. **Concurrent Sessions:**
   - Open multiple browser tabs
   - Use different destinations/Thread IDs
   - Verify sessions are isolated

### Automated Testing

```bash
# Test basic functionality
python test_langgraph_agent.py

# Test agent durability and persistence
python test_agent_durability.py
```

### Testing Features

- **🌍 Travel Planning**: Enter any destination and travel dates
- **🔄 Real-time Updates**: Watch agents coordinate in real-time
- **💾 State Persistence**: Refresh page and see preserved state (with PostgreSQL)
- **📊 Agent Logs**: View detailed conversation between agents
- **🛡️ Error Recovery**: Test with invalid inputs to see error handling

## 🧪 Testing

```bash
# Test basic functionality
python test_langgraph_agent.py

# Test agent durability and persistence
python test_agent_durability.py
```

### Local UI Testing Scenarios

Test these scenarios in the Gradio interface:

1. **Basic Travel Planning:**
   ```
   Destination: Paris, France
   Start Date: 2025-06-01
   End Date: 2025-06-07
   Travelers: 2
   ```

2. **Complex Multi-City Trip:**
   ```
   Destination: Tokyo, Japan → Kyoto → Osaka
   Start Date: 2025-08-15
   End Date: 2025-08-25
   Travelers: 3
   ```

3. **Test Error Recovery:**
   ```
   Destination: Invalid123!@#
   Start Date: 2025-13-45 (invalid date)
   Travelers: 0 (invalid number)
   ```

4. **State Persistence Test** (with PostgreSQL):
   - Start a trip planning request
   - Refresh the browser page
   - Check if the agent state is preserved

## 📚 Documentation

- **[Agent Architecture](travel-agent/README.md)**: Detailed system documentation
- **[Agent Durability](travel-agent/AGENT_DURABILITY.md)**: State persistence and crash recovery
- **[Architecture Comparison](travel-agent/ARCHITECTURE_COMPARISON.md)**: LangGraph vs other orchestration frameworks

## 🔧 Configuration

### Development (Memory Checkpointing)
```python
agent = LangGraphTravelAgent(use_postgres=False)
```

### Production (PostgreSQL Checkpointing)
```python
agent = LangGraphTravelAgent(
    use_postgres=True,
    connection_string="postgresql://user:password@localhost/langgraph_checkpoints"
)
```

## 🌐 Web Interface

The application includes a modern web interface built with Gradio:

- Interactive travel planning form
- Real-time progress tracking
- Agent conversation logs
- Result visualization

Access at: http://localhost:7860

## 🏭 Production Deployment

For production deployments with PostgreSQL:

1. Set up PostgreSQL database
2. Configure connection string
3. Enable PostgreSQL checkpointing
4. Set up monitoring and logging

See [Agent Durability](travel-agent/AGENT_DURABILITY.md) for detailed production setup instructions.

## 🐛 Troubleshooting

### Common Installation Issues

#### "ModuleNotFoundError: No module named 'pydantic'"
```bash
# Solution: Install dependencies in a virtual environment
cd travel-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### "externally-managed-environment" Error
```bash
# Solution 1: Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Solution 2: Use our setup script
./setup.sh

# Solution 3: Install with --user flag
pip install --user -r requirements.txt
```

#### "zsh: command not found: pip"
```bash
# Use python module syntax instead
python3 -m pip install -r requirements.txt
```

#### Virtual Environment Issues
```bash
# Remove and recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Runtime Issues

#### PostgreSQL Connection Failed
```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.local.yml ps

# Start PostgreSQL
docker-compose -f docker-compose.local.yml up -d

# Check logs
docker-compose -f docker-compose.local.yml logs
```

#### OpenAI API Errors
```bash
# Set API key
export OPENAI_API_KEY="your-actual-key-here"

# Verify it's set
echo $OPENAI_API_KEY
```

#### Port Already in Use
```bash
# Use different port
python main.py --mode web --port 8080

# Or find what's using port 7860
lsof -i :7860
```

### Getting Help

1. **Check the logs**: Look at terminal output for detailed error messages
2. **Run tests**: Use `python test_locally.py` for guided troubleshooting
3. **Check system status**: Use the "System Info" tab in the web interface
4. **Verify setup**: Run `./setup.sh` to ensure proper installation

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any improvements.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **LangGraph**: For providing excellent agent orchestration capabilities
- **OpenAI**: For the language models powering the agents
- **Gradio**: For the intuitive web interface framework