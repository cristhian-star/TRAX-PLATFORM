import os
from datetime import timedelta


_TRUE_VALUES = {"1", "true", "yes", "on"}
_PRODUCTION_VALUES = {"production", "prod"}
_DEVELOPMENT_VALUES = {"development", "dev", "local"}
_TESTING_VALUES = {"testing", "test"}
_INSECURE_SECRET_VALUES = {
    "dev-only-insecure-secret-key",
    "tu_clave_aqui",
    "changeme",
    "change-me",
    "secret",
    "password",
}


def _env(name, default=None):
    value = os.environ.get(name)
    if value is None:
        return default

    return value.strip()


def _env_bool(name, default=False):
    value = _env(name)
    if value is None:
        return default

    return value.lower() in _TRUE_VALUES


def current_environment():
    value = (
        _env("APP_ENV")
        or _env("FLASK_ENV")
        or _env("TRAX_ENV")
        or "development"
    )
    return value.lower()


class Config:
    ENV_NAME = "base"
    TESTING = False
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_REFRESH_EACH_REQUEST = False
    REGISTER_DEV_ROUTES = False
    ALLOW_SCHEMA_CREATE_ALL = False
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 1024 * 1024
    MAX_FORM_MEMORY_SIZE = 1024 * 1024
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_HEADERS_ENABLED = True
    MEDIA_STORAGE_PROVIDER = "local"
    LOCAL_MEDIA_UPLOAD_ROOT = "app/static/uploads/professional_media"
    LOCAL_MEDIA_PUBLIC_BASE_URL = "/static/uploads/professional_media"
    CLOUDINARY_FOLDER = "trax/professional_media"
    MEDIA_AUTO_PUBLISH = True

    REQUIRED_ENV_VARS = ()

    @classmethod
    def validate(cls):
        missing = [name for name in cls.REQUIRED_ENV_VARS if not _env(name)]
        if missing:
            raise RuntimeError(
                "Faltan variables de entorno obligatorias: "
                + ", ".join(sorted(missing))
            )

    @classmethod
    def apply_runtime_config(cls, app_config):
        app_config["SECRET_KEY"] = _env("SECRET_KEY") or "dev-only-insecure-secret-key"
        app_config["SQLALCHEMY_DATABASE_URI"] = _env("DATABASE_URL") or "sqlite:///trax.db"
        app_config["MAX_CONTENT_LENGTH"] = int(_env("MAX_CONTENT_LENGTH_BYTES", str(cls.MAX_CONTENT_LENGTH)))
        app_config["MAX_FORM_MEMORY_SIZE"] = int(_env("MAX_FORM_MEMORY_SIZE_BYTES", str(cls.MAX_FORM_MEMORY_SIZE)))
        app_config["RATELIMIT_STORAGE_URI"] = _env("RATELIMIT_STORAGE_URI") or cls.RATELIMIT_STORAGE_URI
        app_config["MEDIA_STORAGE_PROVIDER"] = (_env("MEDIA_STORAGE_PROVIDER") or cls.MEDIA_STORAGE_PROVIDER).lower()
        app_config["LOCAL_MEDIA_UPLOAD_ROOT"] = _env("LOCAL_MEDIA_UPLOAD_ROOT") or cls.LOCAL_MEDIA_UPLOAD_ROOT
        app_config["LOCAL_MEDIA_PUBLIC_BASE_URL"] = _env("LOCAL_MEDIA_PUBLIC_BASE_URL") or cls.LOCAL_MEDIA_PUBLIC_BASE_URL
        app_config["CLOUDINARY_CLOUD_NAME"] = _env("CLOUDINARY_CLOUD_NAME")
        app_config["CLOUDINARY_API_KEY"] = _env("CLOUDINARY_API_KEY")
        app_config["CLOUDINARY_API_SECRET"] = _env("CLOUDINARY_API_SECRET")
        app_config["CLOUDINARY_FOLDER"] = _env("CLOUDINARY_FOLDER") or cls.CLOUDINARY_FOLDER
        app_config["MEDIA_AUTO_PUBLISH"] = _env_bool("MEDIA_AUTO_PUBLISH", cls.MEDIA_AUTO_PUBLISH)


class DevelopmentConfig(Config):
    ENV_NAME = "development"
    REGISTER_DEV_ROUTES = True

    @classmethod
    def apply_runtime_config(cls, app_config):
        super().apply_runtime_config(app_config)
        app_config["DEBUG"] = _env_bool("FLASK_DEBUG", False)
        app_config["ALLOW_SCHEMA_CREATE_ALL"] = _env_bool("ALLOW_DEV_CREATE_ALL", False)


class TestingConfig(Config):
    ENV_NAME = "testing"
    TESTING = True
    WTF_CSRF_ENABLED = False
    ALLOW_SCHEMA_CREATE_ALL = True

    @classmethod
    def apply_runtime_config(cls, app_config):
        app_config["SECRET_KEY"] = _env("SECRET_KEY") or "test-secret-key"
        app_config["SQLALCHEMY_DATABASE_URI"] = _env("DATABASE_URL") or "sqlite:///:memory:"


class ProductionConfig(Config):
    ENV_NAME = "production"
    SESSION_COOKIE_SECURE = True
    REQUIRED_ENV_VARS = ("SECRET_KEY", "DATABASE_URL")

    @classmethod
    def validate(cls):
        super().validate()
        if (_env("SECRET_KEY") or "").strip().lower() in _INSECURE_SECRET_VALUES:
            raise RuntimeError("SECRET_KEY de desarrollo no permitido en produccion")

    @classmethod
    def apply_runtime_config(cls, app_config):
        super().apply_runtime_config(app_config)
        app_config["SECRET_KEY"] = _env("SECRET_KEY")
        app_config["SQLALCHEMY_DATABASE_URI"] = _env("DATABASE_URL")


def get_config_class(environment=None):
    environment = (environment or current_environment()).lower()

    if environment in _PRODUCTION_VALUES:
        return ProductionConfig
    if environment in _TESTING_VALUES:
        return TestingConfig
    if environment in _DEVELOPMENT_VALUES:
        return DevelopmentConfig

    return DevelopmentConfig
