import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

from app.utils.logger import setup_logging
from app.endpoints import invoices, tasks, shipments
from app.core.config import Config

logger = logging.getLogger(__name__)
setup_logging(log_level=Config.LOG_LEVEL, log_file="app.log")

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def get_api_key(api_key: str = Depends(api_key_header)):
    print(f"Received Authorization header: {api_key}")  # Для отладки
    if not api_key or api_key != f"Bearer {Config.API_KEY}":
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return api_key

app = FastAPI(
    title="1C API",
    description="REST API",
    version="1.3.0",
)

app.include_router(invoices.router)
app.include_router(tasks.router)
app.include_router(shipments.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def print_ngrok_url():
    logger.info(f"Сервер запущен с: {Config.PUBLIC_URL}")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Введите токен в формате: Bearer <токен>",
        }
    }
    openapi_schema["security"] = [{"APIKeyHeader": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
