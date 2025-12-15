FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# User non-root
RUN useradd -m appuser
USER appuser

CMD ["python", "generator.py"]