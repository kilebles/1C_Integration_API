from fastapi import APIRouter, HTTPException, Header
from app.config import Config

router = APIRouter()

invoices = {
    "12345": {"id": "12345", "status": "paid", "amount": 1000.0, "date": "2025-01-18"},
}

@router.get("/invoice/{invoice_id}")
async def get_invoice(invoice_id: str, authorization: str = Header(None)):
    print(f"Received Authorization header: {authorization}")  # Для отладки
    expected_token = f"Bearer {Config.API_KEY}"
    if authorization != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    invoice = invoices.get(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return invoice
