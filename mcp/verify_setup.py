#!/usr/bin/env python3
"""
Script de Verificación de Configuración

Verifica que:
1. Todas las dependencias están instaladas
2. InfluxDB es accesible
3. Grafana es accesible
4. Las credenciales son correctas
"""

import sys
import importlib

def check_dependencies():
    """Verificar que todas las dependencias están instaladas"""
    print("🔍 Verificando dependencias Python...")
    
    required = [
        'fastmcp',
        'influxdb_client',
        'fastapi',
        'uvicorn',
        'requests',
        'pydantic'
    ]
    
    missing = []
    for package in required:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Faltan dependencias. Instala con:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("✅ Todas las dependencias instaladas\n")
    return True


def check_influxdb():
    """Verificar conexión a InfluxDB"""
    print("🔍 Verificando conexión a InfluxDB...")
    
    try:
        from config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG
        from influxdb_client import InfluxDBClient
        
        print(f"  URL: {INFLUX_URL}")
        print(f"  Org: {INFLUX_ORG}")
        
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            # Verificar health
            health = client.health()
            if health.status == "pass":
                print(f"  ✅ InfluxDB accesible (version: {health.version})")
                
                # Probar query simple
                query = 'import "influxdata/influxdb/schema"\nschema.measurements(bucket: "juniper")'
                tables = client.query_api().query(query)
                measurements = [record.values.get("_value") for table in tables for record in table.records]
                
                if measurements:
                    print(f"  ✅ Mediciones disponibles: {', '.join(measurements)}")
                else:
                    print(f"  ⚠️  El bucket 'juniper' no tiene datos")
                
                return True
            else:
                print(f"  ❌ InfluxDB no está saludable: {health.message}")
                return False
                
    except Exception as e:
        print(f"  ❌ Error conectando a InfluxDB: {e}")
        return False


def check_grafana():
    """Verificar conexión a Grafana"""
    print("\n🔍 Verificando conexión a Grafana...")
    
    try:
        from config import GRAFANA_URL, GRAFANA_TOKEN
        import requests
        
        print(f"  URL: {GRAFANA_URL}")
        
        headers = {
            "Authorization": f"Bearer {GRAFANA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Verificar health
        r = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
        r.raise_for_status()
        print(f"  ✅ Grafana accesible")
        
        # Listar dashboards
        r = requests.get(f"{GRAFANA_URL}/api/search", headers=headers, timeout=5)
        r.raise_for_status()
        dashboards = r.json()
        
        if dashboards:
            print(f"  ✅ Dashboards disponibles: {len(dashboards)}")
            for dash in dashboards[:3]:
                print(f"     - {dash.get('title')} (uid: {dash.get('uid')})")
        else:
            print(f"  ⚠️  No hay dashboards configurados")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error conectando a Grafana: {e}")
        return False


def check_config():
    """Verificar que config.py existe y tiene credenciales"""
    print("🔍 Verificando configuración...")
    
    try:
        from config import INFLUX_TOKEN, GRAFANA_TOKEN
        
        if "YOUR_" in INFLUX_TOKEN or not INFLUX_TOKEN:
            print("  ❌ INFLUX_TOKEN no está configurado")
            return False
        
        if "YOUR_" in str(GRAFANA_TOKEN) or not GRAFANA_TOKEN:
            print("  ❌ GRAFANA_TOKEN no está configurado")
            return False
        
        print("  ✅ Credenciales configuradas")
        return True
        
    except ImportError:
        print("  ❌ No se encuentra config.py")
        print("     Copia config.example.py a config.py y configura las credenciales")
        return False


def main():
    print("=" * 60)
    print("🚀 Verificación de Configuración - MCP Server")
    print("=" * 60)
    print()
    
    checks = [
        ("Dependencias", check_dependencies),
        ("Configuración", check_config),
        ("InfluxDB", check_influxdb),
        ("Grafana", check_grafana),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            results.append(check_func())
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            results.append(False)
        print()
    
    print("=" * 60)
    if all(results):
        print("✅ TODO LISTO! Puedes iniciar el servidor con:")
        print("   cd /home/ubuntu/openntIA/mcp")
        print("   ./start_servers.sh")
    else:
        print("❌ Hay problemas de configuración. Revisa los errores arriba.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
