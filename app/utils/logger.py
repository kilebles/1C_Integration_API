import logging
from app.config import Config

def setup_logging():
  logging.basicConfig(
    level=Config.LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s"
  )