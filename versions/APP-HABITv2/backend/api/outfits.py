from __future__ import annotations

from fastapi import APIRouter

from backend.services.context_service import get_context
from backend.services.outfit_recommender import recommend_outfits


router = APIRouter(
    prefix="/outfits",
    tags=["outfits"],
)


@router.get("")
def outfits(
    latitude: float,
    longitude: float,
):
    context = get_context(
        latitude=latitude,
        longitude=longitude,
    )

    recommendations = recommend_outfits(
        context=context,
        limit=3,
    )

    return {
        "context": context,
        "count": len(recommendations),
        "outfits": recommendations,
    }
