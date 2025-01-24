import logging
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from app.core.config import Config
from app.database.models import Task, ErrorTask
from app.database.requests import SessionLocal, create_task_in_db, move_task_to_error, restore_task_from_error

router = APIRouter()
logger = logging.getLogger(__name__)

class TaskRequest(BaseModel):
    document_type: str = Field(
        ...,
        example="Cчет",
        description="Тип документа (например, счет)"
    )
    bin: str = Field(
        ...,
        example="123456789012",
        description="БИН контрагента"
    )
    name: str = Field(
        ...,
        example="Тестовое задание",
        description="Название задания"
    )
    quantity: float = Field(
        ...,
        example=10.5,
        description="Кол-во товара или услуг"
    )
    price: float = Field(
        ..., 
        example=1500.0, 
        description="Цена за единицу товара или услуги"
    )


class RetryTaskRequest(BaseModel):
    ид_задачи: int = Field(
        ..., 
        example=1, 
        description="Идентификатор задания для восстановления"
    )
    бин_пользователя: str = Field(
        ..., 
        example="987654321098", 
        description="БИН пользователя"
    )
    тип_документа: str = Field(
        ..., 
        example="Cчет", 
        description="Тип документа (например, счет)"
    )
    бин_контрагента: str = Field(
        ..., 
        example="123456789012", 
        description="БИН контрагента"
    )
    название: str = Field(
        ..., 
        example="Исправленное задание", 
        description="Название задания"
    )
    количество: float = Field(
        ..., 
        example=5.0, 
        description="Количество товара или услуг"
    )
    цена: float = Field(
        ..., 
        example=1000.0, 
        description="Цена за единицу товара или услуги"
    )

class TaskResultRequest(BaseModel):
    ид_задачи: int = Field(
        ..., 
        example=1, 
        description="Идентификатор задания"
    )
    статус: str = Field(
        ..., 
        example="успех", 
        description="Статус выполнения задания ('успех' или 'ошибка')"
    )
    причина_ошибки: str = Field(
        default="", 
        example="Контрагент не найден", 
        description="Причина ошибки (обязательно, если статус = 'ошибка')"
    )
    
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/tasks",
    tags=["Задания"],
    summary="Создание нового задания",
    description="""
        Этот эндпоинт позволяет создать новое задание
        """
    )
async def create_task(
    data: TaskRequest,
    authorization: str = Header(None),
    user_bin: str = Header(None),
    db: Session = Depends(get_db)
):
    logger.info(f"Получен запрос на создание задания: {data}, User-Bin: {user_bin}")

    expected_token = f"Bearer {Config.API_KEY}"
    if authorization != expected_token:
        logger.error("Ошибка авторизации")
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    if not user_bin:
        raise HTTPException(status_code=400, detail="Не указан БИН пользователя")
    

    task_data = data.model_dump()
    task_data["user_bin"] = user_bin
    task_data["counterparty_bin"] = task_data.pop("bin")  # Переименовываем поле

    try:
        task = create_task_in_db(db, task_data)
    except Exception as e:
        logger.error(f"Ошибка при сохранении задания: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении задания")
    
    logger.info(f"Задание успешно обработано для пользователя с БИН {user_bin}")
    return {"task_id": task.id}


@router.post(
    "/tasks/result",
    tags=["Задания"],
    summary="Результат задания из 1С",
    description="""
        Этот эндпоинт позволяет отправить задание в 'Ошибочные', если статус: 'ошибка',
        или удалить задание, если статус: 'успех'
        """
    )
async def process_task_result(
    data: TaskResultRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    logger.info(f"Получен результат выполнения задачи: {data}")

    expected_token = f"Bearer {Config.API_KEY}"
    if authorization != expected_token:
        logger.error("Ошибка авторизации")
        raise HTTPException(status_code=401, detail="Не авторизован")

    status_mapping = {
        "успех": True,
        "ошибка": False
    }

    task_id = data.ид_задачи
    status = status_mapping.get(data.статус)
    error_reason = data.причина_ошибки or ""

    if status is None:
        logger.error("Некорректное значение для статуса")
        raise HTTPException(status_code=400, detail="Некорректное значение для статуса")

    if status and error_reason:
        logger.warning("Причина ошибки указана, но статус задачи 'успех'")
        error_reason = ""

    if not status and not error_reason:
        error_reason = "Нет ошибок"

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
        logger.error(f"Ошибка при перемещении задачи в таблицу ошибок: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при обработке задачи")



@router.post(
    "/tasks/retry",
    tags=["Задания"],
    summary="Восстановление задания 1С",
    description="""
        Этот эндпоинт позволяет восстановить задание из 'Ошибочных'
        """
    )
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
    
    mapped_data = data.model_dump()

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


