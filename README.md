# Observability MCP Server

MCP (Model Context Protocol) server for Juniper network observability with InfluxDB and Grafana integration.

## Overview

This project provides an MCP server that allows AI assistants (Claude Desktop, GitHub Copilot) to query network metrics from InfluxDB and manage Grafana dashboards.

**Available Tools:**
- `query_influx` - Execute Flux queries against InfluxDB for network metrics
- `list_dashboards` - List all available Grafana dashboards
- `get_dashboard` - Get details of a specific Grafana dashboard by UID

---

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
│  GitHub Copilot │
└────────┬────────┘
         │ stdio (MCP Protocol)
         ▼
┌─────────────────┐
│  mcp_bridge.py  │  Bridge: stdio ↔ HTTP
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│   MCP Server    │  FastMCP (Local or Docker)
│   server.py     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌─────────┐
│ InfluxDB│ │ Grafana │  [Always Docker]
│ :8086   │ │ :3000   │
└─────────┘ └─────────┘
```

### Container Strategy

**Always in Docker:**
- **InfluxDB** (port 8086) - Time-series database
- **Grafana** (port 3000) - Visualization dashboards

**Flexible deployment:**
- **MCP Server** - Can run locally (Python) or in Docker
  - Local: Better for development, easy debugging
  - Docker: Better for production, portable deployment

---

## Quick Start

### 1. Start Infrastructure (InfluxDB + Grafana)

```bash
cd /home/ubuntu/openntIA
docker-compose up -d
```

Verify containers are running:
```bash
docker-compose ps
```

### 2. Configure Credentials

```bash
cd mcp
cp config.example.py config.py
nano config.py
```

Edit with your tokens:
```python
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "your-influxdb-token"
INFLUX_ORG = "network"
INFLUX_BUCKET = "juniper"

GRAFANA_URL = "http://localhost:3000"
GRAFANA_TOKEN = "your-grafana-api-key"
```

**Get tokens:**
- InfluxDB: http://localhost:8086 → Data → API Tokens
- Grafana: http://localhost:3000 → Configuration → API Keys

### 3. Start MCP Server

**Option A: Local (Recommended for development)**
```bash
cd mcp
pip install -r requirements.txt
./start_servers.sh
```

**Option B: Docker (Recommended for production)**
```bash
docker-compose up -d --build
# MCP server already included in docker-compose.yaml
```

### 4. Verify

```bash
# Test REST API
curl http://localhost:3333/grafana/dashboards

# Test health
curl http://localhost:8086/health  # InfluxDB
curl http://localhost:3000/api/health  # Grafana
```

---

## Client Configuration

### Claude Desktop

Edit configuration file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add:
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

Restart Claude Desktop and verify tools appear (🔨 icon).

### VS Code + GitHub Copilot

Create/edit `.vscode/settings.json`:
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

Reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"

---

## Deployment Options

### Option 1: Hybrid (Development)

**InfluxDB + Grafana in Docker, MCP Server local**

```bash
# Start infrastructure
docker-compose up -d

# Start MCP server locally
cd mcp
pip install -r requirements.txt
./start_servers.sh
```

✅ Easy debugging, fast iteration  
✅ Direct access to Python debugger  
❌ Requires Python on host

### Option 2: Full Docker (Production)

**Everything in Docker**

```bash
# Start all services
docker-compose up -d --build

# View logs
docker-compose logs -f mcp
```

✅ Consistent deployment, portable  
✅ Isolated environments  
❌ More complex debugging

### Option 3: Remote Infrastructure

**InfluxDB + Grafana on remote server**

Edit `mcp/config.py`:
```python
INFLUX_URL = "http://remote-server.com:8086"
GRAFANA_URL = "http://remote-server.com:3000"
```

✅ Centralized data, distributed access  
❌ Network latency, requires exposing services

---

## Project Structure

```
openntIA/
├── README.md                   This file
├── SETUP.md                    Quick setup guide
├── docker-compose.yaml         Infrastructure (InfluxDB, Grafana, MCP)
│
├── mcp/                        MCP Server
│   ├── server.py              Main MCP server (FastMCP)
│   ├── mcp_bridge.py          Bridge: stdio ↔ HTTP
│   ├── api.py                 REST API (testing)
│   ├── config.py              Configuration
│   ├── config.example.py      Configuration template
│   ├── requirements.txt       Python dependencies
│   ├── start_servers.sh       Start script
│   ├── verify_setup.py        Setup verification
│   ├── Dockerfile             Docker image
│   └── tools/
│       ├── influx.py          InfluxDB tools
│       └── grafana.py         Grafana tools
│
├── claude_desktop_config.json  Example for Claude
└── .vscode/
    └── settings.json           Example for VS Code
