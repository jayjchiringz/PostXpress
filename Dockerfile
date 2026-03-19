FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Set working directory to Django project
WORKDIR /app/PostXpress

# Run migrations and collectstatic
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

# Start the application
CMD ["gunicorn", "PostXpress.wsgi:application", "--workers", "4", "--bind", "0.0.0.0:10000"]