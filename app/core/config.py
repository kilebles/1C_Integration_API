import os
from dotenv import load_dotenv

load_dotenv()

class Config:
  HOST = os.getenv("APP_HOST", "127.0.0.1")
  PORT = int(os.getenv("APP_PORT", 8000))
  API_KEY = os.getenv("API_KEY", "default_api_key")
  LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
  PUBLIC_URL = os.getenv("PUBLIC_URL", f"http://{HOST}:{PORT}")
  
  DB_HOST = os.getenv("DB_HOST", "localhost")
  DB_PORT = int(os.getenv("DB_PORT", 5432))
  DB_NAME = os.getenv("DB_NAME","default_db")
  DB_USER = os.getenv("DB_USER", "default_user")
  DB_PASSWORD = os.getenv("DB_PASSWORD", "default_password")
  DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
  )
  