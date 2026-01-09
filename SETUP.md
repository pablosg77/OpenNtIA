# Quick Setup Guide

Get the complete Juniper Network Observability stack running in 10 minutes.

---

## Prerequisites

- Docker & Docker Compose installed
- Python 3.8+ (if running MCP server locally)
- SSH access to Juniper devices (MX Series routers)
- Linux/macOS/WSL2

---

## Step 1: Start All Services

```bash
cd /home/ubuntu/openntIA
docker-compose up -d
```

This starts:
- ✅ InfluxDB (time-series database)
- ✅ Grafana (visualization)
- ✅ Telegraf Collector (data collection)
- ✅ MCP Server (AI integration, if using Docker)

Verify all containers are running:
```bash
docker-compose ps
# Should show: influxdb, grafana, collector, mcp
```

---

## Step 2: Configure Device Access

### 2.1 Configure Juniper Credentials

```bash
cd collector/data
nano credentials.yaml
```

Add your device credentials:
```yaml
- username: "your-junos-username"
  password: "your-junos-password"
```

### 2.2 Configure Target Routers

```bash
nano routers.yaml
```

List your Juniper devices:
```yaml
- hostname: "mx960-core1"
- hostname: "mx960-core2"
- hostname: "mx480-edge1"
```

### 2.3 Restart Collector

```bash
cd /home/ubuntu/openntIA
docker-compose restart collector
```

---

## Step 3: Verify Data Collection

Wait ~60 seconds for first collection cycle, then check:

```bash
# View collector logs
docker logs -f collector

# Query InfluxDB for data
docker exec influxdb influx query \
  --org network \
  --token influx-token \
  'from(bucket: "juniper") 
    |> range(start: -5m) 
    |> filter(fn: (r) => r._measurement == "pfe_exceptions")
    |> limit(n: 10)'
```

You should see PFE exception data from your devices.

---

## Step 4: Get API Tokens (For AI Integration)

### InfluxDB Token

1. Open http://localhost:8086
2. Login:
   - Username: `admin`
   - Password: `admin123`
3. Go to **Data** → **API Tokens**
4. Copy the token (default: `influx-token`)

### Grafana Token

1. Open http://localhost:3000
2. Login:
   - Username: `admin`
   - Password: `admin`
3. Go to **Configuration** (⚙️) → **API Keys**
4. Click **New API Key**:
   - Name: `mcp-server`
   - Role: **Admin**
5. Copy the generated token

---

## Step 5: Configure MCP Server (Local Only)

**Skip this step if using Docker deployment.**

For local Python deployment:

```bash
cd mcp
cp config.example.py config.py
nano config.py
```

Update tokens:
```python
INFLUX_TOKEN = "influx-token"
GRAFANA_TOKEN = "your-grafana-token-here"
```

Install and start:
```bash
pip install -r requirements.txt
./start_servers.sh
```

---

## Step 6: Verify MCP Server

Test the API:
```bash
# List dashboards
curl http://localhost:3333/grafana/dashboards

# Query PFE exceptions
curl -X POST http://localhost:3333/influx/query \
  -H "Content-Type: application/json" \
  -d '{"flux": "from(bucket: \"juniper\") |> range(start: -1h) |> filter(fn: (r) => r._measurement == \"pfe_exceptions\") |> limit(n: 5)"}'
```

---

## Step 7: Configure AI Client (Optional)

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

4. Verify: Click the tools icon (🔨) - you should see 3 tools:
   - `query_influx`
   - `list_dashboards`
   - `get_dashboard`

### For VS Code + GitHub Copilot

1. Install the **Model Context Protocol** extension in VS Code

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

4. Verify: Open Copilot Chat and ask "List Grafana dashboards"

---

## Step 8: Test with AI

Ask your AI assistant:

- **"Show me the PFE exception rate for all devices in the last hour"**
- **"Which device has the highest rate of firewall_discard exceptions?"**
- **"List all Grafana dashboards"**
- **"Show me devices with sw_error exceptions greater than 50/min"**

---

## Quick Commands Reference

```bash
# Start all services
docker-compose up -d

# View all logs
docker-compose logs -f

# View specific service logs
docker logs -f collector
docker logs -f influxdb
docker logs -f grafana
docker logs -f mcp

# Restart collector after config changes
docker-compose restart collector

# Stop everything
docker-compose down

# Check status
docker-compose ps

# Test data collection
docker exec influxdb influx query \
  --org network --token influx-token \
  'from(bucket: "juniper") |> range(start: -5m) |> limit(n: 10)'

# Test MCP server
curl http://localhost:3333/grafana/dashboards
```

---

## Configuration Files Reference

| File | Purpose | When to Edit |
|------|---------|--------------|
| `collector/data/credentials.yaml` | Junos SSH credentials | Initial setup |
| `collector/data/routers.yaml` | Target device list | Add/remove devices |
| `collector/data/telegraf.conf` | Collection interval | Change frequency |
| `mcp/config.py` | API tokens (local only) | MCP server config |
| `docker-compose.yaml` | Service orchestration | Change ports/env vars |

---

## Troubleshooting

### Containers won't start
```bash
docker-compose logs -f
docker-compose down -v && docker-compose up -d
```

<<<<<<< HEAD
### Can't connect to InfluxDB/Grafana
```bash
# Verify containers are running
docker-compose ps

# Check ports
sudo netstat -tulpn | grep -E ':(8086|3000)'
```

### MCP server not responding
```bash
# If running locally
ps aux | grep server.py
cd mcp && ./start_servers.sh

# If running in Docker
docker-compose logs mcp
docker-compose restart mcp
```

### No data being collected
```bash
# Check collector logs
docker logs -f collector

# Verify device connectivity
docker exec collector ping <router-hostname>

# Check credentials
cat collector/data/credentials.yaml
cat collector/data/routers.yaml

# Restart collector
docker-compose restart collector
```

### Can't connect to InfluxDB/Grafana
```bash
# Verify containers are running
docker-compose ps

# Check ports
sudo netstat -tulpn | grep -E ':(8086|3000)'
```

### MCP server not responding
```bash
# If local: restart
cd mcp && ./start_servers.sh

# If Docker: check logs
docker-compose logs mcp
docker-compose restart mcp
```

### Claude Desktop doesn't show tools
1. Verify MCP server is running: `ps aux | grep server.py`
2. Check path in config file is correct
3. Completely restart Claude Desktop (quit, not just close window)
4. Check Claude logs folder for errors

### Data collection script errors
```bash
# Test script manually
docker exec collector python3 /telegraf/pfe_exceptions.py

# Check Python dependencies
docker exec collector pip list

# Rebuild collector
docker-compose up -d --build collector
```

---

## Next Steps

- Create Grafana dashboards for PFE exceptions
- Set up alerts for high exception rates
- Add more data collectors (BGP, interfaces, system resources)
- Explore Flux queries for advanced analysis

---

**For full documentation, see [`README.md`](README.md)**

**Questions about PFE exceptions?** Ask your AI assistant:
- "Show me devices with unknown_family exceptions"
- "What's the rate of sw_error per device?"
- "Which slots have the most exceptions?"
