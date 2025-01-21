import logging
from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from app.core.config import Config
from app.database.models import Task
from app.database.requests import SessionLocal, create_task_in_db

router = APIRouter()
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/tasks")
async def create_task(
    data: dict, 
    authorization: str = Header(None),
    user_bin: str = Header(None),
    db: Session = Depends(get_db)
):
    logger.info(f"Получен запрос на создание задания: {data}, User-Bin: {user_bin}")
    
    expected_token = f"Bearer {Config.API_KEY}"
    
    if authorization != expected_token:
        logger.error("Не указан User-Bin в заголовке")
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    if not user_bin:
        raise HTTPException(status_code=400, detail="Не указан БИН пользователя")
    
    task_data = {
        "user_bin": user_bin,
        "document_type": data.get("document_type"),
        "counterparty_bin": data.get("bin"),
        "name": data.get("name"),
        "quantity": data.get("quantity"),
        "price": data.get("price"),
    }
    
    try:
        task = create_task_in_db(db, task_data)
    except Exception  as e:
        logger.error("Ошибка при сохранении задания: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении задания")
        
    logger.info(f"Задание успешно обработано для пользователя с БИН {user_bin}")

    return {
        "message": "Задание успешно создано",
        "task_id": task.id,
        "created_at": task.created_at
    }
    