#!/usr/bin/env python3
"""
Herramientas MCP para InfluxDB

Proporciona funciones para consultar métricas de dispositivos de red
almacenadas en InfluxDB usando el lenguaje Flux.
"""

from influxdb_client import InfluxDBClient
from config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET, GRAFANA_URL
from typing import Dict, List
import statistics
from datetime import datetime, timedelta
from urllib.parse import urlencode


def generate_grafana_dashboard_url(device: str, exception: str, slot: str, detected_at: str, lookback_hours: int = 1, dashboard_uid: str = "ef9xzro0ybu9sd") -> str:
    """
    Generate direct Grafana dashboard URL with filters and appropriate time range
    
    Args:
        device: Device hostname
        exception: Exception type
        slot: FPC slot number
        detected_at: Timestamp when anomaly was detected
        lookback_hours: Hours to look back for visualization (default: 1)
        dashboard_uid: Dashboard UID (default: ef9xzro0ybu9sd for pfe-exceptions)
        
    Returns:
        str: Complete Grafana dashboard URL with all parameters
    """
    try:
        # Parse detected_at timestamp
        detected_time = datetime.fromisoformat(detected_at.replace('+00:00', ''))
        
        # Calculate time range - show more context (2 days back to see baseline)
        # This ensures the anomaly is visible in context
        from_time = "now-2d"  # 2 days back
        to_time = "now"
        
        # Use localhost:3000 instead of container name for browser access
        grafana_public_url = GRAFANA_URL.replace('http://grafana:', 'http://localhost:')
        
        # Build dashboard URL with all parameters
        params = {
            'orgId': '1',
            'var-device': device,
            'var-exception': exception,
            'var-slot': slot,
            'from': from_time,
            'to': to_time,
            'refresh': '10s'
        }
        
        dashboard_url = f"{grafana_public_url}/d/{dashboard_uid}/pfe-exceptions?{urlencode(params)}"
        
        return dashboard_url
        
    except Exception as e:
        # Fallback: return simple Grafana home
        grafana_public_url = GRAFANA_URL.replace('http://grafana:', 'http://localhost:')
        return f"{grafana_public_url}/"


