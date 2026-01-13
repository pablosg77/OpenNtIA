# Observability MCP Server

MCP (Model Context Protocol) server for Juniper network observability with InfluxDB and Grafana integration.

## Overview

This project provides a complete observability stack for Juniper networks:

1. **Data Collection**: Automated collection of PFE exceptions from Juniper devices via Telegraf
2. **Storage**: Time-series data stored in InfluxDB
3. **Visualization**: Grafana dashboards for metrics analysis
4. **AI Integration**: MCP server enabling AI assistants (Claude Desktop, GitHub Copilot) to query metrics using natural language

**Available MCP Tools:**
- `query_influx` - Execute Flux queries against InfluxDB for network metrics
- `check_suspicious_exceptions` - Detect PFE exception anomalies with 3 intelligent rules ⭐ NEW
- `list_dashboards` - List all available Grafana dashboards
- `get_dashboard` - Get details of a specific Grafana dashboard by UID

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI Clients Layer                     │
│         Claude Desktop  |  GitHub Copilot               │
└────────────────────┬────────────────────────────────────┘
                     │ stdio (MCP Protocol)
┌────────────────────▼────────────────────────────────────┐
│                   MCP Bridge                            │
│                 mcp_bridge.py                           │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP
┌────────────────────▼────────────────────────────────────┐
│                   MCP Server                            │
│              server.py (FastMCP)                        │
│         [Local Python or Docker]                        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        ▼                           ▼
┌──────────────┐            ┌──────────────┐
│   InfluxDB   │◄───────────│   Telegraf   │
│   :8086      │            │  (Collector) │
│   [Docker]   │            │   [Docker]   │
└──────┬───────┘            └──────▲───────┘
       │                           │
       │                           │ SSH (Junos PyEZ)
       │                           │ Collects PFE exceptions
       │                           │
       ▼                           ▼
┌──────────────┐         ┌────────────────────┐
│   Grafana    │         │  Juniper Devices   │
│   :3000      │         │  (MX960, etc.)     │
│   [Docker]   │         └────────────────────┘
└──────────────┘
```

### Component Breakdown

**Data Collection (Always Docker):**
- **Telegraf Collector** - Python script collecting PFE exceptions every 60s
  - Connects to Juniper devices via SSH (Junos PyEZ)
  - Executes `show pfe statistics exceptions` per slot
  - Normalizes and formats data for InfluxDB
  - Configurable via `telegraf.conf` and `routers.yaml`

**Storage & Visualization (Always Docker):**
- **InfluxDB** (port 8086) - Time-series database for metrics
- **Grafana** (port 3000) - Dashboard visualization

**AI Integration (Flexible):**
- **MCP Server** - Can run locally (Python) or in Docker
  - Local: Better for development, easy debugging
  - Docker: Better for production, portable deployment

---

## Quick Start Guide

Follow these steps in order to set up the complete observability stack:

### Step 1: Start Infrastructure Services

Start InfluxDB, Grafana, and the Telegraf collector:

```bash
cd /home/ubuntu/openntIA
docker-compose up -d
```

Verify all containers are running:
```bash
docker-compose ps
# Should show: influxdb, grafana, mcp, collector (telegraf)
```

**What happens:**
- InfluxDB starts on port 8086
- Grafana starts on port 3000
- Telegraf collector container starts and waits for configuration
- MCP server container starts (if using Docker deployment)

### Step 2: Configure Juniper Device Access

Edit the collector configuration files:

```bash
cd collector/data

# 1. Configure device credentials
nano credentials.yaml
```

Add your Juniper device credentials:
```yaml
- username: "your-junos-username"
  password: "your-junos-password"
```

```bash
# 2. Configure target routers
nano routers.yaml
```

Add your Juniper devices:
```yaml
- hostname: "mx960-core1"
- hostname: "mx960-core2"
- hostname: "mx480-edge1"
```

**Security Note**: Store credentials securely. Consider using SSH keys or encrypted vaults in production.

### Step 3: Verify Data Collection

Wait 60 seconds (default collection interval) and check if data is being collected:

```bash
# Check collector logs
docker logs -f collector

# Query InfluxDB for collected data
docker exec influxdb influx query \
  --org network \
  --token influx-token \
  'from(bucket: "juniper") 
    |> range(start: -5m) 
    |> filter(fn: (r) => r._measurement == "pfe_exceptions")
    |> limit(n: 10)'
```

You should see PFE exception data from your Juniper devices.

### Step 4: Configure InfluxDB and Grafana Access Tokens

**Get InfluxDB Token:**
1. Open http://localhost:8086
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin123`
3. Go to **Data** → **API Tokens**
4. Copy the default token or create a new one

