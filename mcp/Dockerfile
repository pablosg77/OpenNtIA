FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose both MCP (3334) and REST API (8000)
EXPOSE 8000 3334

# Start both servers using shell
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port 8000 & fastmcp run server.py --host 0.0.0.0 --port 3334"]

