from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class Task(Base):
  __tablename__ = "tasks"
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  user_bin = Column(String(12), nullable=False)
  document_type = Column(String(100), nullable=False)
  counterparty_bin = Column(String(12), nullable=False)
  name = Column(String(100), nullable=False)
  quantity = Column(Float, nullable=False)
  price = Column(Float, nullable=False)
  created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
  
class ErrorTask(Base):
  __tablename__ = "error_tasks"
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  task_id = Column(Integer, nullable=False)
  error_reason = Column(Text, nullable=False)
  created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
class Shipment(Base):
  __tablename__ = "shipments"
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  user_bin = Column(String(12), nullable=False)
  contragent_bin = Column(String(50), nullable=False)
  dct_type = Column(String(50), nullable=False)
  created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
  
class ShipmentProduct(Base):
  __tablename__ = "shipment_products"
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
  tovar_name = Column(String(100), nullable=False)
  tovar_count = Column(Integer, nullable=False)
  tovar_price = Column(Float, nullable=False)