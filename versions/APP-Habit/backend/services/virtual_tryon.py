from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PERSON_IMAGE = PROJECT_ROOT / "backend" / "storage" / "person" / "reference_v1.jpg"

MFLUX_PYTHON = Path(
    "/Users/maxime/.local/share/uv/tools/mflux/bin/python"
)

WORKER_SCRIPT = (
    PROJECT_ROOT
    / "backend"
    / "services"
    / "mflux_catvton_worker.py"
)

WIDTH = 576
HEIGHT = 768

GARMENT_MAX_WIDTH = 470
GARMENT_MAX_HEIGHT = 640


MASKS = {
    "haut":
        PROJECT_ROOT
        / "backend"
        / "storage"
        / "person"
        / "masks_v1"
        / "mask_haut.png",

    "haut_long":
        PROJECT_ROOT
        / "backend"
        / "storage"
        / "person"
        / "masks_v1"
        / "mask_haut_long.png",

    "exterieur":
        PROJECT_ROOT
        / "backend"
        / "storage"
        / "person"
        / "masks_v1"
        / "mask_exterieur.png",

    "bas":
        PROJECT_ROOT
        / "backend"
        / "storage"
        / "person"
        / "masks_v1"
        / "mask_bas.png",

    "chaussures":
        PROJECT_ROOT
        / "backend"
        / "storage"
        / "person"
        / "masks_v1"
        / "mask_chaussures.png",
}


ORDRE = [
    "bas",
    "haut",
    "exterieur",
    "chaussures",
]


TYPES_HAUT_LONG = {
    "pull",
    "sweat",
    "sweatshirt",
    "hoodie",
    "col roulé",
    "col roule",
    "pullover",
    "pull-over",
}


# ============================================================
# HELPERS
# ============================================================

def normaliser_type(
    valeur: str | None,
) -> str:

    if not valeur:
        return ""

    return (
        str(valeur)
        .strip()
        .lower()
    )


def choisir_masque(
    categorie: str,
    item: dict,
) -> Path:

    if categorie == "haut":

        type_vetement = normaliser_type(
            item.get("type")
        )

        if type_vetement in TYPES_HAUT_LONG:
            return MASKS["haut_long"]

        return MASKS["haut"]

    return MASKS[categorie]


def choisir_steps(
    categorie: str,
    item: dict,
    steps_defaut: int,
) -> int:

    if categorie == "haut":

        type_vetement = normaliser_type(
            item.get("type")
        )

        if type_vetement in TYPES_HAUT_LONG:
            return 8

        return 6

    if categorie == "exterieur":
        return 8

    if categorie == "bas":
        return 6

    if categorie == "chaussures":
        return 6

    return steps_defaut


# ============================================================
# CHECK
# ============================================================

def verifier_mflux():

    if not MFLUX_PYTHON.exists():
        raise RuntimeError(
            f"Python MFLUX introuvable : {MFLUX_PYTHON}"
        )

    if not WORKER_SCRIPT.exists():
        raise RuntimeError(
            f"Worker MFLUX introuvable : {WORKER_SCRIPT}"
        )

    if not PERSON_IMAGE.exists():
        raise RuntimeError(
            f"Personne fixe introuvable : {PERSON_IMAGE}"
        )

    for nom, masque in MASKS.items():

        if not masque.exists():
            raise RuntimeError(
                f"Masque '{nom}' introuvable : {masque}"
            )


# ============================================================
# PERSON
# ============================================================

def preparer_personne(
    dossier_tmp: Path,
) -> Path:

    sortie = (
        dossier_tmp
        / "person_576x768.jpg"
    )

    image = Image.open(
        PERSON_IMAGE
    ).convert("RGB")

    image = image.resize(
        (
            WIDTH,
            HEIGHT,
        ),
        Image.Resampling.LANCZOS,
    )

    image.save(
        sortie,
        quality=95,
    )

    return sortie


# ============================================================
# GARMENT
# ============================================================

def preparer_vetement(
    chemin_source: str | Path,
    chemin_sortie: str | Path,
) -> Path:

    chemin_source = Path(
        chemin_source
    )

    chemin_sortie = Path(
        chemin_sortie
    )

    image = Image.open(
        chemin_source
    ).convert("RGBA")

    alpha = image.getchannel("A")

    bbox = alpha.getbbox()

    if bbox is not None:
        image = image.crop(
            bbox
        )

    if (
        image.width <= 0
        or image.height <= 0
    ):
        raise RuntimeError(
            "Image vêtement invalide."
        )

    ratio = min(
        GARMENT_MAX_WIDTH
        / image.width,

        GARMENT_MAX_HEIGHT
        / image.height,
    )

    nouveau_w = max(
        1,
        int(
            image.width
            * ratio
        ),
    )

    nouveau_h = max(
        1,
        int(
            image.height
            * ratio
        ),
    )

    image = image.resize(
        (
            nouveau_w,
            nouveau_h,
        ),
        Image.Resampling.LANCZOS,
    )

    fond = Image.new(
        "RGBA",
        (
            WIDTH,
            HEIGHT,
        ),
        (
            255,
            255,
            255,
            255,
        ),
    )

    x = (
        WIDTH
        - nouveau_w
    ) // 2

    y = (
        HEIGHT
        - nouveau_h
    ) // 2

    fond.alpha_composite(
        image,
        (
            x,
            y,
        ),
    )

    fond.convert(
        "RGB"
    ).save(
        chemin_sortie,
        quality=95,
    )

    return chemin_sortie


# ============================================================
# MASK
# ============================================================

def redimensionner_masque(
    masque_source: str | Path,
    masque_sortie: str | Path,
) -> Path:

    masque = Image.open(
        masque_source
    ).convert("L")

    masque = masque.resize(
        (
            WIDTH,
            HEIGHT,
        ),
        Image.Resampling.NEAREST,
    )

    masque_sortie = Path(
        masque_sortie
    )

    masque.save(
        masque_sortie
    )

    return masque_sortie


