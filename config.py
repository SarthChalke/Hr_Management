import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


def _normalize_db_url(url: str) -> str:
    """Some hosts (Heroku/Render style) hand out postgres:// URLs.
    SQLAlchemy 2.x / psycopg3 need postgresql:// or postgresql+psycopg://
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    APP_NAME = os.environ.get("APP_NAME", "AI HR & Employee Management Portal")

    RAW_DATABASE_URL = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:1234@localhost:5432/hr_portal"
    )
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(RAW_DATABASE_URL)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB uploads

    WTF_CSRF_ENABLED = True