```

---

## Usage Examples

Once configured, ask your AI assistant:

- "What interfaces have the highest bandwidth utilization in the last 24 hours?"
- "Show me all Grafana dashboards"
- "What is the CPU and memory usage across all devices?"
- "How many BGP peers are active on mx960-core1?"

---

## Common Commands

### Docker Management

```bash
# Start services
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down
```

### MCP Server (Local)

```bash
# Install dependencies
pip install -r mcp/requirements.txt

# Start server
cd mcp && ./start_servers.sh

# Stop server
pkill -f server.py

# View processes
ps aux | grep server.py
```

### Testing

```bash
# Test REST API
curl http://localhost:3333/

# List dashboards
curl http://localhost:3333/grafana/dashboards

# Query InfluxDB
curl -X POST http://localhost:3333/influx/query \
  -H "Content-Type: application/json" \
  -d '{"flux": "from(bucket: \"juniper\") |> range(start: -1h) |> limit(n: 5)"}'
```

### InfluxDB

```bash
# Enter CLI
docker exec -it influxdb influx

# Check health
curl http://localhost:8086/health

# List measurements
curl -X POST http://localhost:3333/influx/query \
  -H "Content-Type: application/json" \
  -d '{"flux": "import \"influxdata/influxdb/schema\"\nschema.measurements(bucket: \"juniper\")"}'
```

### Grafana

```bash
# Open UI
xdg-open http://localhost:3000

# Login: admin / admin (default)

# List dashboards via API
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:3000/api/search
```

---

## Troubleshooting

### Containers won't start

```bash
# Check logs
docker-compose logs -f

# Restart
docker-compose restart

# Clean restart
docker-compose down -v
docker-compose up -d
```

### MCP Server can't connect to InfluxDB/Grafana

**If MCP is local:**
```bash
# Verify containers are running
docker-compose ps

# Test connectivity
curl http://localhost:8086/health
curl http://localhost:3000/api/health

# Check config.py URLs
cat mcp/config.py | grep URL
```

**If MCP is in Docker:**
```bash
# Use service names in config
INFLUX_URL = "http://influxdb:8086"
GRAFANA_URL = "http://grafana:3000"

# Or use --network host
docker run --network host ...
```

### Claude Desktop doesn't show tools

1. Verify MCP server is running:
   ```bash
   ps aux | grep server.py
   ```

2. Check configuration path in `claude_desktop_config.json`

3. Restart Claude Desktop completely

4. Check Claude logs:
   - macOS: `~/Library/Logs/Claude/`
   - Linux: `~/.config/Claude/logs/`

### VS Code + Copilot doesn't see tools

1. Install MCP extension: "Model Context Protocol"
2. Verify `.vscode/settings.json` configuration
3. Reload VS Code: `Ctrl+Shift+P` → "Reload Window"
4. Check Output panel for errors

### Connection refused errors

```bash
# Verify all services are up
docker-compose ps

# Check ports are open
sudo netstat -tulpn | grep -E ':(8086|3000|3333|3334)'

# Restart everything
docker-compose restart
cd mcp && ./start_servers.sh
```

---

## Data Backup

### InfluxDB Backup

```bash
# Create backup
docker exec influxdb influx backup /tmp/backup -t influx-token
docker cp influxdb:/tmp/backup ./influxdb-backup-$(date +%Y%m%d)
```

### Grafana Backup

```bash
# Backup dashboards and config
docker exec grafana tar czf /tmp/grafana.tar.gz /var/lib/grafana
docker cp grafana:/tmp/grafana.tar.gz ./grafana-backup-$(date +%Y%m%d).tar.gz
```

---

## Security Notes

⚠️ **Important:**
- Don't expose MCP server to the internet without authentication
- Store credentials in environment variables or secure vaults
- Use HTTPS in production
- Limit Flux query complexity to prevent resource exhaustion
- Regularly update Docker images

---

## Ports Reference

| Service | Port | Description | Required |
|---------|------|-------------|----------|
| InfluxDB | 8086 | Time-series database API | Yes |
| Grafana | 3000 | Dashboard UI and API | Yes |
| MCP Server | 3334 | MCP HTTP/SSE endpoint | Optional |
| REST API | 3333 | Testing API | Optional |

---

## Development

### Adding New Tools

1. Create function in `mcp/tools/`:

```python
from mcp.server.fastmcp import FastMCP

@mcp.tool()
def my_new_tool(param: str) -> dict:
    """Tool description"""
    # Implementation
    return {"result": "data"}
```

2. Restart MCP server
3. Tool appears automatically in clients

### Running Tests

```bash
# Verify setup
cd mcp
python3 verify_setup.py

# Test individual components
python3 -c "from tools.influx import query_influx; print(query_influx('from(bucket: \"juniper\") |> range(start: -1h) |> limit(n: 1)'))"
```

---

## License

Internal use for network observability purposes.

## Contributing

To add features:
1. Create new tool functions with `@mcp.tool()` decorator
2. Update `requirements.txt` if adding dependencies
3. Document in README.md
4. Test with both Claude Desktop and VS Code

---

**Network observability powered by AI** 🚀📊🤖
