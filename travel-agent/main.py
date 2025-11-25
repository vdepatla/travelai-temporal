"""
Main Entry Point for LangGraph Travel Agent

This is the primary entry point for running the travel agent chatbot.
It supports multiple modes of operation:
- Web UI (Gradio) - Interactive chat interface
- Single request mode - One-time travel planning
- Benchmark mode - Performance testing
"""

import asyncio
import argparse
import json
import os
from typing import Optional

from src.models.travel_models import TravelRequest
from src.agents.travel_agent import LangGraphTravelAgent


async def create_agent_with_fallback(prefer_postgres: bool = True) -> LangGraphTravelAgent:
    """
    Create a travel agent, trying PostgreSQL first, then falling back to memory
    """
    if prefer_postgres:
        # Try common local PostgreSQL configurations
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
                        return agent
                except Exception:
                    continue
        
        print("⚠️  PostgreSQL not available, using memory checkpointing")
        print("   💡 Run 'docker-compose -f docker-compose.local.yml up -d' to set up PostgreSQL")
    
    return LangGraphTravelAgent(use_postgres=False)



def run_web_ui(port: int = 7860, share: bool = False):
    """
    Launch the enhanced web UI using Gradio
    """
    try:
        # Try enhanced UI first, fallback to original
        try:
            from gradio_ui_enhanced import launch_enhanced_ui
            print(f"🌐 Starting enhanced testing interface on port {port}...")
            if share:
                print("🔗 Creating public sharing link...")
            launch_enhanced_ui(share=share, server_port=port)
        except ImportError:
            # Fallback to original UI
            from src.ui.gradio_ui import launch_ui
            print(f"🌐 Starting web interface on port {port}...")
            if share:
                print("🔗 Creating public sharing link...")
            launch_ui(share=share, server_port=port)
    except ImportError:
        print("❌ Gradio not installed. Install with: pip install gradio")
    except Exception as e:
        print(f"❌ Error starting web UI: {str(e)}")


async def run_single_request(destination: str, start_date: str, end_date: str, travelers: int):
    """
    Run a single travel planning request
    """
    agent = await create_agent_with_fallback()
    
    request = TravelRequest(
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        number_of_travelers=travelers
    )
    
    print(f"🔄 Planning trip to {destination}...")
    result = await agent.run(request)
    
    print(json.dumps(result, indent=2, default=str))


async def benchmark_performance():
    """
    Run performance benchmarks
    """
    import time
    
    print("🏃‍♂️ Running performance benchmarks...")
    
    agent = await create_agent_with_fallback()
    
    # Test requests
    test_requests = [
        TravelRequest("Tokyo, Japan", "2025-06-01", "2025-06-07", 2),
        TravelRequest("Paris, France", "2025-07-01", "2025-07-07", 1),
        TravelRequest("New York, USA", "2025-08-01", "2025-08-07", 3),
    ]
    
    results = []
    
    for i, request in enumerate(test_requests, 1):
        print(f"\nTest {i}: {request.destination}")
        start_time = time.time()
        
        result = await agent.run(request, thread_id=f"benchmark-{i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        results.append({
            "destination": request.destination,
            "duration": duration,
            "success": result["success"],
            "completed_tasks": len(result.get("completed_tasks", [])),
            "errors": len(result.get("errors", {}))
        })
        
        print(f"   Duration: {duration:.2f}s")
        print(f"   Success: {result['success']}")
    
    print("\n📊 Benchmark Results:")
    print("=" * 50)
    for result in results:
        print(f"{result['destination']}: {result['duration']:.2f}s ({'✅' if result['success'] else '❌'})")
    
    avg_duration = sum(r["duration"] for r in results) / len(results)
    success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
    
    print(f"\nAverage Duration: {avg_duration:.2f}s")
    print(f"Success Rate: {success_rate:.1f}%")


def main():
    """
    Main entry point with argument parsing
    """
    parser = argparse.ArgumentParser(description="LangGraph Travel Agent")
    parser.add_argument(
        "mode",
        choices=["web", "single", "benchmark"],
        help="Operation mode"
    )
    parser.add_argument("--port", type=int, default=7860, help="Port for web UI")
    parser.add_argument("--share", action="store_true", help="Create public sharing link")
    parser.add_argument("--destination", type=str, help="Destination for single request")
    parser.add_argument("--start-date", type=str, help="Start date for single request")
    parser.add_argument("--end-date", type=str, help="End date for single request")
    parser.add_argument("--travelers", type=int, default=1, help="Number of travelers")
    
    args = parser.parse_args()
    
    if args.mode == "web":
        run_web_ui(port=args.port, share=args.share)
    
    elif args.mode == "single":
        if not args.destination:
            print("❌ --destination is required for single mode")
            return
        
        destination = args.destination
        start_date = args.start_date or "2025-06-01"
        end_date = args.end_date or "2025-06-07"
        travelers = args.travelers
        
        asyncio.run(run_single_request(destination, start_date, end_date, travelers))
    
    elif args.mode == "benchmark":
        asyncio.run(benchmark_performance())


if __name__ == "__main__":
    main()
