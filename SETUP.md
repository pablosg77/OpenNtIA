# Quick Setup Guide

Get the Observability MCP Server running in 5 minutes.

---

## Prerequisites

- Docker & Docker Compose installed
- Python 3.8+ (if running MCP server locally)
- Linux/macOS/WSL2

---

## Step 1: Start Infrastructure

```bash
cd /home/ubuntu/openntIA
docker-compose up -d
```

Verify:
```bash
docker-compose ps
# Should show influxdb, grafana, and mcp containers running
```

---

## Step 2: Get API Tokens

### InfluxDB Token

1. Open http://localhost:8086
2. Login with credentials from `docker-compose.yaml`:
   - Username: `admin`
   - Password: `admin123`
3. Go to **Data** → **API Tokens**
4. Copy the default token or generate a new one

### Grafana Token

1. Open http://localhost:3000
2. Login:
   - Username: `admin`
   - Password: `admin` (default)
3. Go to **Configuration** (⚙️) → **API Keys**
4. Click **New API Key**:
   - Name: `mcp-server`
   - Role: **Admin**
5. Copy the generated token

---

## Step 3: Configure MCP Server

```bash
cd mcp
cp config.example.py config.py
nano config.py
```

Update these values:
```python
INFLUX_TOKEN = "your-influxdb-token-here"
GRAFANA_TOKEN = "your-grafana-token-here"
```

---

## Step 4: Choose Deployment Mode

### Option A: Local (Development)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start MCP server
./start_servers.sh
```

Verify:
```bash
curl http://localhost:3333/grafana/dashboards
```

### Option B: Docker (Production)

Already running if you used `docker-compose up -d` in Step 1!

Verify:
```bash
docker-compose logs mcp
curl http://localhost:3333/grafana/dashboards
```

---

## Step 5: Configure AI Client

### For Claude Desktop

1. Find config file location:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add this configuration:
```json
{
  "mcpServers": {
    "observability-mcp": {
      "command": "python3",
      "args": ["/home/ubuntu/openntIA/mcp/mcp_bridge.py"],
      "env": {}
    }
  }
}
```

3. Restart Claude Desktop

4. Verify: Click the tools icon (🔨) - you should see 3 tools

### For VS Code + GitHub Copilot

1. Install the **Model Context Protocol** extension

2. Create/edit `.vscode/settings.json`:
```json
{
  "mcp.servers": {
    "observability-mcp": {
      "command": "python3",
      "args": ["/home/ubuntu/openntIA/mcp/mcp_bridge.py"],
      "cwd": "/home/ubuntu/openntIA/mcp"
    }
  }
}
```

3. Reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"

---

## Step 6: Test It!

Ask your AI assistant:

- "What interfaces have the highest bandwidth utilization in the last 24 hours?"
- "Show me all available Grafana dashboards"
- "What is the CPU and memory usage of all devices?"

---

## Quick Commands

```bash
# Start everything
docker-compose up -d && cd mcp && ./start_servers.sh

# Stop everything
docker-compose down && pkill -f server.py

# View logs
docker-compose logs -f

# Check status
docker-compose ps && ps aux | grep server.py

# Test API
curl http://localhost:3333/grafana/dashboards
```

---

## Troubleshooting

### Containers won't start
```bash
docker-compose logs -f
docker-compose down -v && docker-compose up -d
```

### MCP server not responding
```bash
# If local: restart
cd mcp && ./start_servers.sh

# If Docker: check logs
docker-compose logs mcp
```

### Claude Desktop doesn't show tools
1. Verify MCP server is running: `ps aux | grep server.py`
2. Check path in config file is correct
3. Completely restart Claude Desktop

---

## Configuration Reference

**InfluxDB**
- URL: http://localhost:8086
- Org: `network` | Bucket: `juniper`

**Grafana**
- URL: http://localhost:3000
- Login: `admin` / `admin`

**MCP Server**
- REST API: http://localhost:3333
- Config: `mcp/config.py`

---

**For full documentation, see [`README.md`](README.md)**
