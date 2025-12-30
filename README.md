# Observability MCP Server

Servidor MCP (Model Context Protocol) para observabilidad de red Juniper con integración de InfluxDB y Grafana.

## 📋 Descripción

Este proyecto proporciona un servidor MCP que permite a asistentes de IA (Claude Desktop, GitHub Copilot) consultar métricas de red almacenadas en InfluxDB y gestionar dashboards de Grafana.

### Herramientas Disponibles

- **query_influx**: Ejecuta consultas Flux contra InfluxDB para obtener métricas de dispositivos de red
- **list_dashboards**: Lista todos los dashboards disponibles en Grafana
- **get_dashboard**: Obtiene detalles de un dashboard específico por su UID

## 🏗️ Arquitectura

```
┌─────────────────┐
│  Claude Desktop │
│  GitHub Copilot │
└────────┬────────┘
         │ stdio (MCP Protocol)
         ▼
┌─────────────────┐
│  mcp_bridge.py  │  (Adaptador stdio ↔ HTTP)
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│   FastMCP       │  (MCP Server + REST API)
│   server.py     │  [Puede ser local o container]
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌─────────┐
│ InfluxDB│ │ Grafana │  [Siempre en Docker]
│ :8086   │ │ :3000   │
└─────────┘ └─────────┘
   Docker      Docker
```

### 🐳 Arquitectura de Contenedores

Este proyecto usa una arquitectura **híbrida**:

**Componentes en Docker (Obligatorio):**
- **InfluxDB** (puerto 8086) - Base de datos de métricas time-series
- **Grafana** (puerto 3000) - Visualización de dashboards

**MCP Server (Flexible):**
- **Opción 1**: Ejecutar localmente (Python nativo) - Recomendado para desarrollo
- **Opción 2**: Ejecutar en Docker - Recomendado para producción

### ¿Por qué esta arquitectura?

✅ **InfluxDB y Grafana en Docker**: 
- Aislamiento y fácil gestión
- Persistencia de datos con volúmenes
- Configuración reproducible
- Actualizaciones sencillas

⚙️ **MCP Server flexible**:
- **Local**: Desarrollo rápido, debugging fácil, integración directa con IDEs
- **Docker**: Producción, despliegue consistente, aislamiento

## 📁 Estructura del Proyecto

```
openntIA/
├── README.md                          # Este archivo
├── docker-compose.yaml                # Configuración de Docker
├── mcp/
│   ├── server.py                      # Servidor MCP principal (FastMCP)
│   ├── mcp_bridge.py                  # Bridge stdio ↔ HTTP
│   ├── config.py                      # Configuración (InfluxDB, Grafana)
│   ├── requirements.txt               # Dependencias Python
│   ├── start_servers.sh               # Script de inicio
│   ├── Dockerfile                     # (Opcional) Para containerizar
│   ├── verify_setup.py                # Script de verificación
│   └── tools/
│       ├── __init__.py
│       ├── influx.py                  # Herramientas de InfluxDB
│       └── grafana.py                 # Herramientas de Grafana
├── claude_desktop_config.json         # Configuración para Claude Desktop
└── .vscode/
    └── settings.json                  # Configuración para VS Code + Copilot
```

## 🚀 Instalación y Despliegue

### Paso 1: Levantar Servicios Base (InfluxDB + Grafana)

Estos servicios **siempre** corren en Docker:

```bash
cd /home/ubuntu/openntIA
docker-compose up -d
```

Esto levantará:
- **InfluxDB** en `http://localhost:8086`
- **Grafana** en `http://localhost:3000`

Verifica que están corriendo:

```bash
docker-compose ps

# Debería mostrar:
# influxdb2  - Up - 0.0.0.0:8086->8086/tcp
# grafana    - Up - 0.0.0.0:3000->3000/tcp
```

Accede a Grafana:
- URL: http://localhost:3000
- Usuario: `admin`
- Contraseña: `admin123`

### Paso 2: Configurar Credenciales

Copia el archivo de ejemplo y edita con tus credenciales:

```bash
cd /home/ubuntu/openntIA/mcp
cp config.example.py config.py
nano config.py  # o usa tu editor preferido
```

Actualiza las siguientes variables en `config.py`:

```python
# InfluxDB (Docker container)
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "tu-token-de-influxdb"  # Obtenerlo de InfluxDB UI
INFLUX_ORG = "juniper"
INFLUX_BUCKET = "juniper"

# Grafana (Docker container)
GRAFANA_URL = "http://localhost:3000"
GRAFANA_TOKEN = "tu-api-key-de-grafana"  # Crear en Grafana UI
```

