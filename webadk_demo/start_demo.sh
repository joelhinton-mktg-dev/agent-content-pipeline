#!/bin/bash
# Quick Start Script for WebADK Demo Interface

echo "🚀 Starting AI Content Pipeline Demo Interface"
echo "=============================================="

# Check if we're in the right directory
if [[ ! -f "app.py" ]]; then
    echo "❌ Error: app.py not found. Please run this script from the webadk_demo directory."
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "../.venv" ]] && [[ ! -d ".venv" ]] && [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: No virtual environment detected. Consider using a venv."
fi

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP 'Python \K[0-9]+\.[0-9]+')
min_version="3.9"

if [[ "$(printf '%s\n' "$min_version" "$python_version" | sort -V | head -n1)" != "$min_version" ]]; then
    echo "❌ Error: Python 3.9+ required, found Python $python_version"
    exit 1
fi

echo "✅ Python $python_version detected"

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
if ! python3 -c "import fastapi, uvicorn, websockets, jinja2" 2>/dev/null; then
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
    if [[ $? -ne 0 ]]; then
        echo "❌ Failed to install dependencies. Please check your environment."
        exit 1
    fi
else
    echo "✅ Dependencies ready"
fi

# Run test suite
echo "🧪 Running quick validation..."
python3 test_demo.py > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
    echo "⚠️  Some tests failed. Running detailed test..."
    python3 test_demo.py
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Validation passed"
fi

# Check API keys
echo "🔑 Checking API configuration..."
if [[ -z "$GOOGLE_API_KEY" ]] || [[ -z "$PERPLEXITY_API_KEY" ]] || [[ -z "$OPENAI_API_KEY" ]]; then
    echo "⚠️  Some API keys not found in environment."
    echo "   The demo will start but content generation may fail."
    echo "   Ensure .env files are configured in agent directories."
fi

# Display startup information
echo ""
echo "🌐 Demo Interface Information:"
echo "   URL: http://localhost:8080"
echo "   Username: demo"
echo "   Password: content2024"
echo ""
echo "📋 Demo Features:"
echo "   • 8-stage AI content pipeline"
echo "   • Real-time progress updates"
echo "   • Professional citations with working URLs"
echo "   • AI-generated contextual images"
echo "   • Downloadable content packages"
echo ""
echo "💡 Demo Tips:"
echo "   • Try: 'Generate an article about AI in healthcare'"
echo "   • Use quick start buttons for instant demos"
echo "   • Watch real-time progress updates"
echo "   • Download generated content files"
echo ""

# Start the demo server
echo "🚀 Starting demo server..."
echo "   Press Ctrl+C to stop"
echo ""

# Export port for cloud deployments
export PORT=${PORT:-8080}

# Start with appropriate settings for demo
python3 app.py

# Cleanup message
echo ""
echo "👋 Demo server stopped"
echo "   Generated content remains in downloads/ directory"