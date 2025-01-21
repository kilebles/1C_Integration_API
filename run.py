from app.core.main import app
from app.core.config import Config
import uvicorn

if __name__ == "__main__":
  uvicorn.run(app, host=Config.HOST, port=Config.PORT)