**Cómo obtener los tokens:**

1. **Token de InfluxDB**:
   - Ve a http://localhost:8086
   - Login con las credenciales del `docker-compose.yaml`
   - Data → API Tokens → Generate API Token

2. **Token de Grafana**:
   - Ve a http://localhost:3000
   - Configuration → API Keys → New API Key
   - Role: Admin

### Paso 3: Elegir Modo de Despliegue del MCP Server

Tienes **dos opciones**:

---

## 🐍 Opción A: MCP Server Local (Python Nativo)

**Recomendado para**: Desarrollo, debugging, uso con IDEs (VS Code, Claude Desktop)

### A1. Instalar Dependencias

```bash
cd /home/ubuntu/openntIA/mcp
pip install -r requirements.txt
```

### A2. Verificar Configuración

```bash
python3 verify_setup.py
```

Este script verificará:
- ✅ Dependencias Python instaladas
- ✅ Credenciales configuradas
- ✅ Conexión a InfluxDB
- ✅ Conexión a Grafana
- ✅ Disponibilidad de datos

### A3. Iniciar el Servidor

```bash
chmod +x start_servers.sh
./start_servers.sh
```

Esto iniciará:
- **FastMCP Server** en puerto `3334` (protocolo MCP)
- **REST API** en puerto `8000` (para testing)

### A4. Verificar que Funciona

```bash
# Listar dashboards
curl http://localhost:8000/grafana/dashboards

# Consultar InfluxDB
curl -X POST http://localhost:8000/influx/query \
  -H "Content-Type: application/json" \
  -d '{"flux": "from(bucket: \"juniper\") |> range(start: -1h) |> limit(n: 5)"}'
```

---

## 🐳 Opción B: MCP Server en Docker

**Recomendado para**: Producción, despliegue en servidores, entornos aislados

### B1. Construir la Imagen

```bash
cd /home/ubuntu/openntIA/mcp
docker build -t observability-mcp:latest .
```

### B2. Ejecutar el Container

```bash
docker run -d \
  --name mcp-server \
  --network host \
  -v $(pwd)/config.py:/app/config.py:ro \
  -p 8000:8000 \
  -p 3334:3334 \
  observability-mcp:latest
```

**Nota**: Usamos `--network host` para que el container pueda acceder a InfluxDB y Grafana en localhost.

### B3. Ver Logs

```bash
docker logs -f mcp-server
```

### B4. Detener el Container

```bash
docker stop mcp-server
docker rm mcp-server
```

---

## 🔄 Opción C: Todo en Docker Compose (Completo)

Para un despliegue todo-en-uno, actualiza el `docker-compose.yaml`:

```yaml
version: '3.8'

services:
  influxdb:
    # ... configuración existente ...

  grafana:
    # ... configuración existente ...

  mcp-server:
    build: ./mcp
    container_name: mcp-server
    ports:
      - "8000:8000"
      - "3334:3334"
    volumes:
      - ./mcp/config.py:/app/config.py:ro
    environment:
      - INFLUX_URL=http://influxdb:8086
      - GRAFANA_URL=http://grafana:3000
    depends_on:
      - influxdb
      - grafana
    networks:
      - observability-net

networks:
  observability-net:
    driver: bridge
```

Luego ejecuta:

```bash
docker-compose up -d --build
```

---

## 📊 Resumen de Puertos

| Servicio | Puerto | Descripción | Ubicación |
|----------|--------|-------------|-----------|
| **InfluxDB** | 8086 | Base de datos de métricas | Docker (obligatorio) |
| **Grafana** | 3000 | Dashboards y visualización | Docker (obligatorio) |
| **REST API** | 8000 | API de testing (opcional) | Local o Docker |
| **MCP Server** | 3334 | Servidor MCP HTTP/SSE | Local o Docker |

### 2.1. Verificar Configuración

Antes de iniciar el servidor, verifica que todo está correctamente configurado:

```bash
cd /home/ubuntu/openntIA/mcp
python3 verify_setup.py
```

Este script verificará:
- ✅ Dependencias Python instaladas
- ✅ Credenciales configuradas
- ✅ Conexión a InfluxDB
- ✅ Conexión a Grafana
- ✅ Disponibilidad de datos

### 3. Iniciar el Servidor

```bash
cd /home/ubuntu/openntIA/mcp
chmod +x start_servers.sh
./start_servers.sh
```

