from fastapi import APIRouter, HTTPException, Header
from app.config import Config

router = APIRouter()

@router.post("/reference")
async def upload_reference(data: dict, authorization: str = Header(None)):
    print(f"Received Authorization header: {authorization}")  # Для отладки
    expected_token = f"Bearer {Config.API_KEY}"
    if authorization != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {"message": "Reference uploaded successfully", "data": data}
