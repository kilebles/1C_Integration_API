import logging
from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from app.core.config import Config
from app.database.models import Task
from app.database.requests import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@router.get(
    "/tasks/{task_id}",
    tags=["Задания"],
    summary="Получить задание по ID 1С",
    description="Этот эндпоинт позволяет получить данные о задании"
    )
async def get_task(
    task_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    logger.info(f"Запрос на получение задания ID {task_id}")
    
    excepted_token = f"Bearer {Config.API_KEY}"
    if authorization != excepted_token:
        logger.warning("Неавторизованный доступ")
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        logger.error(f"Задание с ID {task_id} не найдено")
        raise HTTPException(status_code=404, detail="Задание не найдено")
    
    logger.info(f"Задание с ID {task_id} успешно получено")
    
    return {
        "идентификатор": task.id,
        "бин_пользователя": task.user_bin,
        "тип_документа": task.document_type,
        "бин_контрагента": task.counterparty_bin,
        "наименование": task.name,
        "количество": task.quantity,
        "цена": task.price,
        "создано": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }