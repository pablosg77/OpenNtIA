# Observability MCP Server

MCP (Model Context Protocol) server for Juniper network observability with InfluxDB and Grafana integration.

![Demo](assets/demo_fast.gif)

## Overview

This project provides a complete observability stack for Juniper networks:

1. **Data Collection**: Automated collection of PFE exceptions from Juniper devices via Telegraf
2. **Storage**: Time-series data stored in InfluxDB
3. **Visualization**: Grafana dashboards for metrics analysis
4. **AI Integration**: MCP servers enabling AI assistants (Claude Desktop, GitHub Copilot) to:
   - Query metrics using natural language
   - Execute Junos commands directly on devices
   - Debug PFE exceptions with packet captures

**Available MCP Servers:**

### 🔍 Observability MCP (`observability-mcp`)
Network monitoring and anomaly detection tools:
- `query_influx` - Execute Flux queries against InfluxDB for network metrics
- `check_suspicious_exceptions` - Detect PFE exception anomalies with **6 intelligent rules** ⭐
- `list_dashboards` - List all available Grafana dashboards
- `get_dashboard` - Get details of a specific Grafana dashboard by UID

### ⚙️ Junos MCP (`junos-mcp-server`)
Direct device management and troubleshooting:
- `execute_junos_command` - Execute any Junos CLI command
- `get_junos_config` - Retrieve device configuration
- `junos_config_diff` - Compare configurations
- `gather_device_facts` - Get device hardware/software info
- `get_router_list` - List all configured devices
- `pfe_debug_exceptions` - **Capture and decode discarded packets** 🔥 NEW
- `load_and_commit_config` - Apply configuration changes

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                CLIENT LAYER                                      │
└──────────────────────────────────────────────────────────────────────────────────┘
              ┌──────────────────┐              ┌──────────────────┐
              │  Claude Desktop  │              │  GitHub Copilot  │
              │                  │              │   (VS Code)      │
              └────────┬─────────┘              └────────┬─────────┘
                       │                                 │
                       │        stdio (JSON-RPC)         │
                       └──────────────┬──────────────────┘
                                      │
┌─────────────────────────────────────┼──────────────────────────────────────────┐
│                                     │            BRIDGE LAYER                  │
│                                     ▼                                          │
│                          ┌─────────────────────┐                               │
│                          │    mcp_bridge.py    │                               │
│                          │   (stdio ↔ HTTP)    │                               │
│                          └──────────┬──────────┘                               │
│                                     │                                          │
│                                     │ HTTP                                     │
└─────────────────────────────────────┼──────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┼─────────────────────────────────────────┐
│                                     │          MCP SERVER LAYER               │
│                                     │                                         │
│     ┌───────────────────────────────┼───────────────────────────────┐         │
│     │  Observability MCP            │  Junos MCP                    │         │
│     │  [Docker: mcp]                │  [Docker: junos-mcp]          │         │
│     │                               │                               │         │
│     │  ┌──────────┐  ┌───────────┐  │ ┌────────────────────┐        │         │
│     │  │ server.py│  │  api.py   │  │ │     jmcp.py        │        │         │
│     │  │ (MCP3334)│  │ (REST3333)│  │ │ (HTTP MCP30030)    │        │         │
│     │  └────┬─────┘  └─────┬─────┘  │ └──────────┬─────────┘        │         │
│     │       │              │        │            │                  │         │
│     │       ▼              ▼        │            ▼                  │         │
│     │  ┌────────────┐               │ ┌────────────────────-┐       │         │
│     │  │   tools/   │               │ │  PyEZ + Paramiko    │       │         │
│     │  │            │               │ │                     │       │         │
│     │  │ • influx   │               │ │ • execute_command   │       │         │
│     │  │ • grafana  │               │ │ • get_config        │       │         │
│     │  │            │               │ │ • gather_facts      │       │         │
│     │  │ [4 tools]  │               │ │ • pfe_debug         │       │         │
│     │  └─────┬──────┘               │ │ [7 tools]           │       │         │
│     └────────┼─────────────────────-┘ └──────────-┬─────────┘       │         │
│              │                                    │                 │         │
│              │ HTTP APIs                          │ SSH / NETCONF   │         │
└──────────────┼────────────────────────────────────┼─────────────────┘         │
               │                                    │                           │
    ┌──────────┴───────────┐                        ▼────────────┐              │
    │                      │                                     │              │
    ▼                      ▼                                     ▼              │
