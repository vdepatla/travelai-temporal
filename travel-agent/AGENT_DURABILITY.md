# Agent Durability in LangGraph

This document explains agent durability features in our LangGraph travel agent system, including state persistence, crash recovery, and production deployment strategies.

## Overview

Agent durability refers to the ability of our travel agents to:
- **Persist state** across application restarts
- **Recover from crashes** without losing progress
- **Resume workflows** from any checkpoint
- **Handle interruptions** gracefully
- **Support concurrent users** with isolated state

## Durability Architecture

### Checkpointing System

LangGraph provides automatic checkpointing that saves agent state after each step:

```python
from langgraph.checkpoint.memory import MemoryCheckpointSaver
from langgraph.checkpoint.postgres import PostgresCheckpointSaver

# Development: In-memory checkpointing
agent = LangGraphTravelAgent(use_postgres=False)

# Production: PostgreSQL checkpointing
agent = LangGraphTravelAgent(
    use_postgres=True,
    connection_string="postgresql://user:password@host:port/db"
)
```

### State Isolation

Each conversation thread maintains independent state:

```python
# Different users, different threads, isolated state
user_1_config = {"configurable": {"thread_id": "user-1-session"}}
user_2_config = {"configurable": {"thread_id": "user-2-session"}}

# These run independently without interference
result_1 = await agent.run(request_1, thread_id="user-1-session")
result_2 = await agent.run(request_2, thread_id="user-2-session")
```

## Memory vs PostgreSQL Checkpointing

### Memory Checkpointer

**Best for:** Development, testing, single-instance deployments

**Characteristics:**
- ✅ Fast performance
- ✅ No external dependencies
- ✅ Easy setup
- ❌ State lost on restart
- ❌ Not scalable
- ❌ Single-instance only

```python
from langgraph.checkpoint.memory import MemoryCheckpointSaver

checkpointer = MemoryCheckpointSaver()
workflow = workflow.compile(checkpointer=checkpointer)
```

### PostgreSQL Checkpointer

**Best for:** Production, multi-instance, high-availability deployments

**Characteristics:**
- ✅ Persistent across restarts
- ✅ Scalable to multiple instances
- ✅ Concurrent access safe
- ✅ Full audit trail
- ✅ Production ready
- ❌ Requires PostgreSQL setup
- ❌ Slightly slower than memory

```python
from langgraph.checkpoint.postgres import PostgresCheckpointSaver

checkpointer = PostgresCheckpointSaver.from_conn_string(
    "postgresql://user:password@localhost/langgraph_checkpoints"
)
workflow = workflow.compile(checkpointer=checkpointer)
```

## Production Setup

### 1. PostgreSQL Database Setup

```sql
-- Create database
CREATE DATABASE langgraph_checkpoints;
CREATE USER travel_agent WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE langgraph_checkpoints TO travel_agent;

-- Tables are created automatically by LangGraph
-- - checkpoints: Main checkpoint data
-- - checkpoint_blobs: Large binary data
-- - checkpoint_writes: Write operations log
```

### 2. Docker Compose Configuration

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: langgraph_checkpoints
      POSTGRES_USER: travel_agent
      POSTGRES_PASSWORD: secure_password
      POSTGRES_INITDB_ARGS: "--encoding=UTF8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
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
      POSTGRES_CONNECTION_STRING: postgresql://travel_agent:secure_password@postgres:5432/langgraph_checkpoints
      PYTHONPATH: /app/src
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "7860:7860"  # Gradio UI
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
```

### 3. Environment Configuration

```python
import os

# Production agent setup
connection_string = os.getenv(
    "POSTGRES_CONNECTION_STRING",
    "postgresql://travel_agent:secure_password@localhost:5432/langgraph_checkpoints"
)

agent = LangGraphTravelAgent(
    use_postgres=True,
    connection_string=connection_string
)
```

## Durability Features

### 1. Automatic State Persistence

Every workflow step is automatically checkpointed:

```python
async def travel_workflow():
    # State saved after each of these steps
    flight_result = await search_flights()      # Checkpoint 1
    hotel_result = await search_hotels()        # Checkpoint 2  
    itinerary = await create_itinerary()        # Checkpoint 3
    return final_result                         # Checkpoint 4
```

### 2. Crash Recovery

Application crashes are handled gracefully:

```python
# Before crash
config = {"configurable": {"thread_id": "user-123"}}
await workflow.ainvoke(travel_request, config=config)
# ... application crashes ...

# After restart
agent = LangGraphTravelAgent(use_postgres=True)
config = {"configurable": {"thread_id": "user-123"}}

# Resume from last checkpoint
async for result in agent.workflow.astream(None, config=config):
    print(f"Resumed: {result}")
```

### 3. State Inspection

View current and historical states:

```python
# Get current state
state = agent.get_state("user-123")
print(f"Current step: {state.next}")
print(f"Completed tasks: {state.values.completed_tasks}")

# Get state history
history = await agent.get_state_history("user-123", limit=10)
for i, checkpoint in enumerate(history):
    print(f"Checkpoint {i}: {checkpoint['created_at']}")
```

### 4. Human-in-the-Loop Persistence

Workflows pause and persist while waiting for human input:

```python
# Workflow pauses at this point
workflow.add_node("human_approval", human_approval_step)
workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_approval"]  # Pause here
)

