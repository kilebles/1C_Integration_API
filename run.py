from app.main import app
from app.config import Config
import uvicorn

if __name__ == "__main__":
  uvicorn.run(app, host=Config.HOST, port=Config.PORT)