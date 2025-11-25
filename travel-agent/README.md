# LangGraph Travel Agent

A sophisticated multi-agent travel planning system built entirely with **LangGraph** - no Temporal dependencies required! This system uses multiple specialized AI agents working together to provide comprehensive travel planning services.

## 🚀 Features

### Multi-Agent Architecture
- **✈️ Flight Search Agent**: Specialized in finding optimal flights
- **🏨 Accommodation Agent**: Expert in hotel recommendations and booking
- **📋 Itinerary Agent**: Creates comprehensive travel itineraries  
- **🧠 Supervisor Agent**: Coordinates all agents and manages workflow

### Advanced Capabilities
- **🔄 Parallel Processing**: Flight and accommodation searches run simultaneously
- **💾 State Persistence**: Built-in checkpointing for conversation memory
- **👤 Human-in-the-Loop**: Interactive feedback and approval workflows
- **🌊 Real-time Streaming**: Live updates during workflow execution
- **🛡️ Error Handling**: Graceful degradation with fallback responses
- **🎯 Smart Routing**: Dynamic workflow paths based on agent results

## 🏗️ Architecture

```
┌─────────────────┐
│   Gradio UI     │ ← Web Interface
└─────────┬───────┘
          │
┌─────────▼───────┐
│ Travel Agent    │ ← Main Coordinator
│ (LangGraph)     │
└─────────┬───────┘
          │
    ┌─────┴─────┐
    │           │
┌───▼──┐    ┌───▼──────┐    ┌─────▼─────┐
│Flight│    │Accommodation│   │ Itinerary │
│Agent │    │   Agent     │   │   Agent   │
└──────┘    └─────────────┘   └───────────┘
```

## 📦 Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd travel-agent
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

4. **Set up PostgreSQL (Optional but Recommended):**

For enhanced durability and production use:

```bash
# Recommended: Docker Compose (simplest setup)
docker-compose -f docker-compose.local.yml up -d

# Alternative: Single Docker command
docker run --name langgraph-postgres \
  -e POSTGRES_DB=langgraph_checkpoints \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 -d postgres:15
```

The application will automatically detect PostgreSQL and use it for state persistence.

## 🎮 Usage

### Web Interface (Recommended)
```bash
# Start the web UI
python main.py web

# With custom port
python main.py web --port 8080

# With public sharing link
python main.py web --share
```

Then open your browser to `http://localhost:7860`

### Quick Single Request
```bash
python main.py single --destination "Tokyo, Japan" --start-date "2025-06-01" --end-date "2025-06-07" --travelers 2
```
   Dates: 2025-06-01 to 2025-06-07
   Please wait...

✅ Travel Plan Created Successfully!
```

### Single Request Mode
```bash
python main.py single --destination "Paris, France" --start-date "2025-06-01" --end-date "2025-06-07" --travelers 2
```

### Performance Benchmarking
```bash
python main.py benchmark
```

## 🔧 Configuration

### Database Options

**Memory (Default)** - For development:
```python
agent = LangGraphTravelAgent(use_postgres=False)
```

**PostgreSQL** - For production:
```python
agent = LangGraphTravelAgent(
    use_postgres=True,
    connection_string="postgresql://user:pass@localhost/langgraph"
)
```

### Environment Variables
- `OPENAI_API_KEY`: Required for LLM functionality
- `ECHO_SERVER_URL`: Optional mock hotel booking service URL

## 🧪 Examples

### Basic Travel Planning
```python
from src.agents.travel_agent import LangGraphTravelAgent
from src.models.travel_models import TravelRequest

# Initialize agent
agent = LangGraphTravelAgent()

# Create request
request = TravelRequest(
    destination="Tokyo, Japan",
    start_date="2025-06-01",
    end_date="2025-06-07",
    number_of_travelers=2
)

# Run planning
result = await agent.run(request)
print(result)
```

### Streaming Execution
```python
# Stream real-time updates
async for update in agent.stream(request):
    print(f"Update: {update}")