**Get Grafana Token:**
1. Open http://localhost:3000
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin`
3. Go to **Configuration** (⚙️) → **API Keys**
4. Click **New API Key**:
   - Name: `mcp-server`
   - Role: **Admin**
5. Copy the generated token

### Step 5: Configure MCP Server (Local Deployment Only)

**Skip this step if using Docker deployment (recommended).**

For local Python deployment:

```bash
cd mcp

# Create configuration file
cp config.example.py config.py
nano config.py
```

Edit with your tokens:
```python
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "influx-token"  # Use token from Step 4
INFLUX_ORG = "network"
INFLUX_BUCKET = "juniper"

GRAFANA_URL = "http://localhost:3000"
GRAFANA_TOKEN = "your-grafana-api-key"  # Use token from Step 4
```

Install dependencies and start:
```bash
pip install -r requirements.txt
./start_servers.sh
```

### Step 6: Verify MCP Server

Test the MCP server REST API:

```bash
# List Grafana dashboards
curl http://localhost:3333/grafana/dashboards

# Query recent PFE exceptions
curl -X POST http://localhost:3333/influx/query \
  -H "Content-Type: application/json" \
  -d '{
    "flux": "from(bucket: \"juniper\") |> range(start: -1h) |> filter(fn: (r) => r._measurement == \"pfe_exceptions\") |> limit(n: 10)"
  }'

# Check service health
curl http://localhost:8086/health  # InfluxDB
curl http://localhost:3000/api/health  # Grafana
```

### Step 7: Configure AI Client (Optional)

To use with Claude Desktop or GitHub Copilot, see [Client Configuration](#client-configuration) section below.

---

## Project Structure

```
openntIA/
├── README.md                   This file
├── SETUP.md                    Quick setup guide
├── docker-compose.yaml         Infrastructure services
│
├── collector/                  Data Collection
│   ├── Dockerfile             Telegraf + Python collector
│   ├── data/
│   │   ├── credentials.yaml   Junos device credentials
│   │   ├── routers.yaml       Target devices list
│   │   ├── pfe_exceptions.py  PFE exception collector script
│   │   └── telegraf.conf      Telegraf configuration
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

## Data Collection Details

### What Data is Collected

The collector runs every 60 seconds (configurable in `telegraf.conf`) and gathers:

**PFE Exceptions per Slot:**
- `firewall_discard` - Packets dropped by firewall rules
- `iif_down` - Input interface down exceptions
- `unknown_iif` - Unknown input interface
- `unknown_family` - Unknown protocol family
- `sw_error` - Software errors
- `discard_route` - Discarded by routing policy
- `invalid_stream` - Invalid packet stream
- And more...

**Collected for each:**
- Device hostname
- FPC slot number
- Exception type
- Exception count (cumulative counter)
- Timestamp

### Collection Script

The `pfe_exceptions.py` script:
1. Reads device list from `routers.yaml`
2. Connects to each device via SSH (Junos PyEZ)
3. Executes `show pfe statistics exceptions fpc <N>` for each slot
4. For MPC1 cards (AFT), uses `show jnh exceptions level terse`
5. Parses output and extracts non-zero exception counts
6. Formats data in InfluxDB line protocol
7. Telegraf reads the output and sends to InfluxDB

### Customizing Collection

**Change collection interval:**
Edit `collector/data/telegraf.conf`:
```toml
[agent]
  interval = "60s"  # Change to desired interval
```

**Add more routers:**
Edit `collector/data/routers.yaml`:
```yaml
- hostname: "new-router-1"
- hostname: "new-router-2"
```

**Modify script timeout:**
Edit `collector/data/telegraf.conf`:
```toml
[[inputs.exec]]
  timeout = "600s"  # 10 minutes default
```

---

## Client Configuration

### VS Code + GitHub Copilot (Recommended for Development)

**Important: MCP configuration can be stored in two locations. We use global configuration to avoid confusion.**

#### Global Configuration (Recommended)

The MCP server is configured in `~/.vscode/mcp-servers.json` (global for all workspaces):

```bash
# Create or edit the global configuration file
mkdir -p ~/.vscode
cat > ~/.vscode/mcp-servers.json << 'EOF'
{
  "mcpServers": {
    "observability-mcp": {
      "command": "python3",
      "args": ["/home/ubuntu/openntIA/mcp/mcp_bridge.py"],
      "env": {
        "MCP_SERVER_URL": "http://localhost:3333"
      }
    }
  }
}
EOF
```

**Why global configuration?**
- ✅ Works across all your VS Code workspaces
- ✅ No need to configure each project separately
- ✅ Won't create conflicts with project-specific settings
- ✅ Absolute paths work from any workspace

**Note:** This project includes `.vscode/settings.json` as an example, but the active configuration is in `~/.vscode/mcp-servers.json`.

#### Setup Steps:

1. **Start the infrastructure:**
   ```bash
   cd /home/ubuntu/openntIA
   docker-compose up -d
   ```

