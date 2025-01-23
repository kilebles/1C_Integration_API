import logging
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from app.core.config import Config
from app.database.models import Task, ErrorTask
from app.database.requests import SessionLocal, create_task_in_db, move_task_to_error, restore_task_from_error

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


@router.post("/tasks/result")
async def process_task_result(
    data: dict,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    logger.info(f"Получен результат выполнения задачи: {data}")
    
    excepted_token = f"Bearer {Config.API_KEY}"
    
    if authorization != excepted_token:
        logger.error("Ошибка авторизации")
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    field_mapping = {
        "ид_задачи": "task_id",
        "статус": "status",
        "причина_ошибки": "error_reason"
    }
    mapped_data = {field_mapping.get(k, k): v for k, v in data.items()}
    
    status_mapping = {
        "успех": True,
        "ошибка": False
    }
    
    task_id = mapped_data.get("task_id")
    status = status_mapping.get(mapped_data.get("status")) 
    error_reason = mapped_data.get("error_reason", "")
    
    if status is None:
        logger.error("Некорректное значение для статуса")
        raise HTTPException(status_code=400, detail="Некорректное значение для статуса")
    
    if status and error_reason:
        logger.warning("Причина ошибки указана, но статус задачи 'успех'")
        error_reason = ""
        
    if status and not error_reason:
        error_reason = "Нет ошибок"
    
    if task_id is None or status is None:
        logger.error("Некорректные данные в запросе: отсутствует идентификатор или статус")
        raise HTTPException(status_code=400, detail="Некорректные данные: 'ид_задачи' и 'статус' обязательны")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        logger.error(f"Задача с ID {task_id} не найдена")
        raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")
    
    if status:  
        db.delete(task)
        db.commit()
        logger.info(f"Задача с ID {task_id} успешно завершена и удалена")
        return {"message": f"Задача с ID {task_id} успешно завершена"}
    

    try:
        move_task_to_error(db, task_id, error_reason)
        logger.info(f"Задача с ID {task_id} перемещена в таблицу ошибок")
        return {"message": f"Задача с ID {task_id} перемещена в таблицу ошибок"}
    except Exception as e:
        logger.error(f"Ошибка при перемещении задачи в таблицу ошибок: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обработке задачи")


class RetryTaskRequest(BaseModel):
    ид_задачи: int
    бин_пользователя: str
    тип_документа: str
    бин_контрагента: str
    название: str
    количество: float
    цена: float
    
@router.post("/tasks/retry")
async def retry_task(
    data: RetryTaskRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    logger.info(f"Получен запрос на восстановление задачи {data}")
    
    expected_token = f"Bearer {Config.API_KEY}"
    if authorization != expected_token:
        logger.error("Ошибка авторизации")
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    mapped_data = data.dict()

    task_id = mapped_data.get("ид_задачи")
    
    if not task_id:
        logger.error("Некорректные данные")
        raise HTTPException(status_code=400, detail="Некорректные данные: task_id обязателен")

    try:
        restored_task = restore_task_from_error(
            db, 
            task_id=task_id,
            user_bin=mapped_data.get("бин_пользователя"),
            document_type=mapped_data.get("тип_документа"),
            counterparty_bin=mapped_data.get("бин_контрагента"),
            name=mapped_data.get("название"),
            quantity=mapped_data.get("количество"),
            price=mapped_data.get("цена")
        )
        logger.info(f"Задача с ID {task_id} успешно восстановлена")
        return {"message": f"Задача с ID {task_id} успешно восстановлена", "restored_task": restored_task.id}
    except ValueError as e:
        logger.error(f"Ошибка восстановления задачи: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при восстановлении задачи: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при восстановлении задачи")