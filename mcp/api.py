"""
Simple REST API wrapper for testing MCP tools
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tools.influx import query_influx, check_suspicious_exceptions
from tools.grafana import list_dashboards, get_dashboard

app = FastAPI(title="Observability MCP API")


class FluxQuery(BaseModel):
    flux: str


class SuspiciousExceptionsParams(BaseModel):
    lookback_hours: int = 1
    min_consecutive_samples: int = 3
    use_ml: bool = True
    ml_confidence_threshold: float = 0.65
    use_dynamic_baseline: bool = True  # ✅ ENABLED: Dynamic baseline with multi-window analysis 


@app.get("/")
def root():
    return {
        "service": "Observability MCP API",
        "version": "1.0",
        "endpoints": {
            "influx_query": "POST /influx/query",
            "check_suspicious": "POST /influx/check_suspicious",
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


@app.post("/influx/check_suspicious")
def api_check_suspicious_exceptions(params: SuspiciousExceptionsParams = None):
    """
    Check for suspicious PFE exception patterns
    
    Uses 7 detection rules including ML-based detection (Rule 8):
    - Rule 1: New exceptions (0 to >=1pps sustained)
    - Rule 2: Spike detection vs 2-day baseline
    - Rule 3: Sustained behavior change
    - Rule 4: Weekly baseline comparison
    - Rule 5: Rate of change / trend detection
    - Rule 7: Multiple exception correlation
    - Rule 8: ML-based detection (Isolation Forest)
    """
    try:
        if params is None:
            params = SuspiciousExceptionsParams()
        return check_suspicious_exceptions(
            lookback_hours=params.lookback_hours,
            min_consecutive_samples=params.min_consecutive_samples,
            use_ml=params.use_ml,
            ml_confidence_threshold=params.ml_confidence_threshold,
            use_dynamic_baseline=params.use_dynamic_baseline
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/influx/debug/{device}/{slot}/{exception}")
def api_debug_exception(device: str, slot: str, exception: str, lookback_hours: int = 1):
    """
    Debug endpoint: Show baseline vs recent data for a specific exception
    """
    from tools.influx import query_influx
    from datetime import datetime, timedelta, timezone
    import statistics
    
    try:
        # Query 48h of data
        flux = f'''
        from(bucket: "juniper")
          |> range(start: -48h)
          |> filter(fn: (r) => r._measurement == "pfe_exceptions")
          |> filter(fn: (r) => r._field == "count")
          |> filter(fn: (r) => r.device == "{device}")
          |> filter(fn: (r) => r.slot == "{slot}")
          |> filter(fn: (r) => r.exception == "{exception}")
          |> derivative(unit: 1s, nonNegative: true)
          |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
        '''
        
        result = query_influx(flux)
        
        # Split into baseline and recent
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        baseline = []
        recent = []
        
        for row in result["rows"]:
            time = row.get("_time")
            value = row.get("_value", 0)
            
            if time < cutoff:
                baseline.append({"time": str(time), "value": value})
            else:
                recent.append({"time": str(time), "value": value})
        
        baseline_values = [x["value"] for x in baseline]
        recent_values = [x["value"] for x in recent]
        
        return {
            "device": device,
            "slot": slot,
            "exception": exception,
            "lookback_hours": lookback_hours,
            "cutoff_time": str(cutoff),
            "baseline": {
                "samples": len(baseline_values),
                "mean": statistics.mean(baseline_values) if baseline_values else 0,
                "std": statistics.stdev(baseline_values) if len(baseline_values) > 1 else 0,
                "min": min(baseline_values) if baseline_values else 0,
                "max": max(baseline_values) if baseline_values else 0,
                "data": baseline
            },
            "recent": {
                "samples": len(recent_values),
                "mean": statistics.mean(recent_values) if recent_values else 0,
                "std": statistics.stdev(recent_values) if len(recent_values) > 1 else 0,
                "min": min(recent_values) if recent_values else 0,
                "max": max(recent_values) if recent_values else 0,
                "data": recent
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
