# 🚀 START HERE - Observability MCP Server

## 📚 Bienvenido al Proyecto

Este es un **servidor MCP (Model Context Protocol)** para observabilidad de redes Juniper que permite a asistentes de IA (Claude Desktop, GitHub Copilot) consultar métricas de InfluxDB y gestionar dashboards de Grafana.

---

## ⚡ Inicio Rápido (5 minutos)

### 1. Levantar Servicios Base
```bash
cd /home/ubuntu/openntIA
docker-compose up -d
```

### 2. Configurar Credenciales
```bash
cd mcp
cp config.example.py config.py
nano config.py  # Edita tokens de InfluxDB y Grafana
```

### 3. Iniciar MCP Server
```bash
pip install -r requirements.txt
./start_servers.sh
```

### 4. Configurar Cliente
- **Claude Desktop**: Ver [`QUICKSTART.md`](QUICKSTART.md#-para-claude-desktop)
- **VS Code + Copilot**: Ver [`QUICKSTART.md`](QUICKSTART.md#-para-vs-code--github-copilot)

---

## 📖 Guía de Documentación

| Documento | ¿Cuándo Leerlo? | Tiempo |
|-----------|-----------------|--------|
| **[START_HERE.md](START_HERE.md)** | 👈 Estás aquí | 5 min |
| **[QUICKSTART.md](QUICKSTART.md)** | Quiero empezar YA | 5 min |
| **[README.md](README.md)** | Documentación completa | 20 min |
| **[DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md)** | ¿Local o Docker? | 10 min |
| **[CONTAINER_ARCHITECTURE.md](CONTAINER_ARCHITECTURE.md)** | Entender la arquitectura | 10 min |
| **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** | Ver estructura de archivos | 5 min |
| **[VISUAL_GUIDE.md](VISUAL_GUIDE.md)** | Guía visual paso a paso | 15 min |
| **[ARCHITECTURE.txt](ARCHITECTURE.txt)** | Diagrama ASCII completo | 5 min |

---

## 🏗️ Arquitectura en 3 Capas

```
┌─────────────────────┐
│  Claude / Copilot   │  ← Clientes AI
└──────────┬──────────┘
           │ stdio
┌──────────▼──────────┐
│   mcp_bridge.py     │  ← Bridge (stdio ↔ HTTP)
└──────────┬──────────┘
           │ HTTP
┌──────────▼──────────┐
│   MCP Server        │  ← FastMCP (Local o Docker)
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌─────────┐  ┌─────────┐
│ InfluxDB│  │ Grafana │  ← Docker (Siempre)
└─────────┘  └─────────┘
```

---

## 🎯 ¿Qué Puedes Hacer?

Una vez configurado, puedes preguntarle a la IA:

✅ **"¿Cuáles son las interfaces con mayor utilización de ancho de banda?"**
✅ **"Muéstrame todos los dashboards de Grafana"**
✅ **"¿Cuál es el uso de CPU y memoria de todos los dispositivos?"**
✅ **"¿Cuántos peers BGP están activos en mx960-core1?"**

---

## 🐳 Componentes

### Siempre en Docker:
- **InfluxDB** (puerto 8086) - Base de datos de métricas
- **Grafana** (puerto 3000) - Visualización

### Flexible (Local o Docker):
- **MCP Server** (puerto 3334) - Servidor de herramientas MCP
- **REST API** (puerto 8000) - Para testing

---

## 🔧 Herramientas MCP Disponibles

1. **`query_influx`** - Ejecuta consultas Flux en InfluxDB
2. **`list_dashboards`** - Lista dashboards de Grafana
3. **`get_dashboard`** - Obtiene detalles de un dashboard

---

## 📁 Estructura de Archivos

```
openntIA/
├── 📄 Documentación/
│   ├── START_HERE.md          ← Estás aquí
│   ├── QUICKSTART.md          ← Inicio rápido
│   ├── README.md              ← Documentación principal
│   ├── DEPLOYMENT_OPTIONS.md  ← Opciones de despliegue
│   └── ...más guías...
│
├── 🐳 Docker/
│   ├── docker-compose.yaml    ← InfluxDB + Grafana
│   └── mcp/Dockerfile         ← (Opcional) MCP en Docker
│
├── 🐍 MCP Server/
│   ├── server.py              ← Servidor MCP principal
│   ├── mcp_bridge.py          ← Bridge stdio ↔ HTTP
│   ├── api.py                 ← REST API de testing
│   ├── config.py              ← Configuración
│   ├── start_servers.sh       ← Script de inicio
│   ├── verify_setup.py        ← Verificar instalación
│   └── tools/                 ← Herramientas MCP
│       ├── influx.py          ← InfluxDB tools
│       └── grafana.py         ← Grafana tools
│
└── ⚙️ Configuración/
    ├── claude_desktop_config.json  ← Ejemplo para Claude
    └── .vscode/settings.json       ← Ejemplo para VS Code
```

---

## 🚦 Checklist de Inicio

- [ ] Docker y Docker Compose instalados
- [ ] Python 3.8+ instalado
- [ ] `docker-compose up -d` ejecutado
- [ ] InfluxDB y Grafana accesibles (http://localhost:8086 y :3000)
- [ ] Tokens de InfluxDB y Grafana obtenidos
- [ ] `mcp/config.py` configurado
- [ ] `pip install -r mcp/requirements.txt` completado
- [ ] `./mcp/start_servers.sh` ejecutado
- [ ] Claude Desktop o VS Code configurado
- [ ] Primera consulta exitosa ✨

---

## 🆘 ¿Problemas?

### Containers no inician
```bash
docker-compose logs -f
docker-compose restart
```

### MCP Server no conecta
```bash
# Verificar que todo está corriendo
docker-compose ps
ps aux | grep server.py

# Verificar conectividad
curl http://localhost:8086/health
curl http://localhost:8000/grafana/dashboards
```

### Cliente (Claude/VS Code) no ve las herramientas
1. Verifica que el servidor MCP está corriendo
2. Revisa la ruta en la configuración del cliente
3. Reinicia el cliente

**Ver más**: [README.md - Troubleshooting](README.md#-troubleshooting)

---

## 🎓 Rutas de Aprendizaje

### Ruta Rápida (20 minutos)
1. Lee [START_HERE.md](START_HERE.md) ← Estás aquí
2. Sigue [QUICKSTART.md](QUICKSTART.md)
3. Configura tu cliente
4. ¡Empieza a usar!

### Ruta Completa (1 hora)
1. Lee [START_HERE.md](START_HERE.md)
2. Lee [README.md](README.md) completo
3. Lee [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md)
4. Decide tu opción de despliegue
5. Sigue [VISUAL_GUIDE.md](VISUAL_GUIDE.md)
6. Configura y prueba

### Ruta Arquitecto (2 horas)
1. Lee toda la documentación
2. Revisa [CONTAINER_ARCHITECTURE.md](CONTAINER_ARCHITECTURE.md)
3. Estudia [ARCHITECTURE.txt](ARCHITECTURE.txt)
4. Lee el código fuente
5. Personaliza según tus necesidades

---

## 💡 Tips Importantes

1. **InfluxDB y Grafana** → Siempre en Docker
2. **MCP Server** → Local para desarrollo, Docker para producción
3. **Orden de inicio**: Docker primero, luego MCP Server
4. **URLs**: `localhost` si MCP local, nombres de servicio si MCP en Docker
5. **Bridge**: Necesario para Claude Desktop y VS Code

---

## 🔗 Enlaces Rápidos

- **Documentación Principal**: [README.md](README.md)
- **Inicio Rápido**: [QUICKSTART.md](QUICKSTART.md)
- **Opciones de Despliegue**: [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md)
- **Troubleshooting**: [README.md#troubleshooting](README.md#-troubleshooting)

---

## 📞 Siguiente Paso

👉 **Ve a [QUICKSTART.md](QUICKSTART.md) para empezar ahora**

O

📖 **Lee [README.md](README.md) para documentación completa**

---

**¡Bienvenido a la observabilidad de red con IA!** 🚀🤖📊
