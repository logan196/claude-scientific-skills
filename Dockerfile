FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
  CMD curl -f http://localhost:8100/health || exit 1

CMD ["python", "-m", "mcp_server", "--host", "0.0.0.0", "--port", "8100"]
