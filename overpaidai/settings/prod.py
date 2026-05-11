from .base import *
import dj_database_url

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# Render injects DATABASE_URL automatically when a Postgres DB is attached
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,         # reuse DB connections for 10 min (important on free tier)
        conn_health_checks=True,  # drop stale connections automatically
    )
}

# Security headers — enforce HTTPS, prevent clickjacking
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Render handles SSL termination; trust X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
