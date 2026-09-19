FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies first for better layer caching.
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# The parcel index is rebuilt from the County's live parcel layer by
# fetch_parcels.py and published as the `geocoder-data` release asset (~30 MB).
# Baking it in keeps the service stateless and read-only.
ADD https://github.com/codefordayton/geocoder/releases/download/geocoder-data/geocoder.db /app/geocoder.db

COPY app.py .

ENV PORT=8080
EXPOSE 8080

# Shell form so $PORT expands at runtime. Bind "::" (dual-stack) so the service
# is reachable over Railway's IPv6-only private network as well as IPv4.
CMD exec uvicorn app:app --host :: --port ${PORT}
