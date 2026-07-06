FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Data directory for SQLite (will be mounted as Railway volume)
RUN mkdir -p /app/data

EXPOSE 8000

# Railway sets PORT env var automatically
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
