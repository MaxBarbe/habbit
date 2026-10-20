from __future__ import annotations

from fastapi import APIRouter

from backend.services.context_service import get_context


router = APIRouter(
    prefix="/context",
    tags=["context"],
)


@router.get("")
def context(
    latitude: float,
    longitude: float,
):
    return get_context(
        latitude=latitude,
        longitude=longitude,
    )
