# 🚀 Guía Rápida de Inicio - MCP Server

## ⚡ Inicio Rápido (5 minutos)

### 1️⃣ Levantar Servicios Base (InfluxDB + Grafana)
```bash
cd /home/ubuntu/openntIA
docker-compose up -d
```

Esto levanta los **containers obligatorios**:
- ✅ InfluxDB en http://localhost:8086
- ✅ Grafana en http://localhost:3000

### 2️⃣ Configurar Credenciales
```bash
cd mcp
cp config.example.py config.py
nano config.py  # Edita los tokens de InfluxDB y Grafana
```

### 3️⃣ Iniciar MCP Server (Local)
```bash
pip install -r requirements.txt
./start_servers.sh
```

### 4️⃣ Verificar
```bash
curl http://localhost:8000/grafana/dashboards
```

---

### 2. Configura Claude Desktop

Edita: `~/.config/Claude/claude_desktop_config.json` (Linux)

```json
{
  "mcpServers": {
    "observability-mcp": {
      "command": "python3",
      "args": ["/home/ubuntu/openntIA/mcp/mcp_bridge.py"]
    }
  }
}
```

### 3. Reinicia Claude Desktop y listo! 🎉

---

## Para VS Code + GitHub Copilot

### 1. Inicia el servidor MCP
```bash
cd /home/ubuntu/openntIA/mcp
./start_servers.sh
```

### 2. Configura VS Code

Crea/edita: `/home/ubuntu/openntIA/.vscode/settings.json`

```json
{
  "mcp.servers": {
    "observability-mcp": {
      "command": "python3",
      "args": ["/home/ubuntu/openntIA/mcp/mcp_bridge.py"],
      "cwd": "/home/ubuntu/openntIA/mcp"
    }
  }
}
```

### 3. Recarga VS Code (Ctrl+Shift+P → "Reload Window") 🎉

---

## Verificación Rápida

```bash
# Ver si el servidor está corriendo
ps aux | grep mcp

# Probar la API REST
curl http://localhost:8000/grafana/dashboards

# Ver logs
tail -f /tmp/mcp_server.log
```

---

## Ejemplos de Preguntas para la IA

✅ "¿Cuáles son las interfaces con mayor utilización en las últimas 24 horas?"
✅ "Muéstrame todos los dashboards de Grafana"
✅ "¿Cuántos peers BGP están activos?"
✅ "Dame el uso de CPU de todos los dispositivos"

---

## ⚠️ Troubleshooting Rápido

**No funciona en Claude Desktop**
→ Verifica la ruta en `claude_desktop_config.json`
→ Reinicia Claude Desktop

**No funciona en VS Code**
→ Instala la extensión "Model Context Protocol"
→ Recarga la ventana (Ctrl+Shift+P)

**Errores de conexión**
→ Verifica que InfluxDB y Grafana están corriendo
→ Revisa `mcp/config.py`
