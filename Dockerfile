# Use specific Python version
FROM python:3.11.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=PostXpress.settings_production
ENV PORT=10000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set working directory to Django project
WORKDIR /app/PostXpress

# Collect static files (doesn't need database)
RUN python manage.py collectstatic --noinput

# Expose the port
EXPOSE 10000

# Start the application with proper error handling
# Using shell grouping to ensure gunicorn starts regardless of migration status
CMD sh -c 'python manage.py makemigrations --noinput || echo "makemigrations failed, continuing..." ; \
           python manage.py migrate --noinput || echo "migrate failed, continuing..." ; \
           echo "Starting gunicorn on port $PORT" ; \
           gunicorn PostXpress.wsgi:application --workers 4 --bind 0.0.0.0:$PORT --access-logfile - --error-logfile -'