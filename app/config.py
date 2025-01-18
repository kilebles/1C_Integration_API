import os
from dotenv import load_dotenv

load_dotenv()

class Config:
  HOST = os.getenv("APP_HOST", "127.0.0.1")
  PORT = int(os.getenv("APP_PORT", 8000))
  API_KEY = os.getenv("API_KEY", "default_api_key")
  LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
  PUBLIC_URL = os.getenv("PUBLIC_URL", f"http://{HOST}:{PORT}")