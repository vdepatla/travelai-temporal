#!/usr/bin/env python3
"""
Local Testing Guide for LangGraph Travel Agent

This script demonstrates how to test the travel agent locally with the Gradio UI.
"""

import os
import subprocess
import sys
import time


def check_requirements():
    """Check if basic requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check if we can import required modules
    try:
        import pydantic
        import gradio
        import langgraph
        print("✅ Required Python packages installed")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Run: pip install -r requirements.txt")
        
        # Offer to install dependencies
        try:
            response = input("🤔 Would you like me to install dependencies? (y/n): ").lower()
            if response == 'y':
                install_dependencies()
                return check_requirements()  # Re-check after installation
        except KeyboardInterrupt:
            print("\n🛑 Cancelled")
        return False
    
    # Check OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not set - you'll need this for full functionality")
        print("💡 Set it with: export OPENAI_API_KEY='your-key-here'")
    else:
        print("✅ OpenAI API key configured")
    
    # Check Docker (optional)
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("✅ Docker available (for PostgreSQL)")
    except:
        print("⚠️  Docker not available (PostgreSQL won't work)")
    
    return True


def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Try different installation methods
        install_commands = [
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            [sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"],
            ["pip3", "install", "--user", "-r", "requirements.txt"],
            ["pip", "install", "-r", "requirements.txt"]
        ]
        
        for cmd in install_commands:
            try:
                print(f"⏳ Trying: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, cwd=".")
                print("✅ Dependencies installed successfully")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        print("❌ Failed to install dependencies automatically")
        print("💡 Please run manually:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate")
        print("   pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False


def start_postgresql():
    """Start PostgreSQL using Docker Compose"""
    print("\n🐘 Starting PostgreSQL for state persistence...")
    
    try:
        # Check if already running
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.local.yml", "ps", "-q"],
            capture_output=True, text=True, cwd="."
        )
        
        if result.stdout.strip():
            print("✅ PostgreSQL already running")
            return True
        
        # Start PostgreSQL
        subprocess.run(
            ["docker-compose", "-f", "docker-compose.local.yml", "up", "-d"],
            check=True, cwd="."
        )
        
        print("⏳ Waiting for PostgreSQL to be ready...")
        time.sleep(5)
        
        # Verify it's running
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.local.yml", "ps"],
            capture_output=True, text=True, cwd="."
        )
        
        if "langgraph-postgres" in result.stdout and "Up" in result.stdout:
            print("✅ PostgreSQL started successfully")
            return True
        else:
            print("❌ PostgreSQL failed to start")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start PostgreSQL: {e}")
        return False
    except FileNotFoundError:
        print("❌ docker-compose not found. Install Docker Compose first.")
        return False


def test_basic_functionality():
    """Test basic agent functionality"""
    print("\n🧪 Running basic functionality test...")
    
    try:
        result = subprocess.run(
            [sys.executable, "test_langgraph_agent.py"],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Basic functionality test passed")
            return True
        else:
            print("❌ Basic functionality test failed")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏱️ Test timed out - this might be normal for first run")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def start_web_ui():
    """Start the Gradio web interface"""
    print("\n🌐 Starting Gradio web interface...")
    print("📍 The UI will be available at: http://localhost:7860")
    print("\n🎯 Testing Tips:")
    print("  - Use the quick test buttons for easy validation")
    print("  - Try the 'Error Test' to see error handling")
    print("  - Check the 'System Status' tab for configuration info")
    print("  - With PostgreSQL, you can refresh the page to test state persistence")
    print("\n🛑 Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([sys.executable, "main.py", "--mode", "web"])
    except KeyboardInterrupt:
        print("\n👋 Web server stopped")


def main():
    """Main testing workflow"""
    print("🚀 LangGraph Travel Agent - Local Testing Guide")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        print("❌ Requirements not met. Please fix the issues above.")
        return
    
    # Interactive menu
    while True:
        print("\n📋 What would you like to do?")
        print("1. 🐘 Start PostgreSQL (recommended)")
        print("2. 🧪 Run basic functionality tests")
        print("3. 🌐 Start Gradio web interface")
        print("4. 🎯 Start web interface (skip tests)")
        print("5. 📊 Run durability tests")
        print("6. ❌ Exit")
        
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                if start_postgresql():
                    print("💡 PostgreSQL is now running. You can proceed with testing.")
                    print("   The application will automatically use PostgreSQL for state persistence.")
                else:
                    print("⚠️  PostgreSQL setup failed. The application will use memory checkpointing.")
                
            elif choice == "2":
                test_basic_functionality()
                
            elif choice == "3":
                # Full workflow: PostgreSQL + Tests + UI
                print("🔄 Full testing workflow...")
                start_postgresql()
                test_basic_functionality()
                start_web_ui()
                
            elif choice == "4":
                start_web_ui()
                
            elif choice == "5":
                print("🧪 Running comprehensive durability tests...")
                try:
                    subprocess.run([sys.executable, "test_agent_durability.py"])
                except KeyboardInterrupt:
                    print("\n🛑 Tests interrupted")
                
            elif choice == "6":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
