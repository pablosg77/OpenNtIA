# 🔧 Comandos Útiles - Cheat Sheet

Referencia rápida de comandos para gestionar el proyecto.

---

## 🐳 Docker (InfluxDB + Grafana)

### Gestión Básica
```bash
# Levantar servicios
docker-compose up -d

# Ver estado
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f influxdb
docker-compose logs -f grafana

# Reiniciar servicios
docker-compose restart

# Detener servicios
docker-compose stop

# Detener y eliminar containers
docker-compose down

# Eliminar también los volúmenes (¡CUIDADO! Borra datos)
docker-compose down -v
```

### Inspección
```bash
# Entrar al container de InfluxDB
docker exec -it influxdb bash

# Entrar al container de Grafana
docker exec -it grafana bash

# Ver recursos usados
docker stats

# Ver volúmenes
docker volume ls

# Inspeccionar volumen
docker volume inspect openntia_influxdb-data
```

### Backup y Restore
```bash
# Backup de InfluxDB
docker exec influxdb influx backup /tmp/backup -t YOUR_TOKEN
docker cp influxdb:/tmp/backup ./influxdb-backup-$(date +%Y%m%d)

# Backup de Grafana
docker exec grafana tar czf /tmp/grafana-backup.tar.gz /var/lib/grafana
docker cp grafana:/tmp/grafana-backup.tar.gz ./grafana-backup-$(date +%Y%m%d).tar.gz

# Restore InfluxDB
docker cp ./influxdb-backup influxdb:/tmp/
docker exec influxdb influx restore /tmp/influxdb-backup
```

---

## 🐍 MCP Server (Local)

### Gestión Básica
```bash
# Instalar dependencias
cd /home/ubuntu/openntIA/mcp
pip install -r requirements.txt

# Iniciar servidor
./start_servers.sh

# Detener servidor (Ctrl+C o)
pkill -f "server.py"
pkill -f "api.py"

# Ver procesos corriendo
ps aux | grep server.py
ps aux | grep api.py

# Ver logs (si se redirigen a archivo)
tail -f /tmp/mcp_server.log
```

### Testing
```bash
# Verificar configuración
python3 verify_setup.py

# Probar REST API
curl http://localhost:8000/

# Listar dashboards
curl http://localhost:8000/grafana/dashboards

# Consultar InfluxDB
curl -X POST http://localhost:8000/influx/query \
  -H "Content-Type: application/json" \
  -d '{"flux": "from(bucket: \"juniper\") |> range(start: -1h) |> limit(n: 5)"}'

# Probar conexión a InfluxDB
curl http://localhost:8086/health

# Probar conexión a Grafana
curl http://localhost:3000/api/health
```

### Debug
```bash
# Ejecutar servidor en modo verbose
cd /home/ubuntu/openntIA/mcp
python3 server.py --verbose

# Ver logs del bridge
python3 mcp_bridge.py 2>&1 | tee bridge.log

# Verificar puertos abiertos
sudo netstat -tulpn | grep -E ':(3334|8000|8086|3000)'

# O con ss
sudo ss -tulpn | grep -E ':(3334|8000|8086|3000)'
```

---

## 🐳 MCP Server (Docker)

### Construcción y Ejecución
```bash
# Construir imagen
cd /home/ubuntu/openntIA/mcp
docker build -t observability-mcp:latest .

# Ejecutar container
docker run -d \
  --name mcp-server \
  --network host \
  -v $(pwd)/config.py:/app/config.py:ro \
  -p 8000:8000 \
  -p 3334:3334 \
  observability-mcp:latest

# Ver logs
docker logs -f mcp-server

# Detener y eliminar
docker stop mcp-server
docker rm mcp-server

# Reconstruir y reiniciar
docker stop mcp-server && docker rm mcp-server
docker build -t observability-mcp:latest . && \
docker run -d --name mcp-server --network host \
  -v $(pwd)/config.py:/app/config.py:ro \
  -p 8000:8000 -p 3334:3334 \
  observability-mcp:latest

# Entrar al container
docker exec -it mcp-server bash

# Ver recursos del container
docker stats mcp-server
```

---

## 📊 InfluxDB

### CLI
```bash
# Entrar al CLI de InfluxDB
docker exec -it influxdb influx

# Desde CLI, listar buckets
> buckets()

# Consulta simple
> from(bucket: "juniper") |> range(start: -1h) |> limit(n: 5)
```

### API
```bash
# Obtener health
curl http://localhost:8086/health

# Listar buckets (necesitas token)
curl -X GET http://localhost:8086/api/v2/buckets \
  -H "Authorization: Token YOUR_TOKEN"

# Query API
curl -X POST http://localhost:8086/api/v2/query \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "from(bucket: \"juniper\") |> range(start: -1h) |> limit(n: 5)",
    "org": "juniper"
  }'
```

### Datos de Prueba
```bash
# Insertar datos de prueba
python3 /home/ubuntu/openntIA/insert_test_data.py

# O manualmente via API
curl -X POST "http://localhost:8086/api/v2/write?org=juniper&bucket=juniper" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d "measurement,device=test,interface=eth0 value=100 $(date +%s)000000000"
```

---

## 📈 Grafana