┌─────────────┐    ┌─────────────┐               ┌────────────────────┐         │
│  InfluxDB   │◄───│  Telegraf   │               │  Juniper Devices   │         │
│   :8086     │    │ (Collector) │               │                    │         │
│             │    │ Python      │               │ • router1          │         │
│    Metrics  │    │ SSH         │               │ • router2          │         │
│ [Docker]    │    │ [Docker]    │               │ • MX960 / MX480    │         │
│             │    │             │               │                    │         │
│ Volumes:    │    └──────▲──────┘               │ SSH :22            │         │
│ • data      │           │                      │ NETCONF :830       │         │
│ • config    │           │                      └────────────────────┘         │
└─────┬───────┘           │                                                     │
      │                   │ Data Collection (PFE exceptions)                    │
      ▼                   │                                                     │
┌─────────────┐           │                                                     │
│  Grafana    │───────────┘                                                     │
│   :3000     │                                                                 │
│ Dashboards  │                                                                 │
│ [Docker]    │                                                                 │
│ Volumes:    │                                                                 │
│ • grafana   │                                                                 │
└─────────────┘                                                                 │
└───────────────────────────────────────────────────────────────────────────────┘

```

### Component Breakdown

**AI Integration Layer:**
- **Observability MCP** - Metrics analysis and anomaly detection
- **Junos MCP** - Direct device access and troubleshooting

**Data Collection (Docker):**
- **Telegraf Collector** - Collects PFE exceptions every 60s via SSH

**Storage & Visualization (Docker):**
- **InfluxDB** (port 8086) - Time-series database
- **Grafana** (port 3000) - Dashboard visualization

---

## Quick Start Guide

### Step 1: Configure Juniper Device Access

Edit device configurations:

```bash
# For Telegraf collector
cd collector/data
nano credentials.yaml  # Add SSH credentials
nano routers.yaml      # Add device hostnames

# For Junos MCP server
cd ../../mcp-junos
nano devices.json      # Add devices with full details
```

**Example `devices.json`:**
```json
{
  "router1": {
    "ip": "10.10.20.1",
    "port": 22,
    "username": "jncie",
    "password": "jncie123"
  },
  "router2": {
    "ip": "10.10.20.3",
    "port": 22,
    "username": "jncie",
    "password": "jncie123"
  }
}
```

### Step 2: Start All Services

```bash
docker-compose up -d
```

This starts:
- ✅ InfluxDB (port 8086)
- ✅ Grafana (port 3000)
- ✅ Telegraf collector
- ✅ Observability MCP server (port 3333/3334)
- ✅ Junos MCP server (port 30030)

Verify:
```bash
docker-compose ps
# Should show: influxdb, grafana, mcp, collector, junos-mcp-server
```


### Step 3: Configure AI Client

#### VS Code + GitHub Copilot (Recommended)

Create global MCP configuration:

```bash
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
    },
    "junos-mcp-server": {
      "url": "http://127.0.0.1:30030/mcp/",
      "transport": {
        "type": "http"
      }
    }
  }
}
EOF
```

**Reload VS Code**: `Ctrl+Shift+P` → "Developer: Reload Window"

**Verify Tools**: Click 🔨 icon in Copilot Chat sidebar - you should see **11 tools** total.

---

## Complete Troubleshooting Workflow

### 🎯 End-to-End Example: Detect and Debug PFE Exception

This workflow demonstrates the power of combining both MCP servers:

#### **Step 1: Detect Suspicious Exceptions**

Ask Copilot:
```
"Detect suspicious exceptions in the last hour"
```

**Tool Used**: `check_suspicious_exceptions` (Observability MCP)

**Example Output**:
```
🚨 Suspicious Exception Detected!
- Device: router2
- Exception: hold_route
- Severity: MEDIUM
- Rate: 1.72 exc/s (+51% above baseline)
- Rule: Rule 3 (Sustained behavior change)
- Grafana: [View Dashboard]
```

#### **Step 2: Get Device Details**

Ask Copilot:
```
"Show me the Junos version of router2"
```

**Tool Used**: `execute_junos_command` (Junos MCP)

**Example Output**:
```
Hostname: router2
Model: MX960
Junos: 22.4X4.11
```

#### **Step 3: Verify Exception is Active**

Ask Copilot:
```
"Show me current PFE exception statistics on router2 slot 0"
```

**Tool Used**: `execute_junos_command` (Junos MCP)

**Command Executed**: `show pfe statistics exceptions fpc 0`

**Example Output**:
```
hold route DISC(70)    170,720 packets
```

#### **Step 4: Capture and Decode Discarded Packet** 🔥

Ask Copilot:
```
"Capture and decode the discarded packets for hold_route exception on router2"
```

**Tool Used**: `pfe_debug_exceptions` (Junos MCP)

**What Happens**:
1. Connects to device via SSH (Paramiko)
2. Enables PFE exception debugging: `debug jnh exceptions 70 discard`
3. Waits 2 seconds to capture packets
4. Disables debug: `no debug jnh exceptions 70 discard`
5. Retrieves output: `show jnh exceptions-trace fpc0`
6. Decodes packet using Scapy

**Example Output**:
```
📦 Decoded Packet:

