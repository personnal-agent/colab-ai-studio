"""Point d'entrée de l'application FastAPI Colab AI Studio (app/main.py).

Serveur léger orchestrant l'API, les websockets/SSE, les contrôleurs REST
et la distribution des fichiers statiques de la SPA React.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes_config import router as config_router
from app.api.routes_crud import router as crud_router
from app.api.routes_generation import router as generation_router
from app.api.routes_llm_proxy import router as llm_proxy_router
from app.api.routes_models import get_worker_gateway
from app.api.routes_models import router as models_router
from app.config import ensure_directories
from app.services.worker_gateway import WorkerGateway
from app.storage.json_store import CorruptedDocumentStoreError


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    ensure_directories()
    yield
    # Arrêt propre
    gateway = get_worker_gateway()
    await gateway.aclose()


app = FastAPI(
    title="Colab AI Studio",
    description="Backend local ultra-léger et tour de contrôle de génération multimédia hybride",
    version="1.0.0",
    lifespan=lifespan,
)

_ORIGINS = [f"http://{h}:{p}" for h in ("localhost", "127.0.0.1") for p in (5173, 8000, 8190)]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(CorruptedDocumentStoreError)
async def corrupted_store_exception_handler(
    request: Request, exc: CorruptedDocumentStoreError
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Stockage de données corrompu : {exc}"},
    )


app.include_router(crud_router)
app.include_router(models_router)
app.include_router(config_router)
app.include_router(generation_router)
app.include_router(llm_proxy_router)


@app.get("/api/health", tags=["Diagnostic"])
async def health_check(
    gateway: WorkerGateway = Depends(get_worker_gateway),
) -> dict[str, Any]:
    worker_health = await gateway.health()
    return {
        "status": "healthy",
        "service": "Colab AI Studio Local Backend",
        "version": "1.0.0",
        **worker_health,
    }