def query_influx(flux: str) -> dict:
    """
    Execute a Flux query against InfluxDB
    
    Args:
        flux: Flux query string
        
    Returns:
        dict: {"rows": [...], "count": N}
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


def check_suspicious_exceptions(lookback_hours: int = 1, min_consecutive_samples: int = 3) -> dict:
    """
    Detect suspicious PFE exception patterns using six rules:
    
    Rule 1: New exceptions (0 to >=1pps sustained for X samples)
    Rule 2: Spike detection (comparing to 2-day baseline)
    Rule 3: Sustained increase (behavior change compared to 2-day baseline)
    Rule 4: Weekly baseline comparison (detects long-term changes)
    Rule 5: Rate of change / trend detection (detects accelerating problems)
    Rule 7: Multiple exception correlation (detects systemic issues)
    
    Args:
        lookback_hours: Hours to look back for analysis (default: 1)
        min_consecutive_samples: Minimum consecutive samples to consider suspicious (default: 3)
        
    Returns:
        dict: {
            "suspicious_exceptions": [
                {
                    "device": str,
                    "exception": str,
                    "slot": str,
                    "state": "CRITICAL|HIGH|MEDIUM|LOW",
                    "rule": "Rule 1|Rule 2|Rule 3|Rule 4|Rule 5|Rule 7",
                    "details": str
                }
            ],
            "summary": {
                "total": int,
                "critical": int,
                "high": int,
                "medium": int,
                "low": int
            }
        }
    """
    
    # Severity classification
    severity_map = {
        "egress_pfe_unspecified": "CRITICAL",
        "unknown_family": "CRITICAL",
        "sw_error": "HIGH",
        "unknown_iif": "HIGH",
        "firewall_discard": "MEDIUM",
        "discard_route": "LOW",
        "hold_route":"MEDIUM"
    }
    
    # Severity order for comparison
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    
    suspicious = []
    
    with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        query_api = client.query_api()
        
        # ===== RULE 1: New exceptions (0 to >=1pps) =====
        # derivative() calcula cambio por segundo
        # Multiplicamos por 60 para obtener cambios por minuto
        rule1_flux = f'''
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -{lookback_hours}h)
          |> filter(fn: (r) => r._measurement == "pfe_exceptions")
          |> filter(fn: (r) => r._field == "count")
          |> derivative(unit: 1s, nonNegative: true)
          |> group(columns: ["device", "slot", "exception"])
          |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
        '''
        
        tables = query_api.query(rule1_flux)
        
        # Analyze Rule 1: Group by device/slot/exception and check for sustained increase
        data_by_key = {}
        for table in tables:
            for record in table.records:
                key = (record.values.get("device"), 
                       record.values.get("slot"), 
                       record.values.get("exception"))
                value = record.values.get("_value")
                time = record.values.get("_time")
                
                # Skip if value is None or time is missing
                if value is None or time is None:
                    continue
                
                if key not in data_by_key:
                    data_by_key[key] = []
                data_by_key[key].append({
                    "time": time,
                    "value": value
                })
        
        for (device, slot, exception), samples in data_by_key.items():
            if len(samples) < min_consecutive_samples:
                continue
            
            # Sort by time
            samples.sort(key=lambda x: x["time"])
            
            # Rule 1: Check for X consecutive samples with sustained rate after starting from 0
            # Pattern: starts near zero, then X consecutive samples ALL above adaptive threshold
            # Adaptive threshold: 0.5 exc/s OR 1.0 exc/s depending on severity
            
            # Determine threshold based on severity
            # CRITICAL/HIGH exceptions: 0.5 exc/s (more sensitive)
            # MEDIUM/LOW exceptions: 0.5 exc/s (also more sensitive to catch cases like hold_route)
            adaptive_threshold = 0.5  # More sensitive threshold
            
            # Find sequences where we go from near-zero to sustained elevated rate
            for i in range(len(samples) - min_consecutive_samples):
                # Check if starting point is near zero (and not None)
                if samples[i]["value"] is not None and samples[i]["value"] < 0.1:
                    # Check next min_consecutive_samples
                    window = samples[i+1:i+1+min_consecutive_samples]
                    
                    # Filter out None values and check if ALL remaining samples >= threshold
                    valid_window = [s for s in window if s["value"] is not None]
                    if len(valid_window) < min_consecutive_samples:
                        continue  # Not enough valid samples
                    
                    all_above_threshold = all(s["value"] >= adaptive_threshold for s in valid_window)
                    
                    if all_above_threshold:
                        avg_rate = sum(s["value"] for s in valid_window) / len(valid_window)
                        # Get timestamp of first sample above threshold
                        first_above_time = valid_window[0]["time"]
                        state = severity_map.get(exception, "LOW")
                        details = f"New exception: ~0→{avg_rate:.2f} exc/s ({min_consecutive_samples} consecutive samples >= {adaptive_threshold} exc/s)"
                        
                        # Generate Grafana dashboard URL
                        grafana_url = generate_grafana_dashboard_url(device, exception, str(slot), str(first_above_time), lookback_hours)
                        
                        suspicious.append({
                            "device": device,
                            "exception": exception,
                            "slot": str(slot),
                            "state": state,
                            "rule": "Rule 1",
                            "detected_at": str(first_above_time),
                            "details": details,
                            "grafana_url": grafana_url
                        })
                        break  # Only report once per key
        
        # ===== RULE 2: Spike detection (2-day baseline) =====
        # Get baseline (older data: -48h to -lookback_hours)
        baseline_flux = f'''
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -48h, stop: -{lookback_hours}h)
          |> filter(fn: (r) => r._measurement == "pfe_exceptions")
          |> filter(fn: (r) => r._field == "count")
          |> derivative(unit: 1s, nonNegative: true)
          |> group(columns: ["device", "slot", "exception"])
          |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
        '''
        
        # Get recent data (last lookback_hours)
        recent_flux = f'''
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -{lookback_hours}h)
          |> filter(fn: (r) => r._measurement == "pfe_exceptions")
          |> filter(fn: (r) => r._field == "count")
          |> derivative(unit: 1s, nonNegative: true)
          |> group(columns: ["device", "slot", "exception"])
          |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
        '''
        
        baseline_tables = query_api.query(baseline_flux)
        recent_tables = query_api.query(recent_flux)
        
        baseline_by_key = {}
        recent_by_key = {}
        
        # Process baseline data
        for table in baseline_tables:
            for record in table.records:
                key = (record.values.get("device"), 
                       record.values.get("slot"), 
                       record.values.get("exception"))
                value = record.values.get("_value", 0)
                time = record.values.get("_time")
                
                # Skip if value is None or invalid
                if value is None:
                    continue
                
                if key not in baseline_by_key:
                    baseline_by_key[key] = []
                baseline_by_key[key].append({"value": value, "time": time})
        
        # Process recent data
        for table in recent_tables:
            for record in table.records:
                key = (record.values.get("device"), 
                       record.values.get("slot"), 
                       record.values.get("exception"))
                value = record.values.get("_value", 0)
                time = record.values.get("_time")
                
                # Skip if value is None or invalid
                if value is None:
                    continue
                
                if key not in recent_by_key:
                    recent_by_key[key] = []
                recent_by_key[key].append({"value": value, "time": time})
        
        for key in recent_by_key:
            if key not in baseline_by_key or len(baseline_by_key[key]) < 10:
                continue
            
            device, slot, exception = key
            baseline_data = baseline_by_key[key]
            recent_data = recent_by_key[key]
            
            # Extract values for statistics - filter out None values
            baseline_values = [x["value"] for x in baseline_data if x["value"] is not None]
            recent_values = [x["value"] for x in recent_data if x["value"] is not None]
            
            # Skip if no valid data
            if not baseline_values or not recent_values:
                continue
            
            baseline_mean = statistics.mean(baseline_values)
            baseline_std = statistics.stdev(baseline_values) if len(baseline_values) > 1 else 0
            recent_max = max(recent_values)
            # Get timestamp of max value
            recent_max_entry = max((x for x in recent_data if x["value"] is not None), key=lambda x: x["value"])
            recent_max_time = recent_max_entry["time"]
            
            # Spike: recent max > baseline_mean + 3*std AND at least 2x increase
            threshold = baseline_mean + (3 * baseline_std)
            if recent_max > threshold and recent_max > 0.5:  # At least 0.5 exc/s
                spike_factor = recent_max / max(baseline_mean, 0.01)  # Avoid division by zero
                if spike_factor > 2.0:  # At least 2x increase
                    state = severity_map.get(exception, "LOW")
                    details = f"Spike: {recent_max:.2f} exc/s (baseline: {baseline_mean:.2f} exc/s, {spike_factor:.1f}x)"
                    
                    # Generate Grafana dashboard URL
                    grafana_url = generate_grafana_dashboard_url(device, exception, str(slot), str(recent_max_time), lookback_hours)
                    
                    suspicious.append({
                        "device": device,
                        "exception": exception,
                        "slot": str(slot),
                        "state": state,
                        "rule": "Rule 2",
                        "detected_at": str(recent_max_time),
                        "details": details,
                        "grafana_url": grafana_url
                    })
        
        # ===== RULE 3: Sustained behavior change =====
        for key in recent_by_key:
            if key not in baseline_by_key or len(baseline_by_key[key]) < 10:
                continue
            
            device, slot, exception = key
            baseline_data = baseline_by_key[key]
            recent_data = recent_by_key[key]
            
            if len(recent_data) < min_consecutive_samples:
                continue
            
            # Extract values for statistics - filter out None values
            baseline_values = [x["value"] for x in baseline_data if x["value"] is not None]
            recent_values = [x["value"] for x in recent_data if x["value"] is not None]
            
            # Skip if no valid data
            if not baseline_values or not recent_values:
                continue
            
            baseline_mean = statistics.mean(baseline_values)
            baseline_std = statistics.stdev(baseline_values) if len(baseline_values) > 1 else 0
            recent_mean = statistics.mean(recent_values)
            recent_min = min(recent_values)
            recent_max = max(recent_values)
            
            # Skip if both baseline and recent are near zero (no meaningful change)
            if baseline_mean < 0.1 and recent_mean < 0.1:
                continue
            
            # Three conditions for sustained behavior change:
            # A) Significant increase from low baseline: recent_mean >= 1.0 exc/s AND baseline_mean < 1.0
            # B) Percentage increase: recent_mean > baseline_mean * 1.3 (30% increase)
            # C) Consistent elevation: recent_min > baseline_mean + baseline_std
            
            condition_a = recent_mean >= 1.0 and baseline_mean < 1.0
            condition_b = recent_mean > baseline_mean * 1.3 and baseline_mean >= 0.1
            condition_c = recent_min > (baseline_mean + baseline_std) and baseline_mean > 0.1
            
            if condition_a or condition_b or condition_c:
                # Check if it's sustained (not just a spike)
                # Filter out None values when counting sustained samples
                valid_recent_data = [x for x in recent_data if x["value"] is not None]
                if not valid_recent_data:
                    continue
                
                sustained_count = sum(1 for x in valid_recent_data if x["value"] > baseline_mean)
                sustained_pct = (sustained_count / len(valid_recent_data)) * 100
                
                if sustained_pct >= 70:  # At least 70% of samples above baseline
                    increase_pct = ((recent_mean - baseline_mean) / max(baseline_mean, 0.01)) * 100
                    
                    # Get timestamp of first sample above baseline (with valid value)
                    first_above = next((x for x in valid_recent_data if x["value"] > baseline_mean), valid_recent_data[0])
                    first_above_time = first_above["time"]
                    
                    # Determine which condition triggered
                    if condition_a:
                        condition_met = "new sustained high rate"
                    elif condition_c:
                        condition_met = "consistent elevation"
                    else:
                        condition_met = "significant increase"
                    
                    state = severity_map.get(exception, "LOW")
                    details = f"Sustained ({condition_met}): {recent_mean:.2f} exc/s (baseline: {baseline_mean:.2f} exc/s, +{increase_pct:.0f}%, min/max: {recent_min:.2f}/{recent_max:.2f})"
                    
                    # Generate Grafana dashboard URL
                    grafana_url = generate_grafana_dashboard_url(device, exception, str(slot), str(first_above_time), lookback_hours)
                    
                    suspicious.append({
                        "device": device,
                        "exception": exception,
                        "slot": str(slot),
                        "state": state,
                        "rule": "Rule 3",
                        "detected_at": str(first_above_time),
                        "details": details,
                        "grafana_url": grafana_url
                    })
        
        # ===== RULE 4: Weekly Baseline Comparison =====
        # Compare recent behavior vs same time last week
        # Solves the "moving baseline" problem for long-duration anomalies
        
        # Calculate total hours: 7 days (168h) + lookback_hours
        weekly_start_hours = 168 + lookback_hours
        
        weekly_baseline_flux = f'''
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -{weekly_start_hours}h, stop: -168h)
          |> filter(fn: (r) => r._measurement == "pfe_exceptions")
          |> filter(fn: (r) => r._field == "count")
          |> derivative(unit: 1s, nonNegative: true)
          |> group(columns: ["device", "slot", "exception"])
          |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
        '''
        
        weekly_baseline_tables = query_api.query(weekly_baseline_flux)
        weekly_baseline_by_key = {}
        
        # Process weekly baseline data
        for table in weekly_baseline_tables:
            for record in table.records:
                key = (record.values.get("device"), 
                       record.values.get("slot"), 
                       record.values.get("exception"))
                value = record.values.get("_value")
                time = record.values.get("_time")
                
                if value is None:
                    continue
                
                if key not in weekly_baseline_by_key:
                    weekly_baseline_by_key[key] = []
                weekly_baseline_by_key[key].append({"value": value, "time": time})
        
        # Compare recent data against weekly baseline
        for key in recent_by_key:
            if key not in weekly_baseline_by_key or len(weekly_baseline_by_key[key]) < 10:
                continue
            
            device, slot, exception = key
            weekly_baseline_data = weekly_baseline_by_key[key]
            recent_data = recent_by_key[key]
            
            # Extract values
            weekly_baseline_values = [x["value"] for x in weekly_baseline_data if x["value"] is not None]
            recent_values = [x["value"] for x in recent_data if x["value"] is not None]
            
            if not weekly_baseline_values or not recent_values:
                continue
            
            weekly_baseline_mean = statistics.mean(weekly_baseline_values)
            recent_mean = statistics.mean(recent_values)
            
            # Skip if both are near zero
            if weekly_baseline_mean < 0.1 and recent_mean < 0.1:
                continue
            
            # Trigger: 50% increase over weekly baseline
            if recent_mean > weekly_baseline_mean * 1.5 and recent_mean >= 1.0:
                increase_pct = ((recent_mean - weekly_baseline_mean) / max(weekly_baseline_mean, 0.01)) * 100
                
                # Get first sample
                first_sample = next((x for x in recent_data if x["value"] is not None), recent_data[0])
                first_time = first_sample["time"]
                
                state = severity_map.get(exception, "LOW")
                details = f"Weekly baseline deviation: {recent_mean:.2f} exc/s (week ago: {weekly_baseline_mean:.2f} exc/s, +{increase_pct:.0f}%)"
                
                grafana_url = generate_grafana_dashboard_url(device, exception, str(slot), str(first_time), lookback_hours)
                
                suspicious.append({
                    "device": device,
                    "exception": exception,
                    "slot": str(slot),
                    "state": state,
                    "rule": "Rule 4",
                    "detected_at": str(first_time),
                    "details": details,
                    "grafana_url": grafana_url
                })
        
        # ===== RULE 5: Rate of Change / Trend Detection =====
        # Detect accelerating problems (increasing trend)
        
        if lookback_hours >= 6:
            # Need at least 6 hours for trend analysis
            trend_flux = f'''
            from(bucket: "{INFLUX_BUCKET}")
              |> range(start: -{lookback_hours}h)
              |> filter(fn: (r) => r._measurement == "pfe_exceptions")
              |> filter(fn: (r) => r._field == "count")
              |> derivative(unit: 1s, nonNegative: true)
              |> group(columns: ["device", "slot", "exception"])
              |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
            '''
            
            trend_tables = query_api.query(trend_flux)
            trend_by_key = {}
            
            # Process trend data
            for table in trend_tables:
                for record in table.records:
                    key = (record.values.get("device"), 
                           record.values.get("slot"), 
                           record.values.get("exception"))
                    value = record.values.get("_value")
                    time = record.values.get("_time")
                    
                    if value is None:
                        continue
                    
                    if key not in trend_by_key:
                        trend_by_key[key] = []
                    trend_by_key[key].append({"value": value, "time": time})
            
            # Analyze trend
            for key, hourly_samples in trend_by_key.items():
                if len(hourly_samples) < 4:
                    continue
                
                # Sort by time
                hourly_samples.sort(key=lambda x: x["time"])
                
                device, slot, exception = key
                
                # Check for consistent increase (4+ consecutive hours with growth)
                increasing_count = 0
                for i in range(len(hourly_samples) - 1):
                    if hourly_samples[i+1]["value"] > hourly_samples[i]["value"]:
                        increasing_count += 1
                    else:
                        increasing_count = 0  # Reset if decrease
                
                # Trigger if 4+ consecutive hours of increase
                if increasing_count >= 4:
                    first_value = hourly_samples[0]["value"]
                    last_value = hourly_samples[-1]["value"]
                    growth_pct = ((last_value - first_value) / max(first_value, 0.01)) * 100
                    
                    # Only trigger if significant growth
                    if growth_pct > 30 and last_value >= 1.0:
                        state = severity_map.get(exception, "LOW")
                        details = f"Accelerating trend: {first_value:.2f}→{last_value:.2f} exc/s (+{growth_pct:.0f}% over {len(hourly_samples)} hours, {increasing_count+1} consecutive increases)"
                        
                        detection_time = hourly_samples[-1]["time"]
                        grafana_url = generate_grafana_dashboard_url(device, exception, str(slot), str(detection_time), lookback_hours)
                        
                        suspicious.append({
                            "device": device,
                            "exception": exception,
                            "slot": str(slot),
                            "state": state,
                            "rule": "Rule 5",
                            "detected_at": str(detection_time),
                            "details": details,
                            "grafana_url": grafana_url
                        })
        
        # ===== RULE 7: Multiple Exception Correlation =====
        # Detect when multiple different exceptions increase simultaneously on same device/slot
        
        # Group recent data by device/slot
        by_device_slot = {}
        for key, data in recent_by_key.items():
            device, slot, exception = key
            device_slot_key = (device, slot)
            
            if device_slot_key not in by_device_slot:
                by_device_slot[device_slot_key] = {}
            
            # Get recent values
            recent_values = [x["value"] for x in data if x["value"] is not None]
            if recent_values:
                recent_mean = statistics.mean(recent_values)
                by_device_slot[device_slot_key][exception] = {
                    "recent_mean": recent_mean,
                    "data": data
                }
        
        # Check each device/slot for multiple correlated exceptions
        for (device, slot), exceptions_data in by_device_slot.items():
            if len(exceptions_data) < 2:
                continue
            
            # Check how many exceptions have increased
            increased_exceptions = []
            
            for exception, exc_data in exceptions_data.items():
                # Get baseline for this exception
                key = (device, slot, exception)
                if key not in baseline_by_key or len(baseline_by_key[key]) < 10:
                    continue
                
                baseline_values = [x["value"] for x in baseline_by_key[key] if x["value"] is not None]
                if not baseline_values:
                    continue
                
                baseline_mean = statistics.mean(baseline_values)
                recent_mean = exc_data["recent_mean"]
                
                # Check if this exception increased significantly
                if recent_mean > baseline_mean * 1.3 and recent_mean >= 0.5:
                    increase_pct = ((recent_mean - baseline_mean) / max(baseline_mean, 0.01)) * 100
                    increased_exceptions.append({
                        "exception": exception,
                        "recent": recent_mean,
                        "baseline": baseline_mean,
                        "increase_pct": increase_pct,
                        "data": exc_data["data"]
                    })
            
            # Trigger if 2+ exceptions increased simultaneously
            if len(increased_exceptions) >= 2:
                # Get highest severity
                max_severity = "LOW"
                for exc in increased_exceptions:
                    exc_severity = severity_map.get(exc["exception"], "LOW")
                    if severity_order.get(exc_severity, 4) < severity_order.get(max_severity, 4):
                        max_severity = exc_severity
                
                # Build details string
                exc_details = ", ".join([
                    f"{e['exception']}:+{e['increase_pct']:.0f}%" 
                    for e in increased_exceptions
                ])
                
                # Use timestamp from first exception
                first_exc_data = increased_exceptions[0]["data"]
                first_sample = next((x for x in first_exc_data if x["value"] is not None), first_exc_data[0])
                detection_time = first_sample["time"]
                
                # Use primary exception for Grafana URL
                primary_exception = increased_exceptions[0]["exception"]
                
                details = f"Multiple correlated exceptions ({len(increased_exceptions)}): {exc_details}"
                grafana_url = generate_grafana_dashboard_url(device, primary_exception, str(slot), str(detection_time), lookback_hours)
                
                suspicious.append({
                    "device": device,
                    "exception": f"multiple_correlated",
                    "slot": str(slot),
                    "state": max_severity,
                    "rule": "Rule 7",
                    "detected_at": str(detection_time),
                    "details": details,
                    "grafana_url": grafana_url
                })
    
    # Remove duplicates (same device/slot/exception might trigger multiple rules)
    seen = set()
    unique_suspicious = []
    for item in suspicious:
        key = (item["device"], item["exception"], item["slot"])
        if key not in seen:
            seen.add(key)
            unique_suspicious.append(item)
    
    # Sort by severity
    unique_suspicious.sort(key=lambda x: severity_order.get(x["state"], 4))
    
    # Summary
    summary = {
        "total": len(unique_suspicious),
        "critical": sum(1 for x in unique_suspicious if x["state"] == "CRITICAL"),
        "high": sum(1 for x in unique_suspicious if x["state"] == "HIGH"),
        "medium": sum(1 for x in unique_suspicious if x["state"] == "MEDIUM"),
        "low": sum(1 for x in unique_suspicious if x["state"] == "LOW")
    }
    
    return {
        "suspicious_exceptions": unique_suspicious,
        "summary": summary
    }


# MCP tool wrappers - Se registran automáticamente en el servidor MCP
# Estas funciones se importan en server.py después de crear la instancia mcp
def register_tools(mcp):
    """Register all InfluxDB tools with the MCP server"""
    
    @mcp.tool()
    def mcp_query_influx(flux: str) -> dict:
        """
        Execute a Flux query against InfluxDB to retrieve time-series metrics from network devices.
        
        Available measurements:
        - pfe_exceptions: PFE exception counters per device/slot
        
        Example queries:
        - Top devices by exception rate: 
          from(bucket: "juniper") |> range(start: -24h) 
          |> filter(fn: (r) => r._measurement == "pfe_exceptions")
          |> derivative(unit: 1s, nonNegative: true)
        """
        return query_influx(flux)
    
    @mcp.tool()
    def mcp_check_suspicious_exceptions(lookback_hours: int = 1, min_consecutive_samples: int = 3) -> dict:
        """
        Detect suspicious PFE exception patterns using intelligent analysis.
        
        Analyzes six types of anomalies:
        - Rule 1: New exceptions appearing (0 to >=1pps sustained)
        - Rule 2: Spike detection (comparing to 2-day historical baseline)
        - Rule 3: Sustained behavior change (gradual increase over baseline)
        - Rule 4: Weekly baseline comparison (detects long-term changes)
        - Rule 5: Rate of change / trend detection (detects accelerating problems)
        - Rule 7: Multiple exception correlation (detects systemic issues)
        
        Severity levels:
        - CRITICAL: egress_pfe_unspecified, unknown_family
        - HIGH: sw_error, unknown_iif
        - MEDIUM: firewall_discard
        - LOW: discard_route
        
        Args:
            lookback_hours: Hours to analyze (default: 1, minimum 6 for Rule 5)
            min_consecutive_samples: Minimum samples to confirm anomaly (default: 3)
            
        Returns:
            Table with: device, exception, slot, state, rule, detected_at, details, grafana_url
        """
        return check_suspicious_exceptions(lookback_hours, min_consecutive_samples)

