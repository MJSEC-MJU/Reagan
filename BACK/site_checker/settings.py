from pathlib import Path
import os

# ─────────────────────────────────────────────────────────────
# 기본 경로
# ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────
# 보안·환경 변수
# ─────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,reagan.mjsec.kr",
).split(",")

# ─────────────────────────────────────────────────────────────
# 애플리케이션
# ─────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    # 3rd-party
    "corsheaders",
    "rest_framework",

    # Django 기본
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 로컬 앱
    "analysis",

]

# ─────────────────────────────────────────────────────────────
# 미들웨어  (CorsMiddleware가 CommonMiddleware보다 ↑)
# ─────────────────────────────────────────────────────────────
MIDDLEWARE = [

    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "site_checker.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "site_checker.wsgi.application"

# ─────────────────────────────────────────────────────────────
# 데이터베이스 : DEBUG → SQLite / 운영 → PostgreSQL 예시
# ─────────────────────────────────────────────────────────────
if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.getenv("DB_HOST", "db"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "NAME": os.getenv("DB_NAME", "reagan"),
            "USER": os.getenv("DB_USER", "reagan"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
        }
    }

# ─────────────────────────────────────────────────────────────
# 비밀번호 검증
# ─────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─────────────────────────────────────────────────────────────
# 국제화 / 시간대
# ─────────────────────────────────────────────────────────────
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ   = True          # DB엔 UTC, 코드에선 KST

# ─────────────────────────────────────────────────────────────
# 정적·미디어 파일
# ─────────────────────────────────────────────────────────────
STATIC_URL  = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL   = "media/"
MEDIA_ROOT  = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─────────────────────────────────────────────────────────────
# CORS / CSRF
# ─────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^chrome-extension://[a-z]{32}$",       # 모든 MV3 확장 (운영용일 땐 ID 하나로 좁혀도 됨)
    r"^https://reagan\.mjsec\.kr$",
    r"^http://localhost:3000$",
]
CORS_ALLOW_CREDENTIALS = False
CORS_ALLOW_HEADERS     = ["content-type"]
CORS_ALLOW_METHODS     = ["GET", "POST", "OPTIONS"]

CSRF_TRUSTED_ORIGINS = [
    "https://reagan.mjsec.kr"
]

# ─────────────────────────────────────────────────────────────
# Django REST framework
# ─────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
}

# ─────────────────────────────────────────────────────────────
# 로깅 (콘솔 출력 중심)
# ─────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {
        "handlers": ["console"],
        "level": "INFO" if DEBUG else "WARNING",
    },
}