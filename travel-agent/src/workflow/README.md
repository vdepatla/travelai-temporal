# LangGraph Workflows Architecture

This directory contains LangGraph-based workflows that are orchestrated by Temporal. Each workflow represents a distinct travel-related agent that can operate independently while being coordinated by the Temporal workflow engine.

## Architecture Overview

```
Temporal Orchestration Layer
    ↓
LangGraph Agent Workflows
    ↓
External Services (APIs, Databases, etc.)
```

## Workflow Structure

Each workflow follows a consistent pattern:

1. **State Management**: Each workflow has its own state class that tracks data throughout the workflow execution
2. **Graph Definition**: Workflows use LangGraph's StateGraph to define nodes and edges
3. **Node Implementation**: Each step in the workflow is implemented as an async method
4. **Error Handling**: Comprehensive error handling with fallback scenarios
5. **Configuration**: Shared constants and configurations

## Available Workflows

### 1. SearchFlightsAgentWorkflow
- **Purpose**: Find optimal flights for travel requests
- **Nodes**: 
  - `prepare_request`: Sets up LLM messages
  - `call_llm`: Invokes the language model
  - `process_response`: Extracts function arguments
  - `create_flight_details`: Generates flight information
- **Output**: `FlightDetails` object

### 2. BookAccommodationAgentWorkflow
- **Purpose**: Book accommodation for travelers
- **Nodes**:
  - `prepare_request`: Sets up LLM messages
  - `call_llm`: Invokes the language model
  - `process_response`: Extracts function arguments
  - `prepare_booking`: Creates booking payload
  - `make_booking`: Calls external booking service
  - `create_accommodation_details`: Generates accommodation information
- **Output**: `AccommodationDetails` object

### 3. CreateItineraryAgentWorkflow
- **Purpose**: Generate comprehensive travel itineraries
- **Nodes**:
  - `prepare_request`: Sets up LLM messages with flight and hotel info
  - `call_llm`: Invokes the language model
  - `process_response`: Extracts the generated itinerary
  - `finalize_itinerary`: Handles fallback scenarios
- **Output**: Formatted itinerary string

## Key Features

### State Management
Each workflow has a dedicated state class that maintains:
- Input parameters
- Intermediate results
- Error information
- LLM responses
- Final outputs

### Error Handling
- Graceful degradation with fallback values
- Comprehensive error capture and logging
- Default responses when external services fail

### Configuration Management
- Centralized constants in `constants.py`
- Environment-specific configurations
- Default values for consistent behavior

### Temporal Integration
- Workflows are called as Temporal activities
- Each workflow can be independently scaled
- Failed workflows can be retried with Temporal's built-in retry mechanisms

## Usage Example

```python
from src.workflow.search_flights_workflow import SearchFlightsAgentWorkflow
from src.models.travel_models import TravelRequest

# Create workflow instance
workflow = SearchFlightsAgentWorkflow()

# Create travel request
request = TravelRequest(
    destination="Paris",
    start_date="2025-06-01",
    end_date="2025-06-07",
    number_of_travelers=2
)

# Run workflow
flight_details = await workflow.run(request)
```

## Extension Points

To add a new workflow:

1. Create a new workflow file in this directory
2. Implement the workflow class with required methods
3. Add to the workflow registry
4. Create corresponding Temporal activity
5. Update documentation

## Dependencies

- **LangGraph**: For workflow orchestration
- **OpenAI**: For LLM integration
- **Temporal**: For overall orchestration
- **Requests**: For external API calls
