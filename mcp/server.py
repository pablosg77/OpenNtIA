#!/usr/bin/env python3
"""
MCP Server para Observabilidad de Red Juniper

Este servidor proporciona herramientas MCP para consultar:
- Métricas de InfluxDB (interfaces, BGP, recursos del sistema)
- Dashboards de Grafana

Uso:
    fastmcp run server.py --host 0.0.0.0 --port 3334
"""

from mcp.server.fastmcp import FastMCP

# Create FastMCP server instance
mcp = FastMCP("observability-mcp")

# Import and register tools
import tools.influx
import tools.grafana

# Register all tools with the mcp instance
tools.influx.register_tools(mcp)
tools.grafana.register_tools(mcp)