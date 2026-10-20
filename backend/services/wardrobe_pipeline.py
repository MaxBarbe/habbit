from __future__ import annotations

from pathlib import Path

from backend.database.wardrobe import (
    calculate_file_hash,
    get_by_hash,
    save_clothing,
)

from backend.services.background_removal import (
    remove_background_file,
)

from backend.services.clothing_recognition import (
    recognize_clothing,
)

from backend.services.clothing_attributes import (
    analyze_attributes,
)


APP_ROOT = Path(__file__).resolve().parents[2]

CUTOUT_DIR = (
    APP_ROOT
    / "backend"
    / "storage"
    / "cutouts"
)


def analyze_and_save(
    image_path: str | Path,
) -> dict:

    image_path = Path(image_path).resolve()

    # ========================================================
    # VERIFICATION
    # ========================================================

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image introuvable : {image_path}"
        )

    if not image_path.is_file():
        raise ValueError(
            f"Le chemin n'est pas un fichier : {image_path}"
        )

    # ========================================================
    # HASH / MEMOIRE
    # ========================================================

    image_hash = calculate_file_hash(
        image_path
    )

    existing = get_by_hash(
        image_hash
    )

    if existing is not None:

        print()
        print("=" * 60)
        print("[WARDROBE] Vêtement déjà connu")
        print("[WARDROBE] Analyse IA ignorée")
        print(f"[WARDROBE] ID : {existing.get('id')}")
        print("=" * 60)
        print()

        return {
            "source": "database",
            "clothing": existing,
        }

    # ========================================================
    # CUTOUT
    # ========================================================

    CUTOUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    cutout_path = (
        CUTOUT_DIR
        / f"{image_hash[:16]}.png"
    )

    # ========================================================
    # DETOURAGE
    # ========================================================

    print()
    print("=" * 60)
    print("[WARDROBE] Nouveau vêtement")
    print("[WARDROBE] Détourage...")
    print("=" * 60)
    print()

    remove_background_file(
        image_path,
        cutout_path,
    )

    if not cutout_path.exists():
        raise RuntimeError(
            "Le détourage n'a pas produit de fichier."
        )

    # ========================================================
    # RECONNAISSANCE
    # ========================================================

    print()
    print("[WARDROBE] Reconnaissance...")
    print()

    clothing = recognize_clothing(
        cutout_path
    )

    if not isinstance(clothing, dict):
        raise RuntimeError(
            "La reconnaissance n'a pas retourné un dictionnaire."
        )

    # ========================================================
    # ATTRIBUTS
    # ========================================================

    print()
    print("[WARDROBE] Attributs...")
    print()

    analysis = analyze_attributes(
        cutout_path,
        clothing,
    )

    if not isinstance(analysis, dict):
        raise RuntimeError(
            "L'analyse des attributs n'a pas retourné un dictionnaire."
        )

    # ========================================================
    # DONNEES BDD
    # ========================================================

    analysis["image_hash"] = image_hash
    analysis["original_path"] = str(image_path)
    analysis["cutout_path"] = str(cutout_path)

    # ========================================================
    # SAUVEGARDE
    # ========================================================

    saved = save_clothing(
        analysis
    )

    if saved is None:
        raise RuntimeError(
            "Le vêtement n'a pas pu être enregistré."
        )

    print()
    print("=" * 60)
    print("[WARDROBE] Vêtement enregistré")
    print(f"[WARDROBE] ID : {saved.get('id')}")
    print(f"[WARDROBE] Type : {saved.get('type')}")
    print(f"[WARDROBE] Catégorie : {saved.get('categorie')}")
    print("=" * 60)
    print()

    return {
        "source": "ai",
        "clothing": saved,
    }
