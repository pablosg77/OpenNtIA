FROM python:3.11-slim

WORKDIR /app

# Clonar el repo original
RUN apt-get update && \
    apt-get install -y git && \
    git clone https://github.com/Juniper/junos-mcp-server.git /tmp/junos-mcp-server && \
    cp -r /tmp/junos-mcp-server/* /app/ && \
    rm -rf /tmp/junos-mcp-server && \
    apt-get remove -y git && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copiar tus archivos modificados (sobrescribir los originales)
COPY ./custom_files/jmcp.py /app/
COPY ./custom_files/config.py /app/utils/

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install scapy

# Copiar configuración
COPY devices.json /app/config/devices.json

# Exponer puerto
EXPOSE 30030

# Comando por defecto
CMD ["python", "jmcp.py", "-f", "/app/config/devices.json", "-t", "streamable-http", "-H", "0.0.0.0", "-p", "30030"]
