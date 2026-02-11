FROM python:3.12.9

WORKDIR /app

# 1. Dependencias de sistema para Playwright
RUN apt-get update && apt-get install -y \
    curl libnss3 libnspr4 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 2. CREAR Y USAR ENTORNO VIRTUAL (Crucial)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Instalamos librerías dentro del venv
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Playwright (instalado dentro del venv)
RUN playwright install chromium --with-deps

COPY . .

# 5. Puertos
EXPOSE 3000
EXPOSE 8000

# 6. Arranque: El venv ya está activo por la variable PATH
CMD ["/opt/venv/bin/reflex", "run", "--loglevel", "debug"]
