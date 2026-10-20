from __future__ import annotations

from pathlib import Path
import traceback
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from backend.database.wardrobe import (
    count_clothes,
    get_all_clothes,
    get_by_id,
)

from backend.services.wardrobe_pipeline import (
    analyze_and_save,
)


# ============================================================
# CONFIG
# ============================================================

APP_ROOT = Path(__file__).resolve().parents[2]

ORIGINALS_DIR = (
    APP_ROOT
    / "backend"
    / "storage"
    / "originals"
)

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/wardrobe",
    tags=["wardrobe"],
)


# ============================================================
# GET - DRESSING COMPLET
# ============================================================

@router.get("")
def wardrobe():
    clothes = get_all_clothes()

    return {
        "count": len(clothes),
        "clothes": clothes,
    }


# ============================================================
# GET - NOMBRE DE VÊTEMENTS
# ============================================================

@router.get("/count")
def wardrobe_count():
    return {
        "count": count_clothes(),
    }


# ============================================================
# GET - UN VÊTEMENT
# ============================================================

@router.get("/{clothing_id}")
def wardrobe_item(clothing_id: int):
    clothing = get_by_id(clothing_id)

    if clothing is None:
        raise HTTPException(
            status_code=404,
            detail="Vêtement introuvable",
        )

    return clothing


# ============================================================
# POST - AJOUT AUTOMATIQUE
# ============================================================

@router.post("")
async def add_clothing(
    file: UploadFile = File(...),
):
    # --------------------------------------------------------
    # Vérification du fichier
    # --------------------------------------------------------

    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Format non supporté. "
                "Utilise JPG, JPEG, PNG ou WEBP."
            ),
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Le fichier envoyé est vide.",
        )

    # --------------------------------------------------------
    # Stockage temporaire dans originals
    # --------------------------------------------------------

    ORIGINALS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        ORIGINALS_DIR
        / f"{uuid4().hex}{extension}"
    )

    destination.write_bytes(content)

    # --------------------------------------------------------
    # Pipeline
    #
    # 1. Hash / mémoire
    # 2. BiRefNet
    # 3. FashionCLIP
    # 4. Attributs
    # 5. Sauvegarde BDD
    # --------------------------------------------------------

    try:
        result = analyze_and_save(
            destination
        )

    except Exception as exc:
        print("\n" + "=" * 60)
        print("[API] ERREUR POST /wardrobe")
        print("=" * 60)
        traceback.print_exc()
        print("=" * 60 + "\n")

        destination.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Analyse automatique du vêtement "
                f"impossible : {exc}"
            ),
        ) from exc

    # --------------------------------------------------------
    # ANTI-DOUBLON
    # --------------------------------------------------------

    if result.get("source") == "database":

        clothing = result.get(
            "clothing",
            {},
        )

        original_path = clothing.get(
            "original_path"
        )

        # Le pipeline a retrouvé un vêtement existant.
        # On supprime donc la nouvelle copie uploadée.
        if original_path:

            existing_original = Path(
                original_path
            )

            if not existing_original.is_absolute():
                existing_original = (
                    APP_ROOT
                    / existing_original
                )

            try:
                if (
                    destination.resolve()
                    != existing_original.resolve()
                ):
                    destination.unlink(
                        missing_ok=True
                    )
            except OSError:
                pass

        else:
            destination.unlink(
                missing_ok=True
            )

    # --------------------------------------------------------
    # RÉSULTAT
    # --------------------------------------------------------

    return result
