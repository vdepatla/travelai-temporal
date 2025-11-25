# PostgreSQL Checkpointing for Local Development

## Why Use PostgreSQL Locally?

While memory checkpointing is fine for testing, using PostgreSQL locally provides several benefits:

### 🔄 **Development-Production Parity**
- Same durability behavior as production
- Test state persistence scenarios locally
- Catch persistence-related bugs early

### 🛡️ **Crash Recovery Testing** 
- Test agent recovery after application crashes
- Verify state consistency across restarts
- Debug complex multi-step workflows

### 👥 **Multi-Session Testing**
- Test concurrent user sessions
- Verify thread isolation
- Simulate production load patterns

### 🔍 **Advanced Debugging**
- Inspect state history and checkpoints
- Query agent state with SQL
- Analyze workflow patterns

## Quick Setup Options

### Option 1: Docker Compose (Recommended)
```bash
# One command setup - creates and starts PostgreSQL
docker-compose -f docker-compose.local.yml up -d

# Check status
docker-compose -f docker-compose.local.yml ps

# Stop when done
docker-compose -f docker-compose.local.yml down
```

### Option 2: Single Docker Command
```bash
docker run --name langgraph-postgres \
  -e POSTGRES_DB=langgraph_checkpoints \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 -d postgres:15
```

### Option 3: Homebrew (macOS)
```bash
brew install postgresql@15
brew services start postgresql@15
createdb langgraph_checkpoints
```

## Usage in Code

The application automatically detects PostgreSQL:

```python
# Automatic fallback
agent = await create_agent_with_fallback()

# Explicit PostgreSQL
agent = LangGraphTravelAgent(
    use_postgres=True,
    connection_string="postgresql://postgres:password@localhost:5432/langgraph_checkpoints"
)

# Check what's being used
info = await agent.get_checkpointer_info()
print(f"Using: {info['type']}")  # "PostgreSQL" or "Memory"
```

## Testing Durability

Run the comprehensive durability tests:

```bash
python test_agent_durability.py
```

This will test:
- Memory checkpointing
- PostgreSQL checkpointing (if available)
- State inspection and history
- Error recovery
- Human-in-the-loop scenarios
- Concurrent sessions

## Production Benefits

When you deploy to production with PostgreSQL:
- ✅ State survives application restarts
- ✅ Scale across multiple instances
- ✅ Handle thousands of concurrent users
- ✅ Full audit trail and debugging
- ✅ Backup and restore capabilities

## Performance Comparison

| Feature | Memory | PostgreSQL |
|---------|--------|------------|
| Latency | ~1-2ms | ~5-10ms |
| Persistence | ❌ | ✅ |
| Scalability | Single instance | Multi-instance |
| Debugging | Limited | Full SQL access |
| Production Ready | ❌ | ✅ |

## Summary

Using PostgreSQL locally gives you:
1. **Realistic testing** of production scenarios
2. **Better debugging** with SQL access to state
3. **Crash recovery** testing capabilities  
4. **Multi-user** session isolation testing
5. **Seamless transition** to production

The setup is quick and the benefits are significant for any serious development work!
