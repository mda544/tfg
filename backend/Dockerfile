FROM python:3.10-slim

# Dependencias del sistema necesarias para:
# - asyncpg (libpq-dev)
# - geoalchemy2/shapely (libgeos-dev, libproj-dev)
# - gdal (gdal-bin, libgdal-dev)
# - passlib bcrypt (gcc)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libgeos-dev \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --no-cache-dir ./pypacity

# 1. Aplica migraciones pendientes al arrancar
# 2. Levanta el servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]