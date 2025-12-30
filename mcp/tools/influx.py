#!/usr/bin/env python3
"""
Herramientas MCP para InfluxDB

Proporciona funciones para consultar métricas de dispositivos de red
almacenadas en InfluxDB usando el lenguaje Flux.

Mediciones disponibles:
- interface_stats: Estadísticas de interfaces (bandwidth_util_percent, input/output bytes, errors)
- bgp_peers: Estado de peers BGP (estado, uptime, prefijos recibidos)
- system_resources: Uso de CPU, memoria, temperatura

Ejemplo de consulta Flux:
    from(bucket: "juniper")
      |> range(start: -24h)
      |> filter(fn: (r) => r["_measurement"] == "interface_stats")
      |> filter(fn: (r) => r["_field"] == "bandwidth_util_percent")
      |> mean()
"""

from influxdb_client import InfluxDBClient
from config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG


def query_influx(flux: str) -> dict:
    """
    Execute a Flux query against InfluxDB
    
    Args:
        flux: Flux query string
        
    Returns:
        dict: {"rows": [...], "count": N}
        
    Raises:
        Exception: Si hay error de conexión o en la consulta
    """
    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as client:
        tables = client.query_api().query(flux)

        rows = []
        for table in tables:
            for record in table.records:
                rows.append(record.values)

        return {
            "rows": rows,
            "count": len(rows)
        }


# MCP tool wrapper - Se registra automáticamente en el servidor MCP
try:
    from server import mcp
    
    @mcp.tool()
    def mcp_query_influx(flux: str) -> dict:
        """
        Execute a Flux query against InfluxDB to retrieve time-series metrics from network devices.
        
        Available measurements:
        - interface_stats: Interface bandwidth utilization, bytes, packets, errors
        - bgp_peers: BGP peer status, uptime, prefixes
        - system_resources: CPU, memory, temperature
        
        Example queries:
        - Top interfaces by bandwidth: 
          from(bucket: "juniper") |> range(start: -24h) 
          |> filter(fn: (r) => r._field == "bandwidth_util_percent") |> mean()
        """
        return query_influx(flux)
except ImportError:
    pass  # Skip MCP registration if not available

