"""
Simple REST API wrapper for testing MCP tools
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tools.influx import query_influx
from tools.grafana import list_dashboards, get_dashboard

app = FastAPI(title="Observability MCP API")


class FluxQuery(BaseModel):
    flux: str


@app.get("/")
def root():
    return {
        "service": "Observability MCP API",
        "version": "1.0",
        "endpoints": {
            "influx_query": "POST /influx/query",
            "list_dashboards": "GET /grafana/dashboards",
            "get_dashboard": "GET /grafana/dashboards/{uid}"
        }
    }


@app.post("/influx/query")
def api_query_influx(query: FluxQuery):
    """Execute a Flux query against InfluxDB"""
    try:
        return query_influx(query.flux)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/grafana/dashboards")
def api_list_dashboards():
    """List all Grafana dashboards"""
    try:
        return list_dashboards()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/grafana/dashboards/{uid}")
def api_get_dashboard(uid: str):
    """Get a specific Grafana dashboard by UID"""
    try:
        return get_dashboard(uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
