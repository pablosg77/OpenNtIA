# 🎨 Guía Visual de Configuración

## Para Claude Desktop

### 📍 Ubicación del Archivo de Configuración

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

### ⚙️ Contenido del Archivo

Copia exactamente este contenido:

```json
{
  "mcpServers": {
    "observability-mcp": {
      "command": "python3",
      "args": ["/home/ubuntu/openntIA/mcp/mcp_bridge.py"],
      "env": {}
    }
  }
}
```

⚠️ **IMPORTANTE**: Ajusta la ruta si tu proyecto está en otra ubicación.

### 🔄 Reiniciar Claude Desktop

1. Cierra completamente Claude Desktop (no solo minimizar)
2. Vuelve a abrir Claude Desktop
3. Haz clic en el ícono de herramientas (🔨) en la esquina inferior derecha
4. Deberías ver 3 herramientas disponibles:
   - `mcp_query_influx`
   - `mcp_list_dashboards`
   - `mcp_get_dashboard`

### ✅ Prueba de Funcionamiento

Pregunta en Claude Desktop:
```
¿Cuáles son los dashboards disponibles en Grafana?
```

Claude debería usar automáticamente la herramienta `mcp_list_dashboards`.

---

## Para VS Code + GitHub Copilot

### 📍 Ubicación del Archivo de Configuración

En la raíz de tu workspace:
```
/home/ubuntu/openntIA/.vscode/settings.json
```

Este archivo **ya está configurado** en el proyecto. No necesitas modificarlo.

### 🔌 Instalar Extensión MCP

1. Abre VS Code
2. Presiona `Ctrl+Shift+X` (Extensions)
3. Busca: **"Model Context Protocol"** o **"MCP Client"**
4. Instala la extensión
5. Recarga VS Code (`Ctrl+Shift+P` → "Developer: Reload Window")

### ⚙️ Contenido del Archivo (ya configurado)

```json
{
  "mcp.servers": {
    "observability-mcp": {
      "command": "python3",
      "args": ["/home/ubuntu/openntIA/mcp/mcp_bridge.py"],
      "cwd": "/home/ubuntu/openntIA/mcp",
      "description": "Network Observability MCP Server - InfluxDB + Grafana"
    }
  }
}
```

### ✅ Prueba de Funcionamiento

1. Abre GitHub Copilot Chat (`Ctrl+Shift+I`)
2. Pregunta:
   ```
   @workspace ¿Cuáles son las interfaces con mayor utilización en las últimas 24 horas?
   ```
3. Copilot debería usar la herramienta `mcp_query_influx`

---

## 🖥️ Iniciando el Servidor

### Terminal 1: Iniciar el Servidor MCP

```bash
cd /home/ubuntu/openntIA/mcp
./start_servers.sh
```

Deberías ver:
```
🚀 Starting Observability MCP Server...
📡 Starting REST API on port 8000...
🔧 Starting MCP Server on port 3334...
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2: (Opcional) Ver Logs en Tiempo Real

```bash
tail -f /tmp/mcp_server.log
```

### 🛑 Detener el Servidor

Presiona `Ctrl+C` en la terminal donde corre el servidor.

---

## 🔍 Verificación Pre-Vuelo

Antes de iniciar, ejecuta el script de verificación:

```bash
cd /home/ubuntu/openntIA/mcp
python3 verify_setup.py
```

### Salida Esperada:

```
============================================================
🚀 Verificación de Configuración - MCP Server
============================================================

🔍 Verificando dependencias Python...
  ✅ fastmcp
  ✅ influxdb_client
  ✅ fastapi
  ✅ uvicorn
  ✅ requests
  ✅ pydantic
✅ Todas las dependencias instaladas

🔍 Verificando configuración...
  ✅ Credenciales configuradas

🔍 Verificando conexión a InfluxDB...
  URL: http://localhost:8086
  Org: juniper
  ✅ InfluxDB accesible (version: 2.7.1)
  ✅ Mediciones disponibles: interface_stats, bgp_peers, system_resources

🔍 Verificando conexión a Grafana...
  URL: http://localhost:3000
  ✅ Grafana accesible
  ✅ Dashboards disponibles: 3
     - Network Overview (uid: network-overview)
     - BGP Monitoring (uid: bgp-mon)
     - Interface Stats (uid: interface-stats)

============================================================
✅ TODO LISTO! Puedes iniciar el servidor con:
   cd /home/ubuntu/openntIA/mcp
   ./start_servers.sh
============================================================
```

---

## 🎯 Flujo de Trabajo Completo

### 1️⃣ Primera Vez (Setup)

```bash
# Instalar dependencias
cd /home/ubuntu/openntIA/mcp
pip install -r requirements.txt

# Configurar credenciales
cp config.example.py config.py
nano config.py  # Editar con tus credenciales

# Verificar configuración
python3 verify_setup.py
```

### 2️⃣ Uso Diario

```bash
# Iniciar servidor
cd /home/ubuntu/openntIA/mcp
./start_servers.sh

# En otra terminal o usa tu cliente (Claude/VS Code)
# Ctrl+C para detener cuando termines
```

### 3️⃣ Troubleshooting

```bash
# Ver si el servidor está corriendo
ps aux | grep mcp_bridge

# Probar la API REST directamente
curl http://localhost:8000/grafana/dashboards

# Ver logs del sistema
journalctl -u mcp-server -f  # Si usas systemd

# Verificar puertos
netstat -tulpn | grep -E '8000|3334'
```

---

## 📊 Ejemplos de Consultas

### En Claude Desktop o GitHub Copilot:

**1. Listar Dashboards:**
```
Muéstrame todos los dashboards disponibles en Grafana
```

**2. Interfaces Saturadas:**
```
¿Cuáles son las interfaces con mayor utilización de ancho de banda en las últimas 24 horas?
```

**3. Estado de BGP:**
```
¿Cuántos peers BGP están activos en el dispositivo mx960-core1?
```

**4. Recursos del Sistema:**
```
Dame el uso de CPU y memoria de todos los dispositivos en la última hora
```

**5. Errores de Interfaces:**
```
¿Qué interfaces tienen más errores de entrada/salida?
```

**6. Análisis Temporal:**
```
Compara la utilización de la interfaz xe-0/0/1 entre las últimas 24 horas y la semana pasada
```

---

## 🎊 ¡Todo Listo!

Tu servidor MCP está:
- ✅ Limpio y organizado
- ✅ Completamente documentado
- ✅ Listo para Claude Desktop
- ✅ Listo para VS Code + GitHub Copilot
- ✅ Con herramientas de verificación
- ✅ Con ejemplos de uso

**¡Disfruta tu asistente de IA con contexto de red en tiempo real!** 🚀
