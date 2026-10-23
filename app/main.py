"""Point d'entrée de l'application FastAPI Colab AI Studio (app/main.py).

Serveur léger orchestrant l'API, les websockets/SSE, les contrôleurs REST
et la distribution des fichiers statiques de la SPA React.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_crud import router as crud_router
from app.config import ensure_directories


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    ensure_directories()
    yield
    # Arrêt propre


app = FastAPI(
    title="Colab AI Studio",
    description="Backend local ultra-léger et tour de contrôle de génération multimédia hybride",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuration CORS pour le développement Vite et les communications locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8190",
        "http://127.0.0.1:8190",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crud_router)


@app.get("/api/health", tags=["Diagnostic"])
async def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "Colab AI Studio Local Backend",
        "version": "1.0.0",
    }
