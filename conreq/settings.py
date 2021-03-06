"""
Django settings for Conreq project.

Generated by 'django-admin startproject' using Django 3.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import json
import os
import secrets

import requests
from django.core.management.utils import get_random_secret_key

from conreq.utils.generic import get_bool_from_env, get_debug_from_env

# Environment and Project Variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = get_debug_from_env()
DB_ENGINE = os.environ.get("DB_ENGINE", "")
MYSQL_CONFIG_FILE = os.environ.get("MYSQL_CONFIG_FILE", "")
ROTATE_SECRET_KEY = get_bool_from_env("ROTATE_SECRET_KEY", False)
USE_SSL = get_bool_from_env("USE_SSL", False)
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
X_FRAME_OPTIONS = os.environ.get("X_FRAME_OPTIONS", "DENY")


# Application Settings
DJVERSION_VERSION = "0.18.2"
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
SILKY_ANALYZE_QUERIES = True
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_PYTHON_PROFILER_RESULT_PATH = os.path.join(DATA_DIR, "profiling")
if not os.path.exists(SILKY_PYTHON_PROFILER_RESULT_PATH):
    os.makedirs(SILKY_PYTHON_PROFILER_RESULT_PATH)
HTML_MINIFY = True
WHITENOISE_MAX_AGE = 31536000 if not DEBUG else 0
COMPRESS_OUTPUT_DIR = "minified"
COMPRESS_OFFLINE = True
COMPRESS_STORAGE = "compressor.storage.BrotliCompressorFileStorage"
COMPRESS_FILTERS = {
    "css": ["compressor.filters.cssmin.rCSSMinFilter"],
    "js": ["compressor.filters.jsmin.JSMinFilter"],
}
HUEY_STORAGE = os.path.join(DATA_DIR, "background_tasks.sqlite3")
HUEY = {
    "huey_class": "huey.SqliteHuey",  # Huey implementation to use.
    "filename": HUEY_STORAGE,
    "results": False,  # Do not store return values of tasks.
    "store_none": False,  # If a task returns None, do not save to results.
    "immediate": False,  # If True, run tasks synchronously.
    "consumer": {
        "workers": 5,
    },
}
try:
    IPAPI_SUCCESS = requests.get("https://ipapi.co").status_code == 200
except:
    IPAPI_SUCCESS = False


# Logging
LOG_DIR = os.path.join(DATA_DIR, "logs")
CONREQ_LOG_FILE = os.path.join(LOG_DIR, "conreq.log")
ACCESS_LOG_FILE = os.path.join(LOG_DIR, "access.log")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
if DEBUG:
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
else:
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "main": {
            "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
        },
        "minimal": {
            "format": "%(levelname)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "conreq_logs": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "main",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "filename": CONREQ_LOG_FILE,
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "minimal",
        },
        "access_logs": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "main",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "filename": ACCESS_LOG_FILE,
        },
    },
    "root": {
        "handlers": ["console", "conreq_logs"],
        "level": "INFO",
    },
    "loggers": {
        "daphne": {
            "level": "INFO",
            "propagate": True,
        },
        "django": {
            "level": "INFO",
            "propagate": True,
        },
        "django.security.*": {
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "level": "INFO",
            "propagate": True,
        },
        "django.channels.server": {
            "level": "INFO",
            "handlers": ["console", "access_logs"],
            "propagate": False,
        },
        "django.db.backends.schema": {
            "level": LOG_LEVEL,
            "propagate": True,
        },
        "conreq": {
            "level": LOG_LEVEL,
            "propagate": True,
        },
        "conreq.*": {
            "level": LOG_LEVEL,
            "propagate": True,
        },
        "conreq.*.*": {
            "level": LOG_LEVEL,
            "propagate": True,
        },
        "huey": {"level": LOG_LEVEL, "propagate": True},
    },
}


# Security Settings
if ROTATE_SECRET_KEY:
    SECRET_KEY = get_random_secret_key()  # Key used for cryptographic signing
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "no-referrer"
ALLOWED_HOSTS = ["*"]
SECURE_BROWSER_XSS_FILTER = True
if USE_SSL:
    SECURE_SSL_REDIRECT = True  # Redirect HTTP to HTTPS
    SECURE_HSTS_PRELOAD = True  # Allow for HSTS preload
    SECURE_HSTS_SECONDS = 31536000  # Allow for HSTS preload
    SESSION_COOKIE_SECURE = True  # Only send cookie over HTTPS
    CSRF_USE_SESSIONS = True  # Store CSRF token within session cookie
    CSRF_COOKIE_SECURE = True  # Only send cookie over HTTPS
    CSRF_COOKIE_HTTPONLY = True  # Do not allow JS to access cookie
    LANGUAGE_COOKIE_SECURE = True  # Only send cookie over HTTPS
    LANGUAGE_COOKIE_HTTPONLY = True  # Do not allow JS to access cookie


# External "settings.json" file
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
UPDATE_SETTINGS_FILE = False
if not os.path.exists(SETTINGS_FILE):
    # Create the file if it doesn't exist
    with open(SETTINGS_FILE, "w") as settings_file:
        settings_file.write("{}")
with open(SETTINGS_FILE, "r+") as settings_file:
    # Read the file
    settings = json.load(settings_file)
    # Obtain the DB Encryption Key from the file
    if (
        settings.__contains__("DB_ENCRYPTION_KEY")
        and settings["DB_ENCRYPTION_KEY"] is not None
        and settings["DB_ENCRYPTION_KEY"] != ""
    ):
        FIELD_ENCRYPTION_KEYS = [settings["DB_ENCRYPTION_KEY"]]
    # DB Encryption Key wasn't found, a new one is needed
    else:
        FIELD_ENCRYPTION_KEYS = [secrets.token_hex(32)]
        settings["DB_ENCRYPTION_KEY"] = FIELD_ENCRYPTION_KEYS[0]
        UPDATE_SETTINGS_FILE = True
    # Obtain the Secret Key from the file
    if (
        settings.__contains__("SECRET_KEY")
        and settings["SECRET_KEY"] is not None
        and settings["SECRET_KEY"] != ""
        and not ROTATE_SECRET_KEY
    ):
        SECRET_KEY = settings["SECRET_KEY"]
    # New secret key is needed
    elif not ROTATE_SECRET_KEY:
        SECRET_KEY = get_random_secret_key()
        settings["SECRET_KEY"] = SECRET_KEY
        UPDATE_SETTINGS_FILE = True
# Save settings.json if needed
if UPDATE_SETTINGS_FILE:
    with open(SETTINGS_FILE, "w") as settings_file:
        print("Updating settings.json to ", settings)
        settings_file.write(json.dumps(settings))


# Application Definitions
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "conreq.apps.base",
    "conreq.apps.discover",
    "conreq.apps.more_info",
    "conreq.apps.search",
    "conreq.apps.server_settings",
    "conreq.apps.manage_users",
    "conreq.apps.sign_up",
    "conreq.apps.user_requests",
    "conreq.apps.issue_reporting",
    "channels",  # Websocket library
    "encrypted_fields",  # Allow for encrypted text in the DB
    "solo",  # Allow for single-row fields in the DB
    "django_cleanup.apps.CleanupConfig",  # Automatically delete old image files
    "djversion",  # Obtains the git commit as a version number
    "huey.contrib.djhuey",  # Queuing background tasks
    "compressor",  # Minifies CSS/JS files
    "url_or_relative_url_field",  # Validates relative URLs
    "awesome_django_timezones",  # Automatically change timezones
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Serve static files through Django securely
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.http.ConditionalGetMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "htmlmin.middleware.HtmlMinifyMiddleware",  # Compresses HTML files
    "htmlmin.middleware.MarkRequestMiddleware",  # Marks the request as minified
]


# Enabling apps/middleware based on flags
if X_FRAME_OPTIONS.lower() != "false":
    # Block embedding conreq
    MIDDLEWARE.append("django.middleware.clickjacking.XFrameOptionsMiddleware")
if IPAPI_SUCCESS:
    # Automatically change timezones
    MIDDLEWARE.append("awesome_django_timezones.middleware.TimezonesMiddleware")
if not IPAPI_SUCCESS:
    print('Connection to "ipapi.co" has failed. Timezone detection may be impacted.')
if DEBUG:
    # Performance analysis tools
    INSTALLED_APPS.append("silk")
    MIDDLEWARE.append("silk.middleware.SilkyMiddleware")


# URL Routing and Page Rendering
ROOT_URLCONF = "conreq.urls"
ASGI_APPLICATION = "conreq.asgi.application"
WSGI_APPLICATION = "conreq.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "conreq", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# Databases
if DB_ENGINE.upper() == "MYSQL" and MYSQL_CONFIG_FILE != "":
    DATABASES = {
        "default": {  # MySQL
            "ENGINE": "django.db.backends.mysql",
            "OPTIONS": {
                "read_default_file": MYSQL_CONFIG_FILE,
            },
        }
    }
else:
    DATABASES = {
        "default": {  # SQLite
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(DATA_DIR, "db.sqlite3"),
            "OPTIONS": {
                "timeout": 30,
            },
        }
    }
CACHES = {
    "default": {
        "BACKEND": "diskcache.DjangoCache",
        "LOCATION": os.path.join(DATA_DIR, "cache"),
        "TIMEOUT": 300,  # Django setting for default timeout of each key.
        "SHARDS": 8,  # Number of db files to create
        "DATABASE_TIMEOUT": 0.010,  # 10 milliseconds
        "OPTIONS": {"size_limit": 2 ** 30},  # 1 gigabyte
    }
}


# User Authenticaiton
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "pwned_passwords_django.validators.PwnedPasswordsValidator",
        "OPTIONS": {
            "error_message": "Cannot use a compromised password. This password was detected %(amount)d time(s) on 'haveibeenpwned.com'.",
            "help_message": "Your password can't be a compromised password.",
        },
    },
]
LOGIN_REDIRECT_URL = "base:index"
LOGIN_URL = "sign_in"


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static Files (CSS, JavaScript, Images)
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "conreq", "static-dev")]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
