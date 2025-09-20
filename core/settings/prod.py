from .base import *

DEBUG = False

# Allow only your domain/servers
ALLOWED_HOSTS = ["yourdomain.com", "www.yourdomain.com"]

# Example: PostgreSQL for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env("DB_NAME"),
        'USER': env("DB_USER"),
        'PASSWORD': env("DB_PASSWORD"),
        'HOST': env("DB_HOST", default="localhost"),
        'PORT': env("DB_PORT", default="5432"),
    }
}

# Static files for production
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

# Extra security in production
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
