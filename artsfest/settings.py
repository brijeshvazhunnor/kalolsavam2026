import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------
# BASIC SETTINGS
# ---------------------------------------------------------

SECRET_KEY = 'your-strong-secret-key'   # Replace in production

DEBUG = True   # Change to False when deploying

ALLOWED_HOSTS = ['*']  # Change to real domain/IP when DEBUG=False


# ---------------------------------------------------------
# INSTALLED APPS
# ---------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your apps
    'accounts',
    'widget_tweaks',
]


# ---------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',   # REQUIRED
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # REQUIRED
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]



# ---------------------------------------------------------
# URL CONFIG (Your Missing Key!)
# ---------------------------------------------------------

ROOT_URLCONF = 'artsfest.urls'


# ---------------------------------------------------------
# TEMPLATES
# ---------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ---------------------------------------------------------
# WSGI / ASGI
# ---------------------------------------------------------

WSGI_APPLICATION = 'artsfest.wsgi.application'


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ---------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 9},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ---------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------
# STATIC & MEDIA FILES
# ---------------------------------------------------------

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ---------------------------------------------------------
# CUSTOM USER MODEL
# ---------------------------------------------------------

AUTH_USER_MODEL = 'accounts.CustomUser'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


# ---------------------------------------------------------
# PASSWORD HASHERS (Strong Security)
# ---------------------------------------------------------

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]


# ---------------------------------------------------------
# SECURITY SETTINGS (Modify when deploying)
# ---------------------------------------------------------

SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = False   # use True in HTTPS
CSRF_COOKIE_SECURE = False      # use True in HTTPS
SECURE_SSL_REDIRECT = False     # enable only with HTTPS
X_FRAME_OPTIONS = 'DENY'


# ---------------------------------------------------------
# CACHING
# ---------------------------------------------------------

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------
# LOGIN SYSTEM SETTINGS (Fix 404)
# ---------------------------------------------------------

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# settings.py
CATEGORY_LIMITS = {
    "sahithyolsavam": 27,
    "chithrolsavam": 9,
    "sangeetholsavam": 17,
    "nritholsavam": 12,
    "drishyanatakolsavam": 8,
}

# Drishyanatakolsavam — Natakam special restriction
NATAKAM_ITEMS = [
    "Natakam (Malayalam)",
    "Natakam (English)",
    "Natakam (Hindi)",
    "Natakam (Kannada)",
]
MAX_NATAKAM = 2
