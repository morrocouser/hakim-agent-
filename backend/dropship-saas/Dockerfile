FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY dropship_saas/ dropship_saas/
COPY .env.example .env

EXPOSE 8000

CMD ["uvicorn", "dropship_saas.api.main:app", "--host", "0.0.0.0", "--port", "8000"]