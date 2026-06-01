FROM python:3.11-slim

WORKDIR /app

# Dependencias necesarias para psycopg2 y compilación
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el proyecto
COPY . .

# Aseguramos que /app esté en el PYTHONPATH
ENV PYTHONPATH=/app

EXPOSE 8000

# Arrancamos FastAPI desde el paquete main
CMD ["uvicorn", "main.api:app", "--host", "0.0.0.0", "--port", "8000"]
