import logging
from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from app.core.config import Config
from app.database.requests import SessionLocal, add_products_to_shipment, create_shipment_in_db
from pydantic import BaseModel, Field
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter()

class Product(BaseModel):
  tovar_name: str = Field(
    ..., 
    example="Ноутбук", 
    description="Название товара"
  )
  tovar_count: int = Field(
    ..., 
    example=1, 
    description="Количество товара"
  )
  tovar_price: float = Field(
    ..., 
    example=150000.0, 
    description="Цена за единицу товара"
  )
    

class ShipmentsRequest(BaseModel):
  contragent_bin: str = Field(
    ..., 
    example="123456789012", 
    description="БИН контрагента"
  )
  dct_type: str = Field(
    ..., 
    example="invoice", 
    description="Тип документа, связанного с отгрузкой (например, счет)"
  )
  products: List[Product] = Field(
    ..., 
    example=[
      {
          "tovar_name": "Ноутбук",
          "tovar_count": 1,
          "tovar_price": 150000.0
      },
      {
          "tovar_name": "Мышь",
          "tovar_count": 2,
          "tovar_price": 5000.0
      }
    ],
    description="Список товаров, входящих в отгрузку"
  )


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

@router.post(
  "/shipments",
  tags=["Товары"],
  summary="Создание нового товара",
  description="Этот эндпоинт создает новый товар"
  )
async def create_shipment(
  shipment: ShipmentsRequest,
  authorization: str = Header(None),
  user_bin: str = Header(None),
  db: Session = Depends(get_db)
):
  logger.info(f"Получен запрос на создание отгрузки {shipment}")

  expected_token = f"Bearer {Config.API_KEY}"
  if authorization != expected_token:
      logger.error("Ошибка авторизации")
      raise HTTPException(status_code=401, detail="Не авторизован")
  
  if not user_bin:
      logger.error("Не указан БИН пользователя")
      raise HTTPException(status_code=400, detail="Не указан БИН пользователя")
  
  try:
      shipment_data = {
          "user_bin": user_bin,
          "contragent_bin": shipment.contragent_bin,
          "dct_type": shipment.dct_type
      }

      new_shipment = create_shipment_in_db(db, shipment_data)
      logger.info(f"Отгрузка создана с ID {new_shipment.id}")
      
      add_products_to_shipment(db, new_shipment.id, shipment.products)
      logger.info(f"Добавлено товаров: {len(shipment.products)} для отгрузки ID {new_shipment.id}")
      
      return {"shipment_id": new_shipment.id}
  except Exception as e:
      logger.error(f"Ошибка при обработке отгрузки: {e}", exc_info=True)
      raise HTTPException(status_code=500, detail="Ошибка при обработке отгрузки")