### API
```bash
# Health check
curl http://localhost:3000/api/health

# Listar dashboards (necesitas API key)
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:3000/api/search

# Obtener dashboard específico
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:3000/api/dashboards/uid/DASHBOARD_UID

# Crear datasource
curl -X POST http://localhost:3000/api/datasources \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "InfluxDB-Test",
    "type": "influxdb",
    "url": "http://influxdb:8086",
    "access": "proxy",
    "jsonData": {
      "version": "Flux",
      "organization": "juniper",
      "defaultBucket": "juniper"
    },
    "secureJsonData": {
      "token": "YOUR_INFLUX_TOKEN"
    }
  }'
```

### UI
```bash
# Abrir Grafana en navegador
xdg-open http://localhost:3000

# Login: admin / admin123 (según docker-compose.yaml)
```

---

## 🔍 Monitoreo y Diagnóstico

### Sistema
```bash
# Ver uso de recursos
htop

# Ver uso de disco
df -h

# Ver espacio usado por Docker
docker system df

# Limpiar Docker
docker system prune -a

# Ver procesos de Python
ps aux | grep python

# Ver procesos escuchando en puertos
sudo netstat -tulpn | grep LISTEN
```

### Red
```bash
# Probar conectividad
ping localhost

# Verificar DNS
nslookup localhost

# Ver conexiones activas
sudo netstat -ant | grep ESTABLISHED

# Test de puertos
nc -zv localhost 8086  # InfluxDB
nc -zv localhost 3000  # Grafana
nc -zv localhost 3334  # MCP Server
nc -zv localhost 8000  # REST API
```

### Logs
```bash
# Ver logs del sistema
sudo journalctl -f

# Ver logs de Docker daemon
sudo journalctl -u docker -f

# Ver logs de containers
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f --tail=100 influxdb
```

---

## 🔧 Configuración

### InfluxDB
```bash
# Obtener token (desde UI o CLI)
# UI: http://localhost:8086 → Load Data → API Tokens

# Crear bucket
docker exec influxdb influx bucket create -n test-bucket -o juniper

# Listar buckets
docker exec influxdb influx bucket list
```

### Grafana
```bash
# Crear API key (desde UI)
# UI: http://localhost:3000 → Configuration → API Keys → New API Key

# O vía API
curl -X POST http://localhost:3000/api/auth/keys \
  -H "Content-Type: application/json" \
  -u admin:admin123 \
  -d '{
    "name": "mcp-server-key",
    "role": "Admin"
  }'
```

### MCP Server
```bash
# Editar configuración
nano /home/ubuntu/openntIA/mcp/config.py

# Verificar configuración
python3 /home/ubuntu/openntIA/mcp/verify_setup.py

# Ver configuración actual
cat /home/ubuntu/openntIA/mcp/config.py | grep -E "^[A-Z]"
```

---

## 🆘 Troubleshooting Rápido

### Resetear Todo
```bash
# Parar todo
docker-compose down
pkill -f server.py
pkill -f api.py

# Limpiar volúmenes (¡CUIDADO! Borra datos)
docker-compose down -v

# Levantar de nuevo
docker-compose up -d

# Reiniciar MCP Server
cd /home/ubuntu/openntIA/mcp
./start_servers.sh
```

### Verificar Estado Completo
```bash
# Containers
docker-compose ps

# Procesos Python
ps aux | grep -E "(server|api|bridge)"

# Puertos
sudo netstat -tulpn | grep -E ":(8086|3000|3334|8000)"

# Conectividad
curl http://localhost:8086/health
curl http://localhost:3000/api/health
curl http://localhost:8000/
```

### Ver Todo el Stack
```bash
# Script one-liner para ver todo
echo "=== Docker Containers ===" && docker-compose ps && \
echo -e "\n=== Python Processes ===" && ps aux | grep -E "(server|api|bridge)" | grep -v grep && \
echo -e "\n=== Open Ports ===" && sudo netstat -tulpn | grep -E ":(8086|3000|3334|8000)" && \
echo -e "\n=== Service Health ===" && \
echo "InfluxDB: $(curl -s http://localhost:8086/health | jq -r .status 2>/dev/null || echo 'FAIL')" && \
echo "Grafana: $(curl -s http://localhost:3000/api/health | jq -r .database 2>/dev/null || echo 'FAIL')" && \
echo "MCP API: $(curl -s http://localhost:8000/ | jq -r .service 2>/dev/null || echo 'FAIL')"
```

---

## 📝 Aliases Útiles

Agrega al `~/.bashrc`:

```bash
# MCP Server aliases
alias mcp-start='cd /home/ubuntu/openntIA && docker-compose up -d && cd mcp && ./start_servers.sh'
alias mcp-stop='cd /home/ubuntu/openntIA && docker-compose stop && pkill -f server.py'
alias mcp-status='docker-compose ps && ps aux | grep server.py | grep -v grep'
alias mcp-logs='docker-compose logs -f'
alias mcp-test='curl http://localhost:8000/grafana/dashboards'
alias mcp-health='echo "InfluxDB:" && curl -s http://localhost:8086/health && echo -e "\nGrafana:" && curl -s http://localhost:3000/api/health'
```

Luego ejecuta: `source ~/.bashrc`

---

**Guarda este archivo para referencia rápida!** 📚