Type: ICMP Echo Request (Ping)
Source: 192.168.252.162
Destination: 10.235.1.3
Protocol: ICMP (Type 8, Code 0)
Size: 84 bytes
TTL: 64 hops
ToS: 224 (CS7 / Network Control)

Packet Layers:
├─ Ethernet
│   ├─ dst: 2c:6b:f5:f2:67:c5
│   ├─ src: 2c:6b:f5:4d:ce:c6
│   └─ type: IPv4
├─ IPv4
│   ├─ src: 192.168.252.162
│   ├─ dst: 10.235.1.3
│   └─ proto: ICMP
└─ ICMP Echo Request
    ├─ id: 31749
    └─ seq: 27391

Exception: hold_route (DISC 70)
Reason: Packet destined to IP without resolved next-hop
```

#### **Step 5: Root Cause Analysis**

Ask Copilot:
```
"Show me the routing table for 10.235.1.3 on router2"
```

**Tool Used**: `execute_junos_command` (Junos MCP)

**Command**: `show route 10.235.1.3`

Based on the output, you can determine if:
- Route is missing
- Next-hop is down
- ARP resolution failed
- Routing policy is blocking

---

## Usage Examples by Category

### 🔍 Network Monitoring (Observability MCP)

```
"Detect suspicious exceptions in the last hour"
"Show me devices with sw_error exceptions"
"Are there any critical exceptions right now?"
"Check for firewall_discard spikes in the last 6 hours"
"List Grafana dashboards"
```

### ⚙️ Device Management (Junos MCP)

```
"Show me the list of configured Juniper devices"
"Get the Junos version of router1"
"Show interface status on router2
"Get BGP neighbor summary on router2"
"Show chassis hardware on router3"
```

### 🔥 Advanced Troubleshooting (Combined)

```
"Detect suspicious exceptions, then capture packets from the affected device"
"Show me current PFE statistics, then decode any discarded packets"
"Find devices with high exception rates, then get their system info"
"Check for hold_route exceptions, then verify routing tables"
```

### 🎯 PFE Exception Debugging Workflow

```
# Step 1: Detect
"Detect suspicious exceptions in the last hour"

# Step 2: Verify
"Show current PFE exception counters on [device] slot [N]"

# Step 3: Capture & Decode
"Capture and decode discarded packets for [exception_type] on [device]"

