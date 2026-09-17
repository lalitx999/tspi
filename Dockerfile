# Dockerfile for Dr. Pat TSPI Clinical AI Backend
FROM python:3.11-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for psycopg2, weasyprint, and pandas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    libpango-1.0-0 \
    pango1.0-tools \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-thai-tlwg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir gunicorn uvicorn && \
    pip install --no-cache-dir -r requirements.txt

# Copy application backend files
COPY . /app/

EXPOSE 8000

# Default command to run gunicorn WSGI server
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
