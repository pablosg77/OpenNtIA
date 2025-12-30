# 🚀 Opciones de Despliegue - MCP Server

Este documento explica las diferentes formas de desplegar el proyecto.

## 📊 Comparativa Rápida

| Componente | Ubicación | ¿Obligatorio? | Propósito |
|------------|-----------|---------------|-----------|
| **InfluxDB** | Docker | ✅ Sí | Base de datos de métricas |
| **Grafana** | Docker | ✅ Sí | Visualización de dashboards |
| **MCP Server** | Local o Docker | ⚙️ Flexible | Servidor de herramientas MCP |
| **REST API** | Junto con MCP | ❌ Opcional | Testing y debugging |

---

## 🏗️ Opción 1: Híbrida (Recomendada para Desarrollo)

### Arquitectura

```
┌─────────────────────────────────────────┐
│           Host (Ubuntu)                 │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Python Local                  │   │
│  │   - mcp_bridge.py (stdio)       │   │
│  │   - server.py (FastMCP)         │   │
│  │   - api.py (REST)               │   │
│  └──────────┬──────────────────────┘   │
│             │                           │
│  ┌──────────▼──────────┐               │
│  │   Docker Network    │               │
│  │                     │               │
│  │  ┌──────────────┐   │               │
│  │  │  InfluxDB    │   │               │
│  │  │  :8086       │   │               │
│  │  └──────────────┘   │               │
│  │                     │               │
│  │  ┌──────────────┐   │               │
│  │  │  Grafana     │   │               │
│  │  │  :3000       │   │               │
│  │  └──────────────┘   │               │
│  └─────────────────────┘               │
└─────────────────────────────────────────┘
```

### Comandos

```bash
# 1. Levantar containers base
docker-compose up -d

# 2. Instalar dependencias Python
cd mcp
pip install -r requirements.txt

# 3. Configurar
cp config.example.py config.py
nano config.py

# 4. Iniciar MCP Server local
./start_servers.sh
```

### ✅ Ventajas
- Debugging fácil (logs en consola)
- Desarrollo rápido (cambios sin rebuild)
- Integración directa con IDEs
- Acceso fácil a Python debugger

### ❌ Desventajas
- Requiere Python instalado en el host
- Dependencias pueden variar por sistema
- No tan portable

---

## 🐳 Opción 2: Todo en Docker

### Arquitectura

```
┌─────────────────────────────────────────┐
│       Docker Network (bridge)           │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │   mcp-server                     │   │
│  │   - mcp_bridge.py                │   │
│  │   - server.py                    │   │
│  │   - api.py                       │   │
│  │   Ports: 3334, 8000              │   │
│  └────────┬─────────────────────────┘   │
│           │                             │
│  ┌────────▼────────┐  ┌──────────────┐  │
│  │  influxdb       │  │  grafana     │  │
│  │  :8086          │  │  :3000       │  │
│  └─────────────────┘  └──────────────┘  │
└─────────────────────────────────────────┘
```

### Comandos

```bash
# Opción 2A: Docker run manual
cd mcp
docker build -t observability-mcp:latest .
docker run -d \
  --name mcp-server \
  --network host \
  -v $(pwd)/config.py:/app/config.py:ro \
  -p 8000:8000 \
  -p 3334:3334 \
  observability-mcp:latest

# Opción 2B: Docker Compose (agregar al docker-compose.yaml)
docker-compose up -d --build
```

### ✅ Ventajas
- Despliegue consistente
- Aislamiento completo
- Fácil de replicar en otros servidores
- No requiere Python en el host

### ❌ Desventajas
- Debugging más complejo
- Rebuild necesario para cambios
- Mayor overhead de recursos
- Logs via `docker logs`

---

## 🔀 Opción 3: MCP Server Local con Containers Remotos

### Arquitectura

```
┌─────────────────┐         ┌─────────────────────┐
│  Local Machine  │         │  Remote Server      │
│                 │         │                     │
│  Python Local   │ HTTP    │  ┌──────────────┐   │
│  - mcp_bridge   ├────────▶│  │  InfluxDB    │   │
│  - server.py    │         │  │  :8086       │   │
│                 │         │  └──────────────┘   │
│                 │         │                     │
│                 │         │  ┌──────────────┐   │
│                 │         │  │  Grafana     │   │
│                 │         │  │  :3000       │   │
│                 │         │  └──────────────┘   │
└─────────────────┘         └─────────────────────┘
```

