from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# SQLite database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / "db.sqlite3",
    }
}

# Static/media paths (match docker volumes)
STATIC_URL = '/static/'
STATIC_ROOT = '/static'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/media'

# Extra production security
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