2. **Create the global MCP configuration** (command above)

3. **Reload VS Code**: `Ctrl+Shift+P` → "Developer: Reload Window"

4. **Verify Tools**: Click the 🔨 icon in GitHub Copilot Chat sidebar

5. **You should see 4 tools:**
   - `query_influx` - Execute Flux queries against InfluxDB
   - `check_suspicious_exceptions` - Detect PFE exception anomalies ⭐
   - `list_dashboards` - List available Grafana dashboards
   - `get_dashboard` - Get dashboard details by UID

#### Test the Integration:

Open GitHub Copilot Chat (`Ctrl+Alt+I`) and try:
```
"Detecta excepciones sospechosas en la última hora"
"Muéstrame los dispositivos con sw_error"
"Lista los dashboards de Grafana"
"Query PFE exceptions in the last 24 hours"
```

#### Troubleshooting:

**Tools don't appear?**
1. Verify MCP server is running: `curl http://localhost:3333/`
2. Check configuration path: `cat ~/.vscode/mcp-servers.json`
3. Completely reload VS Code: Close all windows and reopen
4. Check VS Code Output panel: View → Output → "Model Context Protocol"

**"Command not found" error?**
- Update the `command` path to your Python installation:
  ```bash
  which python3  # Get the full path
  ```
- Update the `args` path to match your clone location

---

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
      "env": {
        "MCP_SERVER_URL": "http://localhost:3333"
      }
    }
  }
}
```

**Important:** Update `/home/ubuntu/openntIA` to match your actual clone path.

Restart Claude Desktop **completely** (quit, not just close window) and verify tools appear (🔨 icon).

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

### Network Monitoring Queries
- "What interfaces have the highest bandwidth utilization in the last 24 hours?"
- "Show me all Grafana dashboards"
- "What is the CPU and memory usage across all devices?"
- "How many BGP peers are active on mx960-core1?"

### PFE Exception Analysis ⭐ NEW
- **"Detecta excepciones sospechosas en la última hora"**
- **"Show me devices with sw_error exceptions"**
- **"Are there any critical exceptions right now?"**
- **"Check for firewall_discard spikes in the last 6 hours"**

#### About `check_suspicious_exceptions`

This AI-powered tool analyzes PFE exceptions using 3 intelligent detection rules:

**Rule 1: New Exceptions**
- Detects when exceptions go from 0 to ≥1 exc/s and stay elevated
- Example: A device suddenly starts reporting `sw_error` after being clean

**Rule 2: Spike Detection**
- Compares current rates against 2-day historical baseline
- Detects sudden peaks (>2x baseline + 3σ)
- Example: `firewall_discard` jumps from 0.2 to 1.3 exc/s

**Rule 3: Sustained Behavior Change**
- Detects gradual but significant increases over baseline
- Example: `sw_error` rate increases from 4.8 to 6.9 exc/s (+42%)

**Severity Levels:**
- 🔴 **CRITICAL**: `egress_pfe_unspecified`, `unknown_family`
- 🟠 **HIGH**: `sw_error`, `unknown_iif`
- 🟡 **MEDIUM**: `firewall_discard`
- 🟢 **LOW**: `discard_route`

**Output includes:**
- Device name and slot number
- Exception type and severity
- Detection rule that triggered
- Timestamp when anomaly was detected
- Detailed metrics (current rate, baseline, percentage change)

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

## Quick Reference Card

### 🚀 Getting Started
```bash
docker-compose up -d                    # Start all services
curl http://localhost:3333/             # Verify MCP server
```

### 🔧 MCP Configuration (VS Code)
```bash
# Create global config (one-time setup)
mkdir -p ~/.vscode
cat > ~/.vscode/mcp-servers.json << 'EOF'
{
  "mcpServers": {
    "observability-mcp": {
      "command": "python3",
      "args": ["/home/ubuntu/openntIA/mcp/mcp_bridge.py"],
      "env": {"MCP_SERVER_URL": "http://localhost:3333"}
    }
  }
}
EOF
```

### 🎯 AI Query Examples
```
"Detecta excepciones sospechosas en la última hora"
"Show me devices with sw_error > 5 exc/s"
"List Grafana dashboards"
"Query PFE exceptions for hl4mmt1-301"
```

### 📊 Available Tools (4)
1. **`query_influx`** - Execute Flux queries
2. **`check_suspicious_exceptions`** - AI-powered anomaly detection ⭐
3. **`list_dashboards`** - List Grafana dashboards  
4. **`get_dashboard`** - Get dashboard details

### 🔗 Service URLs
- InfluxDB UI: http://localhost:8086 (admin/admin123)
- Grafana UI: http://localhost:3000 (admin/admin)
- MCP API: http://localhost:3333

---

**Network observability powered by AI** 🚀📊🤖
