from __future__ import annotations

from backend.version import __version__
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.wardrobe import router as wardrobe_router
from backend.api.context import router as context_router
from backend.api.outfits import router as outfits_router
from backend.api.tryon import router as tryon_router
from backend.database.wardrobe import count_clothes
from backend.services.fashn_tryon import fashn_available


app = FastAPI(
    title="Habbit API",
    version=__version__,
)

app.include_router(wardrobe_router)
app.include_router(context_router)
app.include_router(outfits_router)
app.include_router(tryon_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "app": "Habbit",
        "version": __version__,
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "wardrobe_count": count_clothes(),
        "fashn_available": fashn_available(),
    }