# ============================================================
# PIECES
# ============================================================

def extraire_pieces(
    tenue: dict,
    dossier_tmp: Path,
    *,
    steps_defaut: int = 6,
):

    pieces = []

    masques_cache: dict[str, Path] = {}

    for categorie in ORDRE:

        item = tenue.get(
            categorie
        )

        if not item:
            continue

        if isinstance(
            item,
            str,
        ):
            item = {
                "image_path":
                    item
            }

        chemin = (
            item.get("cutout_path")
            or item.get("image_path")
            or item.get("original_path")
            or item.get("chemin")
            or item.get("path")
        )

        if not chemin:
            continue

        chemin = Path(
            chemin
        )

        if not chemin.exists():

            print(
                "[VTON] Vêtement ignoré :",
                categorie,
                chemin,
            )

            continue

        masque_source = choisir_masque(
            categorie,
            item,
        )

        cle_masque = (
            masque_source.stem
        )

        if cle_masque not in masques_cache:

            masque_prepare = (
                dossier_tmp
                / f"{cle_masque}_576x768.png"
            )

            masques_cache[
                cle_masque
            ] = redimensionner_masque(
                masque_source,
                masque_prepare,
            )

        masque = (
            masques_cache[
                cle_masque
            ]
        )

        prepared = (
            dossier_tmp
            / f"garment_{categorie}.jpg"
        )

        preparer_vetement(
            chemin,
            prepared,
        )

        steps_piece = choisir_steps(
            categorie,
            item,
            steps_defaut,
        )

        print()
        print(
            "[VTON] Pièce préparée"
        )
        print(
            f"  Catégorie : {categorie}"
        )
        print(
            f"  Type      : {item.get('type')}"
        )
        print(
            f"  Masque    : {masque_source.name}"
        )
        print(
            f"  Steps     : {steps_piece}"
        )
        print()

        pieces.append(
            {
                "categorie":
                    categorie,

                "type":
                    item.get(
                        "type"
                    ),

                "garment":
                    str(
                        prepared
                    ),

                "mask":
                    str(
                        masque
                    ),

                "steps":
                    steps_piece,
            }
        )

    return pieces


# ============================================================
# GENERATE
# ============================================================

def generer_look(
    tenue: dict,
    *,
    steps: int = 6,
    progression=None,
) -> str:

    verifier_mflux()

    dossier_tmp = Path(
        tempfile.mkdtemp(
            prefix="dressing_vton_"
        )
    )

    personne_preparee = (
        preparer_personne(
            dossier_tmp
        )
    )

    pieces = extraire_pieces(
        tenue,
        dossier_tmp,
        steps_defaut=steps,
    )

    if not pieces:
        raise RuntimeError(
            "Aucun vêtement utilisable dans la tenue."
        )

    sortie_finale = (
        PROJECT_ROOT
        / "backend"
        / "storage"
        / "person"
        / "tryon_mflux"
        / "look_current.png"
    )

    sortie_finale.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    config_path = (
        dossier_tmp
        / "job.json"
    )

    job = {
        "person_image":
            str(
                personne_preparee
            ),

        "pieces":
            pieces,

        "steps":
            int(
                steps
            ),

        "width":
            WIDTH,

        "height":
            HEIGHT,

        "quantize":
            4,

        "output":
            str(
                sortie_finale
            ),

        "temp_dir":
            str(
                dossier_tmp
            ),
    }

    config_path.write_text(
        json.dumps(
            job,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    if progression:

        progression(
            0.05,
            desc=(
                "Chargement du moteur d'essayage..."
            ),
        )

    print()
    print(
        "========================================"
    )
    print(
        "[VTON] Démarrage moteur unique MFLUX"
    )
    print(
        f"[VTON] Résolution : {WIDTH}x{HEIGHT}"
    )
    print(
        f"[VTON] Nombre de pièces : {len(pieces)}"
    )
    print(
        "========================================"
    )
    print()

    commande = [
        str(
            MFLUX_PYTHON
        ),
        "-u",
        str(
            WORKER_SCRIPT
        ),
        str(
            config_path
        ),
    ]

    process = subprocess.Popen(
        commande,
        cwd=str(
            PROJECT_ROOT
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    assert (
        process.stdout
        is not None
    )

    total = len(
        pieces
    )

    for ligne in process.stdout:

        ligne = ligne.rstrip()

        print(
            ligne,
            flush=True,
        )

        if not progression:
            continue

        if ligne.startswith(
            "PROGRESS:"
        ):

            try:

                data = json.loads(
                    ligne[
                        len(
                            "PROGRESS:"
                        ):
                    ]
                )

                piece_index = int(
                    data.get(
                        "piece",
                        1,
                    )
                )

                categorie = (
                    data.get(
                        "categorie",
                        ""
                    )
                )

                ratio = (
                    piece_index
                    / total
                )

                progression(
                    min(
                        0.95,
                        ratio,
                    ),
                    desc=(
                        f"Essayage {categorie} "
                        f"({piece_index}/{total})..."
                    ),
                )

            except Exception:
                pass

    code = process.wait()

    if code != 0:

        raise RuntimeError(
            "Le moteur CatVTON a rencontré une erreur. "
            "Regarde le Terminal."
        )

    if not sortie_finale.exists():

        raise RuntimeError(
            "Aucune image finale n'a été créée."
        )

    if progression:

        progression(
            1.0,
            desc="Tenue terminée.",
        )

    print()
    print(
        "[VTON] LOOK TERMINÉ :",
        sortie_finale,
    )
    print()

    return str(
        sortie_finale
    )