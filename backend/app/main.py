from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.config import settings
from app.core.db import engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger
from app.core.middleware import RequestIDMiddleware

OPENAPI_TAGS = [
    {"name": "auth", "description": "Registro, login e refresh/logout de tokens JWT."},
    {"name": "users", "description": "Perfil do usuário autenticado."},
    {"name": "organizations", "description": "Organizações, membros e convites."},
    {"name": "invitations", "description": "Aceite de convites para uma organização."},
    {"name": "projects", "description": "Projetos dentro de uma organização."},
    {"name": "apis", "description": "Catálogo de APIs registradas em um projeto."},
    {"name": "endpoints", "description": "Endpoints registrados em uma API."},
    {"name": "rest-client", "description": "Cliente REST embutido e histórico de requisições."},
    {"name": "docs", "description": "Documentação OpenAPI/Swagger gerada por API registrada."},
    {"name": "dashboard", "description": "Resumo agregado do que o usuário tem acesso."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=settings.rest_client_timeout_seconds)
    logger.info("ApiNest starting up ({} environment)", settings.environment)
    yield
    await app.state.http_client.aclose()
    await engine.dispose()
    logger.info("ApiNest shut down")


app = FastAPI(
    title=settings.app_name,
    description="ApiNest — plataforma de gerenciamento de APIs.",
    version="0.1.0",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}
