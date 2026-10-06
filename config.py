"""
Configuration module for modelScaniTem backend & database.
"""
import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")

# Raw Database URL from environment
RAW_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234@localhost:5432/model_stcan_item"
).strip()

def normalize_db_url(url: str) -> str:
    """
    Normalizes PostgreSQL URL for SQLAlchemy compatibility:
    1. Replaces postgres:// or postgresql:// with postgresql+psycopg2:// (or postgresql+psycopg://)
    2. Handles missing slash between port and database name (e.g. :5432dbname -> :5432/dbname)
    """
    # Detect available driver
    driver_prefix = "postgresql+psycopg2://"
    try:
        import psycopg2
        driver_prefix = "postgresql+psycopg2://"
    except ImportError:
        try:
            import psycopg
            driver_prefix = "postgresql+psycopg://"
        except ImportError:
            driver_prefix = "postgresql+psycopg2://"

    # Fix schema prefix
    if url.startswith("postgres://"):
        url = driver_prefix + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = driver_prefix + url[len("postgresql://"):]

    # Fix port without trailing slash: e.g. localhost:5432model_stcan_item -> localhost:5432/model_stcan_item
    url = re.sub(r':(\d{2,5})([a-zA-Z_][a-zA-Z0-9_]*)', r':\1/\2', url)
    return url

DATABASE_URL = normalize_db_url(RAW_DB_URL)

# Admin authentication defaults
SECRET_KEY = os.getenv("SECRET_KEY", "tool_scanner_secret_key_2026")
ADMIN_DEFAULT_USER = os.getenv("ADMIN_DEFAULT_USER", "admin")
ADMIN_DEFAULT_PASS = os.getenv("ADMIN_DEFAULT_PASS", "admin1234")

# Storage Directories
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "admin_data")
IMAGES_DIR = DATA_DIR / "images"
MODELS_DIR = DATA_DIR / "models"
EXPORTS_DIR = DATA_DIR / "exports"
TRAY_REFS_DIR = DATA_DIR / "tray_refs"

# Ensure required directories exist
for path in [DATA_DIR, IMAGES_DIR, MODELS_DIR, EXPORTS_DIR, TRAY_REFS_DIR]:
    path.mkdir(parents=True, exist_ok=True)
