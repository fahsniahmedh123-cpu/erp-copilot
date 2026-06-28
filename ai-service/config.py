import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "finance_dev")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

FINANCE_API_BASE_URL = os.getenv("FINANCE_API_BASE_URL", "")
FINANCE_API_TOKEN = os.getenv("FINANCE_API_TOKEN", "")

APP_ENV = os.getenv("APP_ENV", "development")
APP_PORT = int(os.getenv("APP_PORT", "8000"))