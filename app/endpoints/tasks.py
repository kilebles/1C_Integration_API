import logging
from fastapi import APIRouter, HTTPException, Header
from app.config import Config

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/tasks")
async def create_task(
    data: dict, 
    authorization: str = Header(None),
    user_bin: str = Header(None)
):
    logger.info(f"Получен запрос на создание задания: {data}, User-Bin: {user_bin}")
    
    expected_token = f"Bearer {Config.API_KEY}"
    
    if authorization != expected_token:
        logger.error("Не указан User-Bin в заголовке")
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    if not user_bin:
        raise HTTPException(status_code=400, detail="Не указан БИН пользователя")
    
    logger.info(f"Задание успешно обработано для пользователя с БИН {user_bin}")
    
    return {
        "message": "Задание успешно создано",
        "данные": "data"
    }
    