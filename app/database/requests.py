from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base, Task
from app.core.config import Config

engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
  Base.metadata.create_all(bind=engine)

def create_task_in_db(session, task_data):
  new_task = Task(**task_data)
  session.add(new_task)
  session.commit()
  session.refresh(new_task)
  return new_task