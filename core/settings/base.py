from pathlib import Path
from shutil import which
import environ

# ------------------------------
# Environment Setup
# ------------------------------
env = environ.Env()
environ.Env.read_env('.env')

# ------------------------------
# Build BASE_DIR
# ------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ------------------------------
# Security settings
# ------------------------------
SECRET_KEY = env("SECRET_KEY")

# ------------------------------
# Installed apps
# ------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'core.apps.CoreConfig',
    'doctor.apps.DoctorConfig',
    'users.apps.UsersConfig',
    'booking.apps.BookingConfig',
    'wallet.apps.WalletConfig',

    # tailwind apps
    'tailwind',
    'theme',
]

TAILWIND_APP_NAME = 'theme'

# ------------------------------
# Middleware
# ------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ------------------------------
# URL configuration
# ------------------------------
ROOT_URLCONF = 'core.urls'

# ------------------------------
# Templates configuration
# ------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"], 
        'APP_DIRS': True,                 
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',  
                'django.contrib.auth.context_processors.auth', 
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ------------------------------
# Password validation
# ------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},

    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',        
        'OPTIONS': {'min_length': 8,}
    },
    
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# ------------------------------
# Password hashing (secure storage)
# ------------------------------
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher', 
    'django.contrib.auth.hashers.PBKDF2PasswordHasher', 
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# ------------------------------
# Internationalization
# ------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ------------------------------
# Static files 
# ------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"] 

# ------------------------------
# Media files 
# ------------------------------
MEDIA_URL = '/media/'                    
MEDIA_ROOT = BASE_DIR / "media" 

# ------------------------------
# Default primary key field type
# ------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------
# Node.js path for Tailwind
# ------------------------------
NPM_BIN_PATH = which("npm")


# ------------------------------
# Auth User Model
# ------------------------------
AUTH_USER_MODEL = 'users.User'


# --------------------------
# Authentication URL settings
# --------------------------
LOGIN_REDIRECT_URL = "home"
LOGIN_URL = "users:login"
LOGOUT_REDIRECT_URL = "home"