Esto iniciará:
- **FastMCP Server** en puerto `3334` (protocolo MCP)
- **REST API** en puerto `8000` (para testing)

### 4. Verificar que el Servidor Funciona

Prueba la API REST:

```bash
# Listar dashboards
curl http://localhost:8000/grafana/dashboards

# Consultar InfluxDB
curl -X POST http://localhost:8000/influx/query \
  -H "Content-Type: application/json" \
  -d '{"flux": "from(bucket: \"juniper\") |> range(start: -1h) |> limit(n: 5)"}'
```

## 🔧 Configuración de Clientes

### Opción 1: Claude Desktop

1. **Edita la configuración de Claude Desktop:**

   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Agrega la siguiente configuración:**

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

3. **Reinicia Claude Desktop**

4. **Verifica que funciona:**
   - Abre Claude Desktop
   - Haz clic en el ícono de herramientas (🔨)
   - Deberías ver las 3 herramientas: `query_influx`, `list_dashboards`, `get_dashboard`

### Opción 2: Visual Studio Code + GitHub Copilot

1. **Instala la extensión MCP:**
   - Abre VS Code
   - Ve a Extensions (Ctrl+Shift+X)
   - Busca e instala: **"Model Context Protocol"** o **"MCP Client"**

2. **Configura VS Code:**

Crea/edita `.vscode/settings.json` en la raíz del proyecto:

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

3. **Recarga VS Code:**
   - Presiona `Ctrl+Shift+P`
   - Ejecuta: `Developer: Reload Window`

4. **Verifica que funciona:**
   - Abre GitHub Copilot Chat
   - Pregunta: "¿Cuáles son los dashboards disponibles en Grafana?"
   - Copilot debería usar la herramienta `list_dashboards`

## 📊 Ejemplos de Uso

### Consultar Interfaces con Mayor Utilización

```
¿Cuáles son las interfaces con mayor utilización de ancho de banda en las últimas 24 horas?
```

### Listar Dashboards

```
Muéstrame todos los dashboards disponibles en Grafana
```

### Consultar Métricas de BGP

```
¿Cuántos peers BGP están activos en el dispositivo mx960-core1?
```

### Analizar Recursos del Sistema

```
Muéstrame el uso de CPU y memoria de todos los dispositivos en la última hora
```

## 🛠️ Desarrollo y Testing

### Modo Debug

Para ver logs detallados del bridge:

```bash
cd /home/ubuntu/openntIA/mcp
python3 mcp_bridge.py 2>&1 | tee bridge.log
```

### Probar Consultas Flux

Usa el endpoint REST para testing rápido:

```bash
curl -X POST http://localhost:8000/influx/query \
  -H "Content-Type: application/json" \
  -d '{
    "flux": "from(bucket: \"juniper\") |> range(start: -1h) |> filter(fn: (r) => r._measurement == \"interface_stats\") |> limit(n: 10)"
  }'
```

### Verificar Mediciones Disponibles

```bash
curl -X POST http://localhost:8000/influx/query \
  -H "Content-Type: application/json" \
  -d '{
    "flux": "import \"influxdata/influxdb/schema\"\nschema.measurements(bucket: \"juniper\")"
  }'
```

## 🔍 Troubleshooting

### Problemas con Containers (InfluxDB/Grafana)

**Error**: `Connection refused` al conectar a InfluxDB o Grafana

**Solución**:
```bash
# Verificar que los containers están corriendo
docker-compose ps

# Ver logs de InfluxDB
docker-compose logs influxdb

# Ver logs de Grafana
docker-compose logs grafana

# Reiniciar servicios
docker-compose restart

# Verificar salud de los servicios
curl http://localhost:8086/health  # InfluxDB
curl http://localhost:3000/api/health  # Grafana
```

**Error**: Los containers no inician

**Solución**:
```bash
# Ver logs detallados
docker-compose logs -f

# Eliminar y recrear containers
docker-compose down -v
docker-compose up -d

# Verificar que no hay conflictos de puertos
sudo netstat -tulpn | grep -E ':(8086|3000)'
```

**Error**: "No space left on device"

**Solución**:
```bash
# Limpiar volúmenes no utilizados
docker volume prune

# Ver espacio usado por Docker
docker system df

# Limpiar todo (¡cuidado con los datos!)
docker system prune -a --volumes
```

### Problemas con MCP Server

**Error**: `ModuleNotFoundError: No module named 'fastmcp'`

