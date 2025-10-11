from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------
SECRET_KEY = "qro2dj^!9!8pdg5p@g93)8_&v)x%ufb&g^y^f3xgwb)av*8n@f"

DEBUG = True  # ⚠️ Recuerda cambiar a False en producción

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# ---------------------------------------------------------------------
# Apps
# ---------------------------------------------------------------------
DJANGO_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "widget_tweaks",
]

LOCAL_APPS = [
    "dashboard",
    "accounts",
    "cash",
    "catalog",
    "customers",
    "inventory",
    "orders",
    "theme",
    "reports"
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

# ---------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------
TEMPLATES_DIR = BASE_DIR / "templates"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "theme.context_processors.active_theme",
            ],
        },
    },
]


WSGI_APPLICATION = "core.wsgi.application"

# ---------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---------------------------------------------------------------------
# Validadores de password
# ---------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------
# Internacionalización
# ---------------------------------------------------------------------
LANGUAGE_CODE = "es"

TIME_ZONE = "America/Santo_Domingo"

USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------
# Archivos estáticos y media
# ---------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]     # Para desarrollo
STATIC_ROOT = BASE_DIR / "staticfiles"       # Para producción (collectstatic)

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------
# Configuración por defecto de PK
# ---------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"


# ---------------------------------------------------------------------
# Gestion logs
# ---------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}


# ---------------------------------------------------------------------
# Configuracion de Jazzmin
# ---------------------------------------------------------------------

JAZZMIN_SETTINGS = {
    # Identidad general
    "site_title": "Backoffice",
    "site_header": "Backoffice",
    "site_brand": "Backoffice",
    "welcome_sign": "Bienvenido al Backoffice de Lavandería",
    "copyright": "© Lavandería Clean Studio",

    # Sin logo por ahora (dejamos vacío)
    "site_logo": None,
    "login_logo": None,
    "site_icon": None,

    # Búsqueda global
    "search_model": [
        "orders.Order",

    ],

    # Avatar (si luego tienes campo en User)
    "user_avatar": None,

    # ===========================
    # 🔹 MENÚ SUPERIOR Y USUARIO
    # ===========================
    "topmenu_links": [
        {"name": "Inicio", "url": "/", "permissions": ["auth.view_user"]},
    ],
    "usermenu_links": [
        {"name": "Inicio", "url": "/", "new_window": False},
    ],

    # ===========================
    # 🔹 MENÚ LATERAL
    # ===========================
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    # Orden lógico de tus apps
    "order_with_respect_to": [
        "theme",          # identidad visual
        "customers",      # clientes
        "catalog",        # servicios
        "orders",         # órdenes
        "inventory",      # inventario
        "cash",           # caja
        "reports",        # reportes
        "auth",           # usuarios y grupos
    ],

    # Íconos por app y modelo (FontAwesome)
    "icons": {
        # Usuarios y seguridad
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",

        # Core del negocio
        "customers": "fas fa-user-tag",
        "customers.customer": "fas fa-id-badge",

        "catalog": "fas fa-tags",
        "catalog.service": "fas fa-cogs",
        "catalog.servicecategory": "fas fa-folder-tree",
        "catalog.servicepricing": "fas fa-dollar-sign",

        "orders": "fas fa-box",
        "orders.order": "fas fa-file-invoice",
        "orders.orderline": "fas fa-list-ul",
        "orders.ordertracking": "fas fa-clock",

        "inventory": "fas fa-warehouse",
        "inventory.unit": "fas fa-ruler",
        "inventory.inventoryitem": "fas fa-boxes-stacked",
        "inventory.inventorymovement": "fas fa-arrows-rotate",

        "cash": "fas fa-cash-register",
        "cash.cashregister": "fas fa-wallet",
        "cash.cashmovement": "fas fa-money-bill-transfer",

        "reports": "fas fa-chart-line",
        "theme.theme": "fas fa-brush",
    },

    # Por si olvidas asignar iconos a alguno
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # ===========================
    # 🔹 FORMATO DE PÁGINAS
    # ===========================
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "collapsible",
    },

    # ===========================
    # 🔹 UI Y EXPERIENCIA
    # ===========================
    "related_modal_active": True,
    "language_chooser": False,
    "show_ui_builder": False,
}


