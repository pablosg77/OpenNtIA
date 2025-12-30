#!/bin/bash
# Start MCP Server and REST API for Network Observability

echo "🚀 Starting Observability MCP Server..."

# Start REST API in background (for testing)
echo "📡 Starting REST API on port 8000..."
uvicorn api:app --host 0.0.0.0 --port 8000 &
REST_PID=$!

# Start MCP Server on port 3334
echo "🔧 Starting MCP Server on port 3334..."
fastmcp run server.py --host 0.0.0.0 --port 3334

# Cleanup on exit
trap "echo '🛑 Stopping servers...'; kill $REST_PID 2>/dev/null" EXIT