### Configuración

```python
# config.py
INFLUX_URL = "http://servidor-remoto.ejemplo.com:8086"
INFLUX_TOKEN = "token-influxdb"

GRAFANA_URL = "http://servidor-remoto.ejemplo.com:3000"
GRAFANA_TOKEN = "token-grafana"
```

### ✅ Ventajas
- InfluxDB/Grafana centralizados
- Múltiples usuarios pueden usar el mismo backend
- Escalabilidad

### ❌ Desventajas
- Latencia de red
- Requiere exponer servicios (seguridad)
- Dependencia de conectividad

---

## 🎯 ¿Cuál Elegir?

### Para Desarrollo Local
**→ Opción 1 (Híbrida)**
```bash
docker-compose up -d  # Solo InfluxDB + Grafana
cd mcp && ./start_servers.sh  # MCP local
```

### Para Producción
**→ Opción 2 (Todo Docker)**
```bash
# Agregar mcp-server al docker-compose.yaml
docker-compose up -d --build
```

### Para Equipo Distribuido
**→ Opción 3 (Containers Remotos)**
```bash
# Servidor central con InfluxDB + Grafana
# Cada desarrollador corre MCP local apuntando al servidor
```

---

## 📋 Checklist de Despliegue

### Opción 1: Híbrida ✓

- [ ] `docker-compose up -d` ejecutado
- [ ] Containers InfluxDB y Grafana corriendo
- [ ] Python 3.8+ instalado
- [ ] `pip install -r requirements.txt` completado
- [ ] `config.py` configurado con tokens
- [ ] `./start_servers.sh` ejecutado
- [ ] `curl http://localhost:8000` responde
- [ ] Claude Desktop / VS Code configurado

### Opción 2: Todo Docker ✓

- [ ] `docker-compose.yaml` actualizado con mcp-server
- [ ] `config.py` montado como volumen
- [ ] `docker-compose up -d --build` ejecutado
- [ ] Tres containers corriendo (influxdb, grafana, mcp-server)
- [ ] `docker logs mcp-server` sin errores
- [ ] `curl http://localhost:8000` responde
- [ ] Claude Desktop / VS Code configurado (apuntando al bridge)

---

## 🔧 Comandos Útiles por Opción

### Opción 1 (Híbrida)

```bash
# Ver logs del MCP Server
tail -f mcp/server.log

# Reiniciar solo MCP Server
cd mcp && ./start_servers.sh

# Reiniciar containers
docker-compose restart

# Ver estado completo
docker-compose ps && ps aux | grep python
```

### Opción 2 (Todo Docker)

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs solo del MCP Server
docker-compose logs -f mcp-server

# Reiniciar todo
docker-compose restart

# Rebuild solo MCP Server
docker-compose up -d --build mcp-server

# Entrar al container para debugging
docker exec -it mcp-server /bin/bash
```

---

## 🆘 Problemas Comunes

### "Connection refused" a InfluxDB/Grafana

**Si MCP está local**:
```bash
# Verificar que containers están corriendo
docker-compose ps

# Verificar conectividad
curl http://localhost:8086/health
```

**Si MCP está en Docker**:
```bash
# Usar nombres de servicio en vez de localhost
INFLUX_URL = "http://influxdb:8086"  # En config.py
GRAFANA_URL = "http://grafana:3000"

# O usar --network host en docker run
```

### MCP Bridge no conecta al servidor

**Verificar que el servidor está corriendo**:
```bash
# Si MCP local:
ps aux | grep server.py

# Si MCP en Docker:
docker ps | grep mcp-server

# Verificar puerto 3334 está abierto
netstat -tulpn | grep 3334
```

---

**Recomendación Final**: Empieza con la **Opción 1 (Híbrida)** para familiarizarte, luego migra a **Opción 2 (Docker)** para producción.
