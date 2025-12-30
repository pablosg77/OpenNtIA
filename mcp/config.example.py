#!/usr/bin/env python3
"""
EJEMPLO DE CONFIGURACIÓN - config.py

IMPORTANTE: Copia este archivo a config.py y actualiza con tus credenciales reales.

Instrucciones:
1. cp config.example.py config.py
2. Edita config.py con tus valores reales
3. O configura variables de entorno antes de iniciar el servidor

Variables de Entorno:
    export INFLUX_URL="http://localhost:8086"
    export INFLUX_TOKEN="tu-token-influxdb-aqui"
    export INFLUX_ORG="juniper"
    export INFLUX_BUCKET="juniper"
    export GRAFANA_URL="http://localhost:3000"
    export GRAFANA_API_KEY="tu-api-key-grafana-aqui"
"""

import os

# ============================================================================
# InfluxDB Configuration
# ============================================================================
# URL del servidor InfluxDB
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")

# Token de autenticación (Settings > API Tokens en InfluxDB UI)
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "YOUR_INFLUX_TOKEN_HERE")

# Organización en InfluxDB
INFLUX_ORG = os.getenv("INFLUX_ORG", "juniper")

# Bucket donde se almacenan las métricas de red
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "juniper")

# ============================================================================
# Grafana Configuration
# ============================================================================
# URL del servidor Grafana
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")

# API Key de Grafana (Settings > API Keys > Add API key con rol Viewer)
GRAFANA_TOKEN = os.getenv("GRAFANA_TOKEN", "YOUR_GRAFANA_API_KEY_HERE")

# ============================================================================
# Cómo obtener las credenciales:
# ============================================================================
# 
# InfluxDB Token:
#   1. Abre InfluxDB UI: http://localhost:8086
#   2. Ve a Data > API Tokens
#   3. Crea un nuevo token con permisos de lectura en el bucket "juniper"
#   4. Copia el token y pégalo arriba
#
# Grafana API Key:
#   1. Abre Grafana: http://localhost:3000
#   2. Ve a Configuration > API Keys
#   3. Crea una nueva API key con rol "Viewer"
#   4. Copia la key y pégala arriba
#
# ============================================================================
