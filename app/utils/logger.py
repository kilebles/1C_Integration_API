import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "DEBUG", log_file: str = "app.log"):
    log_path = Path(log_file).resolve()

    log_format = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_path, encoding="utf-8")
    ]

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), "DEBUG"),
        format=log_format,
        handlers=handlers,
    )

    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    logging.info(f"Логирование настроено. Уровень: {log_level}, файл: {log_path}")