# User can come back hours later
await agent.resume_from_feedback("user-123", "Approved!")
```

### 5. Error Recovery

Errors are captured and can be corrected:

```python
# Get state with errors
state = agent.get_state("user-123")
if state.values.errors:
    print(f"Errors: {state.values.errors}")
    
    # Fix the issue and continue
    agent.update_state("user-123", {
        "request": corrected_request,
        "errors": {}
    })
    
    # Resume workflow
    result = await agent.workflow.ainvoke(None, config=config)
```

## Testing Durability

Use our comprehensive test suite:

```bash
# Run all durability tests
python test_agent_durability.py

# Tests include:
# - Memory checkpointing
# - State inspection
# - Error recovery
# - Human-in-the-loop
# - Concurrent sessions
```

## Performance Considerations

### Memory Checkpointer Performance
- **Latency:** ~1-2ms per checkpoint
- **Memory usage:** Grows with conversation length
- **Suitable for:** Development, demo, single-user

### PostgreSQL Checkpointer Performance
- **Latency:** ~5-10ms per checkpoint
- **Storage:** Scales with database
- **Suitable for:** Production, multi-user, high-availability

### Optimization Tips

1. **Batch operations** where possible
2. **Clean old checkpoints** regularly in production
3. **Use connection pooling** for PostgreSQL
4. **Monitor database performance**
5. **Set appropriate checkpoint limits**

```python
# Connection pooling example
from sqlalchemy.pool import QueuePool

checkpointer = PostgresCheckpointSaver.from_conn_string(
    connection_string,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30
)
```

## Monitoring and Maintenance

### Health Checks

```python
async def health_check():
    """Check agent durability health"""
    try:
        # Test checkpointer
        info = await agent.get_checkpointer_info()
        
        # Test state operations
        test_thread = f"health-check-{time.time()}"
        agent.update_state(test_thread, {"test": True})
        state = agent.get_state(test_thread)
        
        return {
            "status": "healthy",
            "checkpointer": info,
            "state_operations": "working"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e)
        }
```

### Cleanup Old Data

```sql
-- Clean up old checkpoints (PostgreSQL)
DELETE FROM checkpoints 
WHERE created_at < NOW() - INTERVAL '30 days';

DELETE FROM checkpoint_blobs 
WHERE created_at < NOW() - INTERVAL '30 days';

DELETE FROM checkpoint_writes 
WHERE created_at < NOW() - INTERVAL '30 days';
```

### Monitoring Metrics

```python
# Example monitoring
metrics = {
    "active_threads": await agent.list_active_threads(),
    "checkpointer_type": agent.checkpointer.__class__.__name__,
    "database_size": "SELECT pg_size_pretty(pg_database_size('langgraph_checkpoints'))",
    "checkpoint_count": "SELECT COUNT(*) FROM checkpoints",
    "avg_state_size": "SELECT AVG(octet_length(checkpoint::text)) FROM checkpoints"
}
```

## Best Practices

### 1. Thread ID Strategy
```python
# Good: Include user and session info
thread_id = f"user-{user_id}-session-{session_id}"

# Good: Include timestamp for debugging
thread_id = f"user-{user_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

# Avoid: Generic or predictable IDs
thread_id = "thread1"  # Bad
```

### 2. State Management
```python
# Keep state lean - don't store large objects
state = TravelPlanningState(
    request=request,
    flight_details=summary_only,  # Not full flight data
    completed_tasks=["flight_search"],
    next_action="book_flight"
)

# Store large data externally if needed
state.flight_data_url = "s3://bucket/flight-data-user123.json"
```

### 3. Error Handling
```python
try:
    result = await agent.run(request, thread_id=thread_id)
except Exception as e:
    # Log error with thread context
    logger.error(f"Agent error for thread {thread_id}: {str(e)}")
    
    # Get state for debugging
    state = agent.get_state(thread_id)
    logger.info(f"State at error: {state.values}")
    
    # Potentially allow recovery
    return {"error": str(e), "recoverable": True, "thread_id": thread_id}
```

### 4. Testing
```python
# Always test durability in your application
async def test_durability():
    agent = LangGraphTravelAgent(use_postgres=True)
    
    # Start workflow
    thread_id = "durability-test"
    await agent.run(request, thread_id=thread_id)
    
    # Simulate restart
    del agent
    agent = LangGraphTravelAgent(use_postgres=True)
    
    # Verify state persisted
    state = agent.get_state(thread_id)
    assert state.values.completed_tasks  # Should have previous progress
```

## Troubleshooting

### Common Issues

1. **Connection errors**: Check PostgreSQL connection string and credentials
2. **State conflicts**: Ensure unique thread IDs across users
3. **Memory leaks**: Clean up old threads in development
4. **Performance**: Monitor database size and query performance

### Debug Commands

```python
# Check current state
state = agent.get_state(thread_id)
print(f"State: {state.values}")
print(f"Next: {state.next}")
print(f"Tasks: {state.tasks}")

# Check history
history = await agent.get_state_history(thread_id)
print(f"History length: {len(history)}")

# Test checkpointer
info = await agent.get_checkpointer_info()
print(f"Checkpointer: {info}")
```

This durability system ensures that your travel agents can handle real-world production scenarios with confidence, providing users with reliable and resilient travel planning experiences.
