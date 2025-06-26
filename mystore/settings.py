# settings.py

import os
from pathlib import Path
import dj_database_url  # Importamos la librería

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# CONFIGURACIÓN DE SEGURIDAD PARA PRODUCCIÓN
# ==============================================================================

# La SECRET_KEY se leerá desde las variables de entorno en Render.
# No dejes la clave secreta expuesta en el código.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-default-key-for-dev')

# DEBUG será 'False' en producción (cuando la variable RENDER esté presente).
# En tu máquina local, seguirá siendo 'True'.
DEBUG = 'RENDER' not in os.environ

# Hosts permitidos. Se configurará automáticamente con la URL de Render.
ALLOWED_HOSTS = [
    '127.0.0.1',
    'fgshop-ecommerce.onrender.com',
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# ==============================================================================
# APLICACIONES
# ==============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    'django_jsonform',

    # Tus apps
    'core.apps.CoreConfig',
    'myproducts.apps.MyproductsConfig',
    'myorders.apps.MyordersConfig',
    'mycustomers.apps.MycustomersConfig',
    'mysuppliers.apps.MysuppliersConfig',
    'mydeliveries.apps.MydeliveriesConfig',
    'mycart.apps.MycartConfig',

    # Apps de Allauth
    'allauth',
    'allauth.account',
    
    # Apps de terceros
    'crispy_forms',
    'crispy_bootstrap5',
    'storages',  # Añadido para gestionar S3
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <-- AÑADIDO PARA WHITENOISE
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    # El segundo XFrameOptionsMiddleware era un duplicado y fue eliminado.
]

X_FRAME_OPTIONS = 'SAMEORIGIN'
ROOT_URLCONF = 'mystore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'mycart.context_processors.cart',
                'myproducts.context_processors.categories_for_menu',
            ],
        },
    },
]

WSGI_APPLICATION = 'mystore.wsgi.application'

# ==============================================================================
# BASE DE DATOS
# ==============================================================================

DATABASES = {
    'default': dj_database_url.config(
        # Leerá la URL de la base de datos de Render desde la variable de entorno.
        # Si no la encuentra, usará tu SQLite local para desarrollo.
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600  # Mantiene las conexiones abiertas por 600 segundos
    )
}

# ==============================================================================
# ARCHIVOS ESTÁTICOS (CSS, JS) Y MEDIA (IMÁGENES SUBIDAS)
# ==============================================================================

# URL para acceder a los archivos estáticos en el navegador.
STATIC_URL = '/static/'
# Directorio donde `collectstatic` reunirá todos los archivos estáticos para producción.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# URL para los archivos de medios.
MEDIA_URL = '/media/'
# Directorio donde se guardan los archivos subidos localmente.
MEDIA_ROOT = BASE_DIR / 'media'

# Configuración del almacenamiento para producción (WhiteNoise y S3)
# Esta variable 'STORAGES' es la forma moderna de configurar esto en Django.
STORAGES = {
    "default": {
        # Configuración por defecto para MEDIA (archivos subidos)
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # Configuración para STATIC (CSS, JS) usando WhiteNoise
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Configuración para AWS S3 (solo se activará en producción)
if 'AWS_ACCESS_KEY_ID' in os.environ:
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    
    # Sobrescribimos el almacenamiento 'default' para que apunte a S3 en producción.
    STORAGES['default'] = {'BACKEND': 'storages.backends.s3.S3Storage'}


# ==============================================================================
# CONFIGURACIÓN DE AUTENTICACIÓN Y ALLAUTH (Sin cambios)
# ==============================================================================

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_USERNAME_MIN_LENGTH = 4
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_FORMS = {
    'login': 'mycustomers.forms.CustomLoginFormAllauth',
    'signup': 'mycustomers.forms.CustomSignupFormAllauth',
    'reset_password': 'allauth.account.forms.ResetPasswordForm',
}
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_SESSION_REMEMBER = True


# ==============================================================================
# OTRAS CONFIGURACIONES (Sin cambios)
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CART_SESSION_ID = 'cart_fgshop'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Durante el despliegue, los correos se mostrarán en los logs de Render.
# Para enviar correos reales, necesitarás un servicio como SendGrid o Mailgun.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'