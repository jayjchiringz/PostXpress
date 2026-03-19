# PostXpress/PostXpress/settings_production.py
from .settings import *
import dj_database_url
import os

# Security
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')

# Fix: Add schemes to ALLOWED_HOSTS
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

# Fix: Add schemes to CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://farm-fuzion-frontend-vercel.vercel.app'
]

# Fix: Add schemes to CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS = [
    'https://farm-fuzion-frontend-vercel.vercel.app',
    'https://farm-fuzion-backend.onrender.com',
    'http://localhost:3000'
]
CORS_ALLOW_ALL_ORIGINS = False

# Database - PostgreSQL (don't run migrations during build)
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add whitenoise middleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Media files (for QR codes, barcodes)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}