#!/usr/bin/env python3
"""
MCP Bridge: stdio <-> HTTP REST
This bridge allows Cline (which uses stdio) to communicate with our HTTP-based MCP server
"""

import sys
import json
import requests
from typing import Dict, Any

MCP_SERVER_URL = 'http://localhost:3333'

def log(message: str):
    """Log to stderr so it doesn't interfere with JSON-RPC on stdout"""
    print(f"[MCP Bridge] {message}", file=sys.stderr)

def call_tool(tool_name: str, args: Dict[str, Any]) -> Any:
    """Call a tool via the REST API"""
    try:
        if tool_name in ['query_influx', 'mcp_query_influx']:
            response = requests.post(
                f'{MCP_SERVER_URL}/influx/query',
                json={'flux': args.get('flux', '')},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        elif tool_name in ['check_suspicious_exceptions', 'mcp_check_suspicious_exceptions']:
            response = requests.post(
                f'{MCP_SERVER_URL}/influx/check_suspicious',
                json={
                    'lookback_hours': args.get('lookback_hours', 1),
                    'min_consecutive_samples': args.get('min_consecutive_samples', 3)
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        
        elif tool_name in ['list_dashboards', 'mcp_list_dashboards']:
            response = requests.get(
                f'{MCP_SERVER_URL}/grafana/dashboards',
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        elif tool_name in ['get_dashboard', 'mcp_get_dashboard']:
            uid = args.get('uid', '')
            response = requests.get(
                f'{MCP_SERVER_URL}/grafana/dashboards/{uid}',
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP request failed: {str(e)}")

def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle a JSON-RPC request"""
    method = request.get('method')
    request_id = request.get('id')
    
    log(f"Request: {method}")
    
    if method == 'initialize':
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'protocolVersion': '2024-11-05',
                'capabilities': {
                    'tools': {}
                },
                'serverInfo': {
                    'name': 'observability-mcp',
                    'version': '1.0.0'
                }
            }
        }
    
    elif method == 'tools/list':
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'tools': [
                    {
                        'name': 'query_influx',
                        'description': 'Execute a Flux query against InfluxDB to retrieve time-series metrics from network devices (interfaces, BGP, system resources)',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'flux': {
                                    'type': 'string',
                                    'description': 'Flux query string to execute against the juniper bucket'
                                }
                            },
                            'required': ['flux']
                        }
                    },
                    {
                        'name': 'check_suspicious_exceptions',
                        'description': 'Detect suspicious PFE exception patterns using 3 rules: (1) New exceptions 0→>=1 exc/s sustained, (2) Spike vs 2-day baseline, (3) Sustained behavior change. Returns table with device, exception, slot, state (CRITICAL/HIGH/MEDIUM/LOW), rule, detected_at timestamp, and details.',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'lookback_hours': {
                                    'type': 'integer',
                                    'description': 'Hours to analyze for recent period (default: 1)',
                                    'default': 1
                                },
                                'min_consecutive_samples': {
                                    'type': 'integer',
                                    'description': 'Minimum consecutive samples to confirm anomaly (default: 3)',
                                    'default': 3
                                }
                            }
                        }
                    },
                    {
                        'name': 'list_dashboards',
                        'description': 'List all available Grafana dashboards',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {}
                        }
                    },
                    {
                        'name': 'get_dashboard',
                        'description': 'Get details of a specific Grafana dashboard by its UID',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'uid': {
                                    'type': 'string',
                                    'description': 'The unique identifier (UID) of the dashboard'
                                }
                            },
                            'required': ['uid']
                        }
                    }
                ]
            }
        }
    
    elif method == 'tools/call':
        try:
            params = request.get('params', {})
            tool_name = params.get('name')
            tool_args = params.get('arguments', {})
            
            log(f"Calling tool: {tool_name}")
            result = call_tool(tool_name, tool_args)
            
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        
        except Exception as e:
            log(f"Tool call error: {str(e)}")
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32000,
                    'message': str(e)
                }
            }
    
    else:
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': -32601,
                'message': f'Method not found: {method}'
            }
        }

def main():
    """Main loop: read JSON-RPC requests from stdin, write responses to stdout"""
    log(f"MCP Bridge started, connecting to {MCP_SERVER_URL}")
    
    # Read line by line from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            response = handle_request(request)
            
            # Write response to stdout
            print(json.dumps(response), flush=True)
        
        except json.JSONDecodeError as e:
            log(f"JSON decode error: {e}")
            error_response = {
                'jsonrpc': '2.0',
                'id': None,
                'error': {
                    'code': -32700,
                    'message': 'Parse error',
                    'data': str(e)
                }
            }
            print(json.dumps(error_response), flush=True)
        
        except Exception as e:
            log(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()