# Step 4: Investigate
"Show routing table for [destination_ip] on [device]"
"Show interface status on [device]"
"Get BGP neighbor status on [device]"
```

---

## Tool Reference

### Observability MCP Tools

#### `check_suspicious_exceptions`
**Purpose**: AI-powered anomaly detection with 6 intelligent rules

**Detection Rules**:
- **Rule 1**: New exceptions (0→≥1 exc/s sustained)
- **Rule 2**: Spike detection (vs 2-day baseline)
- **Rule 3**: Sustained behavior change
- **Rule 4**: Weekly baseline comparison
- **Rule 5**: Rate of change / trend detection
- **Rule 7**: Multiple exception correlation

**Example**:
```
"Detect suspicious exceptions in the last 6 hours"
```

**Output**:
- Device name
- Exception type
- Severity (CRITICAL/HIGH/MEDIUM/LOW)
- Detection rule triggered
- Timestamp when detected
- Metrics (rate, baseline, change %)
- Direct Grafana dashboard link

#### `query_influx`
Execute custom Flux queries against InfluxDB.

**Example**:
```
"Query PFE exceptions for device hl4mmt1-301 in the last hour"
```

#### `list_dashboards`, `get_dashboard`
Manage Grafana dashboards.

---

### Junos MCP Tools

#### `pfe_debug_exceptions` 🔥 NEW
**Purpose**: Capture and decode packets discarded by PFE exceptions

**Parameters**:
- `router_name`: Device hostname (required)
- `fpc`: FPC slot (default: "fpc0")
- `debug_val`: DISC code from exception (required)
- `duration`: Capture duration in seconds (default: 2)

**How it works**:
1. Connects via SSH using Paramiko
2. Enables PFE debug: `debug jnh exceptions <debug_val> discard`
3. Waits for specified duration to capture packets
4. Disables debug
5. Retrieves captured data: `show jnh exceptions-trace <fpc>`
6. Parses hex dump and decodes using Scapy
7. Returns human-readable packet analysis

**Example**:
```
"Capture discarded packets for hold_route (DISC 70) on router1"
```

**Output**:
```json
{
  "device": "router1",
  "fpc": "fpc0",
  "debug_val": "70",
  "duration": 2,
  "captured_at": "2026-01-16T09:30:45Z",
  "packet": {
    "summary": "Ether / IP / ICMP 192.168.252.162 > 10.235.1.3 echo-request",
    "layers": {
      "Ethernet": {...},
      "IP": {...},
      "ICMP": {...}
    },
    "raw_output": "...",
    "decoded": "..."
  }
}
```

#### `execute_junos_command`
Execute any Junos CLI command.

**Example**:
```
"Show BGP summary on hl4mmt1-301"
→ Executes: show bgp summary
```

#### `get_junos_config`
Retrieve device configuration (full or specific section).

**Example**:
```
"Get firewall configuration from router1"
→ Retrieves: show configuration firewall
```

#### `gather_device_facts`
Get device hardware/software information.

**Example**:
```
"Get system info for hl4mmt1-302"
→ Returns: hostname, model, version, serial, uptime
```

#### `get_router_list`
List all configured Juniper devices.

**Example**:
```
"Show me all available Juniper devices"
```

---

## DISC Code Reference

When using `pfe_debug_exceptions`, you need the DISC code for the exception type:

| Exception Type | DISC Code | Severity |
|----------------|-----------|----------|
| `firewall_discard` | 67 | MEDIUM |
| `hold_route` | 70 | MEDIUM |
| `discard_route` | 71 | LOW |
| `sw_error` | 1 | HIGH |
| `unknown_iif` | 8 | HIGH |
| `egress_pfe_unspecified` | 3 | CRITICAL |
| `unknown_family` | 9 | CRITICAL |

*Not all possible exceptions are covered, and the severity mapping is only indicative, since an exception by itself, without being correlated with other factors, cannot be placed into any specific category.*


**How to find DISC code**:
```
" show pfe statistics exceptions on [device]"
→ Output shows: "exception_name DISC(XX)"
```

---

## Architecture Details

### MCP Server Communication

#### Observability MCP
- **Protocol**: STDIO (VS Code) or HTTP (direct)
- **Port**: 3333 (REST API), 3334 (MCP HTTP)
- **Backend**: FastMCP + FastAPI
- **Data Source**: InfluxDB + Grafana APIs

#### Junos MCP Server
- **Protocol**: HTTP (streamable-http)
- **Port**: 30030
- **Backend**: FastMCP + Junos PyEZ + Paramiko
- **Device Access**: SSH (PyEZ for commands, Paramiko for PFE debug)

### Why Two MCP Servers?

**Separation of Concerns**:
- **Observability MCP**: Read-only monitoring and analysis
- **Junos MCP**: Direct device access and configuration changes

**Different Data Sources**:
- Observability → InfluxDB (historical metrics)
- Junos MCP → Live device state

**Security Isolation**:
- Can grant different access levels
- Observability can run without device credentials
- Junos MCP requires SSH access

---

## Project Structure

```
openntIA/
├── README.md                          This file
├── docker-compose.yaml                All services orchestration
│
├── mcp/                               Observability MCP Server
│   ├── server.py                      Main server (FastMCP)
│   ├── mcp_bridge.py                  STDIO ↔ HTTP bridge
│   ├── api.py                         REST API
│   ├── config.py                      Configuration
│   ├── tools/
│   │   ├── influx.py                  InfluxDB tools
│   │   └── grafana.py                 Grafana tools
│   └── requirements.txt
│
├── mcp-junos/                         Junos MCP Server
│   ├── Dockerfile                     Docker build
│   ├── devices.json                   Device inventory
│   ├── custom_files/
│   │   └── jmcp.py                    Main server with custom tools
│   └── utils/
│       └── config.py                  Connection utilities
│
├── collector/                         Telegraf Data Collector
│   └── data/
│       ├── pfe_exceptions.py          Collection script
│       ├── telegraf.conf              Telegraf config
│       ├── routers.yaml               Device list
│       └── credentials.yaml           SSH credentials
│
└── .vscode/
    └── settings.json                  Example MCP config
