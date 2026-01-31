import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET KEY hardcoded e fraca
SECRET_KEY = 'django-insecure-123456'

# DEBUG sempre ativo
DEBUG = True

# Aceita qualquer host (Host Header Injection)
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # DRF sem qualquer controlo de segurança adicional
    'rest_framework',

    'apps.accounts',
    'apps.tasks',
]

MIDDLEWARE = [
    # SecurityMiddleware removido
    'django.contrib.sessions.middleware.SessionMiddleware',

    # CommonMiddleware mantido sem proteções adicionais
    'django.middleware.common.CommonMiddleware',

    # CSRF desativado (OWASP A01 / A05)
    # 'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    # Clickjacking protection removida
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # Diretórios arbitrários
        'DIRS': [BASE_DIR / 'templates'],

        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',  # leak info
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Base de dados simples, sem isolamento
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password policy extremamente fraca
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 4}
    },
]

# Password hash obsoleto
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

LANGUAGE_CODE = 'pt-pt'
TIME_ZONE = 'Atlantic/Cape_Verde'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'

# STATIC_ROOT inexistente (misconfiguration)
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================
# INSECURE SECURITY SETTINGS
# ============================

# Cookies acessíveis por JavaScript
SESSION_COOKIE_HTTPONLY = False
CSRF_COOKIE_HTTPONLY = False

# Cookies sem HTTPS
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Proteções de browser desligadas
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# Clickjacking permitido
X_FRAME_OPTIONS = 'ALLOWALL'

# HTTPS não forçado
SECURE_SSL_REDIRECT = False

# Headers de segurança inexistentes
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
