"""
Paramètres Django du projet Gestion Entrepreneurs.

Principe : tout ce qui est secret ou qui change entre le local et la
production est lu dans les variables d'environnement (fichier .env en local,
tableau de bord Render en production).
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Valeurs par défaut sûres : sans configuration, on est en mode production.
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")


# --- Sécurité de base -------------------------------------------------------

# Pas de valeur par défaut : si la clé manque, Django refuse de démarrer.
SECRET_KEY = env("SECRET_KEY")

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Render fournit automatiquement le nom de domaine du service.
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default=None)
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")


# --- Applications -----------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Nos applications seront ajoutées ici à partir de l'étape 1b.
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise sert les fichiers statiques compressés, juste après la sécurité.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Base de données --------------------------------------------------------

# Local : SQLite par défaut. Production : DATABASE_URL (Neon) dans Render.
# as_posix() évite les problèmes de barres obliques inversées sous Windows.
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="sqlite:///" + (BASE_DIR / "db.sqlite3").as_posix(),
    )
}


# --- Mots de passe ----------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Langue et fuseau horaire -----------------------------------------------

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Kinshasa"
USE_I18N = True
USE_TZ = True  # dates stockées en UTC, affichées à l'heure de Kinshasa


# --- Fichiers statiques -----------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # rempli par collectstatic en production

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # En production : fichiers compressés (moins de données mobiles)
        # et nommés avec une empreinte (cache long sans risque de version périmée).
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Sécurité en production -------------------------------------------------

if not DEBUG:
    # Render est derrière un proxy : il indique via cet en-tête si la requête était en HTTPS.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True  # cookie de session envoyé seulement en HTTPS
    CSRF_COOKIE_SECURE = True
    # HSTS : le navigateur refusera le HTTP. On commence à 1 h, on augmentera plus tard.
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)