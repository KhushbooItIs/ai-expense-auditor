from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

# SQLite locally — zero setup, works with all Django features including JSONField
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Disable WhiteNoise compression in dev (faster reloads)
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Print emails to console instead of sending them
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable rate limiting so repeated test submits don't 403
RATELIMIT_ENABLE = False
