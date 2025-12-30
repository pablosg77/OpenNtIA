# 📦 Proyecto Limpio - Estructura Final

## Archivos del Proyecto

```
openntIA/
│
├── README.md                           ✅ Documentación completa
├── QUICKSTART.md                       ✅ Guía rápida de inicio
├── docker-compose.yaml                 ✅ Servicios (InfluxDB, Grafana)
├── claude_desktop_config.json          ✅ Configuración ejemplo para Claude
│
├── .vscode/
│   └── settings.json                   ✅ Configuración para VS Code + Copilot
│
└── mcp/                                📁 Servidor MCP
    ├── server.py                       ✅ Servidor MCP principal (FastMCP)
    ├── mcp_bridge.py                   ✅ Bridge stdio ↔ HTTP
    ├── api.py                          ✅ REST API para testing
    ├── config.py                       ✅ Configuración (credenciales)
    ├── requirements.txt                ✅ Dependencias Python
    ├── start_servers.sh                ✅ Script de inicio
    ├── Dockerfile                      ⚙️  (Opcional) Para containerizar
    │
    └── tools/                          📁 Herramientas MCP
        ├── __init__.py                 ✅
        ├── influx.py                   ✅ Herramientas InfluxDB
        └── grafana.py                  ✅ Herramientas Grafana
```

## ✅ Archivos Eliminados (ya no necesarios)

- ❌ `mcp/mcp_bridge.js` - Bridge en JavaScript (reemplazado por Python)
- ❌ `mcp/package.json` - Dependencias Node.js (ya no se usan)
- ❌ `insert_test_data.py` - Script temporal de pruebas
- ❌ `MCP_SETUP_INSTRUCTIONS.md` - Documentación antigua
- ❌ `COPILOT_MCP_USAGE.md` - Documentación antigua
- ❌ `mcp/__pycache__/` - Caché de Python

## 📚 Documentación Actualizada

### 1. README.md
- Descripción completa del proyecto
- Arquitectura del sistema
- Instrucciones de instalación paso a paso
- Configuración para Claude Desktop
- Configuración para VS Code + GitHub Copilot
- Ejemplos de uso
- Troubleshooting completo

### 2. QUICKSTART.md
- Guía rápida de 3 pasos para Claude Desktop
- Guía rápida de 3 pasos para VS Code + Copilot
- Verificación rápida
- Troubleshooting express

### 3. claude_desktop_config.json
- Configuración lista para copiar
- Comando correcto: `python3 /home/ubuntu/openntIA/mcp/mcp_bridge.py`

### 4. .vscode/settings.json
- Configuración lista para usar
- Integración con GitHub Copilot

## 🚀 Cómo Desplegar

### Paso 1: Instalar Dependencias
```bash
cd /home/ubuntu/openntIA/mcp
pip install -r requirements.txt
```

### Paso 2: Configurar Credenciales
Edita `mcp/config.py` con tus credenciales de InfluxDB y Grafana

### Paso 3: Iniciar Servidor
```bash
cd /home/ubuntu/openntIA/mcp
chmod +x start_servers.sh
./start_servers.sh
```

### Paso 4: Configurar Cliente

**Para Claude Desktop:**
- Copia el contenido de `claude_desktop_config.json`
- Pégalo en `~/.config/Claude/claude_desktop_config.json`
- Reinicia Claude Desktop

**Para VS Code + GitHub Copilot:**
- El archivo `.vscode/settings.json` ya está configurado
- Instala la extensión "Model Context Protocol"
- Recarga VS Code (Ctrl+Shift+P → Reload Window)

## ✨ Herramientas Disponibles

1. **query_influx** - Consulta métricas de InfluxDB con Flux
2. **list_dashboards** - Lista dashboards de Grafana
3. **get_dashboard** - Obtiene detalles de un dashboard

## 🎯 Todo Listo!

El proyecto está limpio y documentado. Solo necesitas:
1. Tener InfluxDB y Grafana corriendo
2. Configurar las credenciales en `config.py`
3. Iniciar el servidor con `./start_servers.sh`
4. Configurar tu cliente (Claude o VS Code)

---

**¿Necesitas ayuda?** Consulta:
- `README.md` para documentación completa
- `QUICKSTART.md` para inicio rápido
