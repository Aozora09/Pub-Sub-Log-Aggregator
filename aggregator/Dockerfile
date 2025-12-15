FROM python:3.11-slim

WORKDIR /app

# Install dependencies sistem yang minimal
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Setup user non-root
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Jalankan server (Uvicorn)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]