```

---

## Troubleshooting

### Junos MCP Server Issues

**Container won't start:**
```bash
# Check logs
docker logs junos-mcp-server

```

**Can't connect to devices:**
```bash
# Test SSH connectivity
ssh jncie@10.10.20.1

# Verify devices.json 
docker exec junos-mcp-server cat /app/config/devices.json

```

**PFE debug not working:**
```bash
# Verify Paramiko is installed
docker exec junos-mcp-server pip list | grep paramiko

# Test manual SSH
docker exec -it junos-mcp-server bash
python3
>>> import paramiko
>>> client = paramiko.SSHClient()
>>> client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
>>> client.connect('10.10.20.1', username='jncie', password='jncie123')
>>> stdin, stdout, stderr = client.exec_command('show version')
>>> print(stdout.read().decode())
```

*It’s possible that not all hexadecimal dumps can be decoded correctly. Check the output to ensure that both the exception number and the slot number being used are correct.*

### Tools Not Appearing in VS Code

1. **Verify both servers are running:**
   ```bash
   curl http://localhost:3333/  # Observability MCP

   curl -X POST "http://127.0.0.1:30030/mcp/" \
     -H "Authorization: Bearer your_token" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' # Junos MCP

2. **Check MCP configuration:**
   ```bash
   cat ~/.vscode/mcp-servers.json
   ```

3. **Reload VS Code completely:**
   - Close all windows
   - Reopen workspace

4. **Check Output panel:**
   - View → Output
   - Select "Model Context Protocol"

---

## Security Best Practices

### Device Credentials
- ✅ Use SSH keys instead of passwords when possible
- ✅ Store credentials in environment variables
- ✅ Use read-only accounts for monitoring
- ✅ Rotate passwords regularly

### MCP Server Access
- ✅ Don't expose ports (3333, 30030) to internet
- ✅ Use firewall rules to restrict access
- ✅ Consider adding authentication to HTTP endpoints
- ✅ Run in isolated network segment

### PFE Debug Access
- ⚠️ `pfe_debug_exceptions` requires elevated privileges
- ⚠️ Can impact device performance if overused
- ✅ Use sparingly and during maintenance windows
- ✅ Monitor device CPU/memory during debug sessions

