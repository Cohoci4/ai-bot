#!/bin/bash
# ============================================
# DevinX Ultimate — One-Click Start
# ============================================

set -e

echo "⚡ DevinX Ultimate — Starting..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install it: https://python.org"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e . --quiet 2>/dev/null || pip3 install -e . --quiet 2>/dev/null

# Create .env if missing
if [ ! -f .env ]; then
    echo ""
    echo "🔑 No .env file found. Let's set up your AI provider."
    echo ""
    echo "Get a FREE Groq API key at: https://console.groq.com"
    echo ""
    read -p "Paste your API key: " API_KEY
    
    if [ -z "$API_KEY" ]; then
        echo "❌ API key is required. Get one at https://console.groq.com"
        exit 1
    fi

    cat > .env << EOF
OPENAI_API_KEY=${API_KEY}
OPENAI_MODEL=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1
WORKSPACE_DIR=./workspace
HOST=0.0.0.0
PORT=8000
EOF
    echo "✅ .env created with Groq config"
fi

# Create workspace
mkdir -p workspace

echo ""
echo "🚀 Starting server..."
echo "   Open in browser: http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

python -m app.main
