from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Auto-reload browser during development
INSTALLED_APPS += ['django_browser_reload']

# Add django_browser_reload middleware
MIDDLEWARE += [
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]
