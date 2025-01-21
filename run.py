import uvicorn
from app.core.main import app
from app.core.config import Config
from app.database.requests import init_db

if __name__ == "__main__":
  init_db()
  uvicorn.run(app, host=Config.HOST, port=Config.PORT)