```

### State Management
```python
# Get current state
state = agent.get_state(thread_id="my-trip")

# Resume from human feedback
await agent.resume_from_feedback(thread_id="my-trip", user_input="approved")
```

## 📊 Performance

### Typical Execution Times
- **Sequential**: ~90 seconds (Flight → Hotel → Itinerary)
- **Parallel**: ~60 seconds (Flight ∥ Hotel → Itinerary) 
- **33% faster** with parallel agent execution!

### Scalability
- **Concurrent Users**: Handles multiple users simultaneously
- **State Isolation**: Each conversation has independent state
- **Memory Efficient**: Lightweight compared to Temporal workflows

## 🔍 Architecture Benefits

### vs. Temporal-based Systems
| Feature | LangGraph Only | Temporal + LangGraph |
|---------|---------------|---------------------|
| **Setup Complexity** | ⭐⭐ Low | ⭐⭐⭐⭐⭐ High |
| **AI Capabilities** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Excellent |
| **Development Speed** | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐ Medium |
| **Operational Overhead** | ⭐⭐⭐⭐⭐ Low | ⭐⭐ High |
| **AI-Native Features** | ⭐⭐⭐⭐⭐ Built-in | ⭐⭐⭐ Limited |

### Why LangGraph Only?
- ✅ **AI-Native**: Built specifically for agent workflows
- ✅ **Simpler**: One technology stack to manage
- ✅ **Faster Development**: Less boilerplate code
- ✅ **Better State Management**: Rich context for AI agents
- ✅ **Human-in-Loop**: Built-in interactive capabilities
- ✅ **Streaming**: Real-time agent responses
- ✅ **Lower Costs**: No enterprise orchestration overhead

## 🧪 Testing

### Run All Tests
```bash
python -m pytest tests/
```

### Manual Testing
```bash
# Test individual agents
python -c "
from src.agents.flight_search_agent import LangGraphFlightSearchAgent
from src.models.travel_models import TravelRequest
import asyncio

agent = LangGraphFlightSearchAgent()
request = TravelRequest('Tokyo', '2025-06-01', '2025-06-07', 2)
result = asyncio.run(agent.run(request))
print(result)
"
```

## 🛠️ Development

### Project Structure
```
travel-agent/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── src/
│   ├── agents/               # Pure LangGraph agents
│   │   ├── travel_agent.py   # Main coordinator
│   │   ├── flight_search_agent.py
│   │   ├── accommodation_agent.py
│   │   └── itinerary_agent.py
│   ├── models/
│   │   └── travel_models.py  # Data models
│   ├── ui/
│   │   └── gradio_ui.py      # Web interface
│   └── workflow/
│       ├── constants.py      # Shared config
│       └── README.md         # Architecture docs
└── tests/                    # Test suites
```

### Adding New Agents
1. Create agent class inheriting from base patterns
2. Implement LangGraph workflow with StateGraph
3. Add to workflow registry
4. Update coordinator routing logic

### Extending Functionality
- **New Travel Services**: Add car rental, activities, etc.
- **Enhanced LLM Integration**: Add function calling, tools
- **External APIs**: Integrate real booking services
- **Advanced Routing**: Add conditional logic based on user preferences

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♀️ Support

- **Documentation**: Check the `/src/workflow/README.md` for architecture details
- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

## 🎉 Migration from Temporal

If you're migrating from a Temporal-based system:

1. **Remove Temporal dependencies**: Update `requirements.txt`
2. **Replace workflow decorators**: Convert `@workflow.defn` to LangGraph StateGraph
3. **Update activity calls**: Replace `workflow.execute_activity()` with direct async calls
4. **Simplify state management**: Use LangGraph's built-in state classes
5. **Update UI integration**: Remove Temporal client initialization

See `ARCHITECTURE_COMPARISON.md` for detailed migration guidance.

---

**Built with ❤️ using LangGraph** - The future of AI agent orchestration!