---

## Advanced Use Cases

### 1. Automated Incident Response

```
# Detect → Investigate → Document
"Detect suspicious exceptions in the last hour, 
 then for each device:
 1. Get current exception counters
 2. Capture and decode packets
 3. Check routing tables
 4. Summarize findings"
```

### 2. Proactive Monitoring

```
# Daily health check
"Check for any suspicious exceptions in the last 24 hours,
 group by severity,
 highlight any CRITICAL or HIGH severity issues"
```

### 3. Capacity Planning

```
# Trend analysis
"Query exception rates for all devices over the last 7 days,
 identify devices with increasing trends,
 forecast when they might hit thresholds"
```

### 4. Configuration Audit

```
# After detecting firewall_discard spike
"Show me the firewall configuration on [device],
 compare with baseline configuration from last week,
 highlight any recent changes"
```

---

## Performance Considerations

### InfluxDB Query Performance
- Use time ranges (`-1h`, `-24h`) to limit data
- Aggregate data with `aggregateWindow()` for large time ranges
- Index commonly queried fields

### PFE Debug Impact
- **Duration**: Keep captures short (2-5 seconds)
- **Frequency**: Don't run continuously on production
- **Device Load**: Monitor CPU during debug sessions
- **Best Practice**: Use during maintenance windows or low-traffic periods

### MCP Server Scaling
- Each tool call is synchronous
- Long-running queries block other requests
- Consider async implementations for production
- Use connection pooling for database queries

---

## Roadmap

### Planned Features
- [ ] Multi-device correlation analysis
- [ ] Historical packet capture analysis
- [ ] Webhook notifications for critical anomalies
- [ ] AI-powered root cause analysis
- [ ] Use LSTM for anomaliy detection

---

## Quick Reference Card

### 🚀 Complete Setup (One-Time)
```bash
# 1. Start all services
docker-compose up -d

# 2. Configure devices
nano collector/data/routers.yaml
nano mcp-junos/devices.json

# 3. Configure MCP in VS Code
cat > ~/.vscode/mcp-servers.json << 'EOF'
{
  "mcpServers": {
    "observability-mcp": {
      "command": "python3",
      "args": ["/home/ubuntu/openntIA/mcp/mcp_bridge.py"],
      "env": {"MCP_SERVER_URL": "http://localhost:3333"}
    },
    "junos-mcp-server": {
      "url": "http://127.0.0.1:30030/mcp/"
    }
  }
}
EOF

# 4. Reload VS Code
```

### 🎯 Essential Commands

**Detect & Debug Workflow:**
```
1. "Detect suspicious exceptions in the last hour"
2. "Show PFE statistics on [device] slot [N]"
3. "Capture packets for [exception] DISC([code]) on [device]"
4. "Show routing table for [destination] on [device]"
```

**Device Management:**
```
"List all Juniper devices"
"Get Junos version of [device]"
"Show interface status on [device]"
"Get configuration from [device]"
```

**Monitoring:**
```
"Check for suspicious exceptions in last 6 hours"
"Query PFE exceptions for device [name]"
"List Grafana dashboards"
```

### 📊 Available Tools (11 Total)

**Observability MCP (4):**
- `check_suspicious_exceptions` - AI anomaly detection
- `query_influx` - Custom Flux queries
- `list_dashboards` - List Grafana dashboards
- `get_dashboard` - Get dashboard details

**Junos MCP (7):**
- `pfe_debug_exceptions` - Capture & decode packets 🔥
- `execute_junos_command` - Execute CLI commands
- `get_junos_config` - Retrieve configuration
- `gather_device_facts` - Get device info
- `get_router_list` - List devices
- `junos_config_diff` - Compare configs
- `load_and_commit_config` - Apply changes

### 🔗 Service URLs
- InfluxDB: http://localhost:8086 (admin/admin123)
- Grafana: http://localhost:3000 (admin/admin)
- Observability MCP: http://localhost:3333
- Junos MCP: http://localhost:30030

---

**Complete network observability and troubleshooting powered by AI** 🚀📊🤖🔧
