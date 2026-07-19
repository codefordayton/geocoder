FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies first for better layer caching.
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# App code and the pre-built lookup index.
COPY app.py .
COPY geocoder.db .

# Cloud Run injects PORT; default to 8080 for local `docker run`.
ENV PORT=8080
EXPOSE 8080

# Shell form so $PORT expands at runtime.
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT}