**Solución**:
```bash
# Si usas MCP Server local
pip install -r mcp/requirements.txt

# Si usas Docker, reconstruye la imagen
docker-compose build mcp-server
# o
cd mcp && docker build -t observability-mcp:latest .
```

**Error**: MCP Server no puede conectar a InfluxDB/Grafana

**Solución**:
```bash
# Si MCP Server está en Docker, verifica la red
docker network inspect openntia_observability-net

# Si MCP Server está local, verifica localhost
ping localhost
curl http://localhost:8086/health
curl http://localhost:3000/api/health

# Verifica las URLs en config.py
cat mcp/config.py | grep URL
```

### Claude Desktop no muestra las herramientas

1. Verifica que el servidor está corriendo:
   ```bash
   ps aux | grep mcp
   ```

2. Revisa los logs de Claude Desktop:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

3. Verifica la ruta en `claude_desktop_config.json` es correcta

### GitHub Copilot no encuentra las herramientas

1. Verifica que la extensión MCP está instalada
2. Recarga VS Code completamente
3. Revisa la configuración en `.vscode/settings.json`

### Errores de conexión a InfluxDB/Grafana

**Error**: `Connection refused`

**Solución**: Verifica que los servicios están corriendo:
```bash
# Verificar containers de Docker
docker-compose ps

# Verificar conectividad
curl http://localhost:8086/health  # InfluxDB
curl http://localhost:3000/api/health  # Grafana

# Si no responden, reiniciar
docker-compose restart
```

### MCP Server en Docker vs Local

**Diferencias de configuración:**

| Aspecto | MCP Local | MCP Docker |
|---------|-----------|------------|
| **URLs de conexión** | `http://localhost:8086` | `http://influxdb:8086` (si en misma red Docker) |
| **Configuración** | `config.py` local | Volumen montado o ENV vars |
| **Debugging** | Fácil con logs en consola | `docker logs mcp-server` |
| **Actualizaciones** | `git pull` + reiniciar | Rebuild imagen Docker |
| **Integración IDE** | Directa | Requiere configuración especial |

**Recomendación**: Usa **MCP local** para desarrollo y **MCP Docker** para producción.

## 📝 Notas Importantes

### Arquitectura de Containers

- **InfluxDB y Grafana**: Siempre corren en Docker containers
  - Datos persistentes en volúmenes Docker
  - Configuración en `docker-compose.yaml`
  - Reinicio automático habilitado

- **MCP Server**: Flexible (local o Docker)
  - **Local**: Mejor para desarrollo, debugging directo
  - **Docker**: Mejor para producción, portabilidad

### Puertos y Conectividad

- El **bridge MCP** (`mcp_bridge.py`) debe estar corriendo antes de usar Claude Desktop o GitHub Copilot
- Si usas **MCP Server en Docker con `--network host`**, accede a InfluxDB/Grafana con `localhost`
- Si usas **MCP Server en Docker con red personalizada**, accede con nombres de servicio (`influxdb`, `grafana`)
- El servidor MCP usa el puerto **3334** por defecto
- La REST API usa el puerto **8000** (solo para testing)
- Las consultas Flux tienen un timeout de 30 segundos
- El bucket de InfluxDB por defecto es `juniper`

### Persistencia de Datos

Los datos se almacenan en volúmenes Docker:
```bash
# Ver volúmenes
docker volume ls | grep openntia

# Backup de InfluxDB
docker exec influxdb influx backup /tmp/backup
docker cp influxdb:/tmp/backup ./influxdb-backup

# Backup de Grafana
docker exec grafana tar czf /tmp/grafana-backup.tar.gz /var/lib/grafana
docker cp grafana:/tmp/grafana-backup.tar.gz ./grafana-backup.tar.gz
```

## 🔐 Seguridad

⚠️ **Importante**: 
- No expongas el servidor MCP a internet sin autenticación
- Guarda las credenciales de InfluxDB y Grafana en variables de entorno
- Usa HTTPS en producción
- Limita las consultas Flux para evitar sobrecarga

## 📄 Licencia

Este proyecto es para uso interno y fines de observabilidad de red.

## 🤝 Contribuciones

Para agregar nuevas herramientas al servidor MCP:

1. Crea una nueva función en `tools/` con el decorador `@mcp.tool()`
2. Reinicia el servidor
3. Las herramientas aparecerán automáticamente en los clientes

---

**Desarrollado para monitorización de redes Juniper con IA** 🚀
