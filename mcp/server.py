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

# Import tools after server creation
# Los decoradores @mcp.tool() registran automáticamente las herramientas
import tools.influx
import tools.grafana