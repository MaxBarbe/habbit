from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import BaseModel

from backend.database.wardrobe import get_by_id
from backend.services.fashn_tryon import (
    fashn_available,
    generate_outfit_tryon,
)


router = APIRouter(
    prefix="/tryon",
    tags=["tryon"],
)


class TryOnRequest(BaseModel):
    top_id: int
    bottom_id: int
    force: bool = False


@router.get("/health")
def tryon_health():
    return {
        "available": fashn_available(),
    }


@router.post("")
def generate_tryon(request: TryOnRequest):

    if not fashn_available():
        raise HTTPException(
            status_code=503,
            detail="Serveur Try-On indisponible",
        )

    top = get_by_id(request.top_id)
    bottom = get_by_id(request.bottom_id)

    if top is None:
        raise HTTPException(
            status_code=404,
            detail="Haut introuvable",
        )

    if bottom is None:
        raise HTTPException(
            status_code=404,
            detail="Bas introuvable",
        )

    if top.get("categorie") != "haut":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Le vêtement {request.top_id} "
                "n'est pas un haut"
            ),
        )

    if bottom.get("categorie") != "bas":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Le vêtement {request.bottom_id} "
                "n'est pas un bas"
            ),
        )

    outfit = {
        "haut": top,
        "bas": bottom,
    }

    try:
        output_path = generate_outfit_tryon(
            outfit,
            force=request.force,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Génération impossible : {exc}",
        ) from exc

    return {
        "status": "ok",
        "top": top,
        "bottom": bottom,
        "output_path": output_path,
    }
