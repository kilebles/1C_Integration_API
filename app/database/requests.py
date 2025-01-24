from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base, Task, ErrorTask, Shipment, ShipmentProduct
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


def move_task_to_error(session, task_id, error_reason):
  task = session.query(Task).filter(Task.id == task_id).first()
  if not task:
    raise ValueError(f"Задание с ID {task_id} не найдено")
  
  error_task = ErrorTask(
    task_id=task.id,
    error_reason=error_reason
  )
  session.add(error_task)
  session.delete(task)
  session.commit()
  return error_task


def restore_task_from_error(session, task_id, user_bin, document_type, counterparty_bin, name, quantity, price):
  error_task = session.query(ErrorTask).filter(ErrorTask.task_id == task_id).first()
  if not error_task:
    raise ValueError(f"Задание с ID {task_id} не найдено")
  
  restored_task = Task(
    id=error_task.task_id,
    user_bin=user_bin,
    document_type=document_type,
    counterparty_bin=counterparty_bin,
    name=name,
    quantity=quantity,
    price=price,
  )
  session.add(restored_task)
  session.delete(error_task)
  session.commit()
  return restored_task


def create_shipment_in_db(session, shipment_data):
  new_shipment = Shipment(
    user_bin=shipment_data["user_bin"],
    contragent_bin=shipment_data["contragent_bin"],
    dct_type=shipment_data["dct_type"],
  )
  session.add(new_shipment)
  session.commit()
  session.refresh(new_shipment)
  return new_shipment


def add_products_to_shipment(session, shipment_id, products):
    for product in products:
        new_product = ShipmentProduct(
            shipment_id=shipment_id,
            tovar_name=product.tovar_name,
            tovar_count=product.tovar_count,
            tovar_price=product.tovar_price,
        )
        session.add(new_product)
    session.commit()