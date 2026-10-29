from .base import *  # noqa

DEBUG = False

if not env("SECRET_KEY", default=""):  # noqa: F405
    raise RuntimeError("SECRET_KEY ortam degiskeni zorunlu")

if not env("DATABASE_URL", default=""):  # noqa: F405
    raise RuntimeError("DATABASE_URL ortam degiskeni zorunlu")

# Render TLS'i load balancer'da sonlandirir
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
DATABASES["default"]["CONN_MAX_AGE"] = 60  # noqa: F405
