#!/bin/bash
# Setup script for LangGraph Travel Agent

set -e  # Exit on any error

echo "🚀 Setting up LangGraph Travel Agent"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found"
    echo "   Please run this script from the travel-agent directory"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8+ required (found: $python_version)"
    exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📥 Installing dependencies..."
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Activate the environment: source venv/bin/activate"
echo "2. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'"
echo "3. (Optional) Start PostgreSQL: docker-compose -f docker-compose.local.yml up -d"
echo "4. Start the application:"
echo "   - Interactive setup: python test_locally.py"
echo "   - Direct web UI: python main.py --mode web"
echo ""
echo "🌐 The web interface will be available at: http://localhost:7860"
