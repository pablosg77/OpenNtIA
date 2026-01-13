#!/usr/bin/env python3
"""
Herramientas MCP para Grafana

Proporciona funciones para interactuar con la API de Grafana:
- Listar dashboards disponibles
- Obtener detalles de un dashboard específico
- Consultar paneles y queries

Uso típico:
1. list_dashboards() para ver qué dashboards están disponibles
2. get_dashboard(uid) para obtener la configuración completa de un dashboard
"""

import requests
from config import GRAFANA_URL, GRAFANA_TOKEN

HEADERS = {
    "Authorization": f"Bearer {GRAFANA_TOKEN}",
    "Content-Type": "application/json"
}


def list_dashboards() -> dict:
    """
    List all Grafana dashboards
    
    Returns:
        list[dict]: Lista de dashboards con uid, title, uri, url, etc.
    """
    r = requests.get(
        f"{GRAFANA_URL}/api/search",
        headers=HEADERS
    )
    r.raise_for_status()
    return r.json()


def get_dashboard(uid: str) -> dict:
    """
    Get a specific Grafana dashboard by UID
    
    Args:
        uid: Dashboard UID (e.g., "network-overview")
        
    Returns:
        dict: Dashboard completo con panels, queries, variables, etc.
    """
    r = requests.get(
        f"{GRAFANA_URL}/api/dashboards/uid/{uid}",
        headers=HEADERS
    )
    r.raise_for_status()
    return r.json()


# MCP tool wrappers - Se registran automáticamente en el servidor MCP
# Estas funciones se importan en server.py después de crear la instancia mcp
def register_tools(mcp):
    """Register all Grafana tools with the MCP server"""
    
    @mcp.tool()
    def mcp_list_dashboards() -> dict:
        """
        List all available Grafana dashboards.
        
        Returns a list of dashboards with their UID, title, URI, and URL.
        Use the UID to get detailed information about a specific dashboard.
        """
        return list_dashboards()
    
    @mcp.tool()
    def mcp_get_dashboard(uid: str) -> dict:
        """
        Get details of a specific Grafana dashboard by its UID.
        
        Args:
            uid: The unique identifier of the dashboard (from list_dashboards)
            
        Returns the complete dashboard configuration including panels, queries,
        variables, and visualization settings.
        """
        return get_dashboard(uid)

