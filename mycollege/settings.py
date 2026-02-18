from pathlib import Path
import os
from django.contrib.messages import constants as messages

# -------------------------------------------------------------------------
# Base paths
# -------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------------
# Core settings
# -------------------------------------------------------------------------
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-this-in-production-1234567890"
)

DEBUG = False  # ✅ MUST be False on Render

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".onrender.com",
]

# -------------------------------------------------------------------------
# Applications
# -------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Your app
    "main.apps.MainConfig",
]

# -------------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ✅ REQUIRED
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -------------------------------------------------------------------------
# URLs / WSGI
# -------------------------------------------------------------------------
ROOT_URLCONF = "mycollege.urls"
WSGI_APPLICATION = "mycollege.wsgi.application"

# -------------------------------------------------------------------------
# Templates
# -------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "main.context_processors.department_settings",
            ],
        },
    },
]

# -------------------------------------------------------------------------
# Database (SQLite – OK for Render demo)
# -------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -------------------------------------------------------------------------
# Password validation
# -------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------------------------------------------------------------
# Internationalization
# -------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------------
# Static & Media files
# -------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------------------------------------------------------------------------
# Messages framework
# -------------------------------------------------------------------------
MESSAGE_TAGS = {
    messages.DEBUG: "debug",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "error",
}

# -------------------------------------------------------------------------
# Email (dev)
# -------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "cs@university.edu"

# -------------------------------------------------------------------------
# Default PK type
# -------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------------------------
# Security
# -------------------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
]

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# -------------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"}
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# -------------------------------------------------------------------------
# Admin Panel Reordering
# -------------------------------------------------------------------------
ADMIN_REORDER = [
    {"app": "main", "label": "✨ Highlights", "models": [
        "main.HighlightCard",
    ]},
    {"app": "main", "label": "📚 Exams", "models": [
        "main.Exam",
    ]},
    {"app": "main", "label": "🎉 Events", "models": [
        "main.Event",
    ]},
    {"app": "main", "label": "📅 Timetables", "models": [
        "main.ClassTimetable",
    ]},
    {"app": "main", "label": "📰 News", "models": [
        "main.News",
    ]},
    {"app": "main", "label": "👨‍🏫 Staff", "models": [
        "main.StaffProfile",
    ]},
    {"app": "main", "label": "📸 Gallery", "models": [
        "main.GalleryMedia",
    ]},
    {"app": "main", "label": "✉️ Contact", "models": [
        "main.ContactMessage",
    ]},
]
