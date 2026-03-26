# PostXpress/PostXpress/settings_production.py
from .settings import *
import dj_database_url
import os
from datetime import timedelta

# Security
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')

# Fix: Add schemes to ALLOWED_HOSTS
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

# Fix: Add schemes to CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://farm-fuzion-frontend-vercel.vercel.app',
    'https://farm-fuzion-abdf3.web.app'
]

# Fix: Add schemes to CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS = [
    'https://farm-fuzion-frontend-vercel.vercel.app',
    'https://farm-fuzion-abdf3.web.app',
    'https://farm-fuzion-backend.onrender.com',
    'http://localhost:3000',
    'http://localhost:5173'
]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

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

# Add whitenoise middleware (check if already present)
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
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

# ============================================
# DJANGO REST FRAMEWORK & JWT SETTINGS
# ============================================

# Add REST Framework to INSTALLED_APPS (avoid duplicates)
# Check each app before adding
apps_to_add = ['rest_framework', 'rest_framework_simplejwt', 'corsheaders']

for app in apps_to_add:
    if app not in INSTALLED_APPS:
        INSTALLED_APPS.append(app)

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'postal.jwt_auth.FarmFuzionJWTAuthentication',  # Custom auth for FarmFuzion
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# FarmFuzion Integration Settings
FARMFUZION_JWT_SECRET = os.environ.get('FARMFUZION_JWT_SECRET', SECRET_KEY)
FARMFUZION_API_URL = os.environ.get('FARMFUZION_API_URL', 'https://farm-fuzion-backend.onrender.com')

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
    'loggers': {
        'postal.jwt_auth': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
