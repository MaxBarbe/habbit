from pathlib import Path
import sqlite3

from PIL import Image, ImageChops, ImageDraw

from mflux.models.common.config.model_config import ModelConfig
from mflux.models.flux.variants.in_context.flux_in_context_fill import (
    Flux1InContextFill,
)

ROOT = Path("/Users/maxime/Documents/Projets_IA/Habillage/APP-Habit")

WIDTH = 576
HEIGHT = 768

PERSON = ROOT / "backend/storage/person/reference_v1.jpg"
MASK_DIR = ROOT / "backend/storage/person/masks_v1"

OUTPUT_DIR = ROOT / "backend/storage/person/tryon_thirds"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PERSON_PATH = OUTPUT_DIR / "person.png"
BOARD_PATH = OUTPUT_DIR / "board_thirds.png"
MASK_PATH = OUTPUT_DIR / "mask_complete.png"
OUTPUT_PATH = OUTPUT_DIR / "look_thirds.png"


def get_item(clothing_id):
    db = ROOT / "backend/database/wardrobe.db"

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        "SELECT * FROM clothes WHERE id = ?",
        (clothing_id,),
    ).fetchone()

    conn.close()

    if row is None:
        raise RuntimeError(
            f"ID {clothing_id} introuvable"
        )

    return dict(row)


def resolve_path(item):
    value = (
        item.get("cutout_path")
        or item.get("original_path")
    )

    if not value:
        raise RuntimeError(
            f"Image introuvable pour ID {item['id']}"
        )

    path = Path(value)

    if not path.is_absolute():
        path = ROOT / path

    return path


def crop_rgba(path):
    image = Image.open(path).convert("RGBA")

    bbox = image.getchannel("A").getbbox()

    if bbox:
        image = image.crop(bbox)

    return image


def fit_inside(
    image,
    max_width,
    max_height,
):
    ratio = min(
        max_width / image.width,
        max_height / image.height,
    )

    width = max(
        1,
        int(image.width * ratio),
    )

    height = max(
        1,
        int(image.height * ratio),
    )

    return image.resize(
        (width, height),
        Image.Resampling.LANCZOS,
    )


def place_in_zone(
    canvas,
    image,
    y_start,
    y_end,
):
    zone_height = y_end - y_start

    image = fit_inside(
        image,
        WIDTH - 50,
        zone_height - 24,
    )

    x = (
        WIDTH - image.width
    ) // 2

    y = (
        y_start
        + (zone_height - image.height) // 2
    )

    canvas.alpha_composite(
        image,
        (x, y),
    )


haut = get_item(1)
bas = get_item(5)
chaussures = get_item(13)

print("TENUE")
print("1/3 HAUT       :", haut["type"], haut["couleur"])
print("1/3 BAS        :", bas["type"], bas["couleur"])
print("1/3 CHAUSSURES :", chaussures["type"], chaussures["couleur"])


# ============================================================
# PERSONNE
# ============================================================

person = Image.open(
    PERSON
).convert("RGB")

person = person.resize(
    (WIDTH, HEIGHT),
    Image.Resampling.LANCZOS,
)

person.save(
    PERSON_PATH
)


# ============================================================
# BOARD : EXACTEMENT 1/3 PAR VÊTEMENT
# ============================================================

board = Image.new(
    "RGBA",
    (WIDTH, HEIGHT),
    (255, 255, 255, 255),
)

third = HEIGHT // 3

zones = {
    "haut": (
        0,
        third,
    ),
    "bas": (
        third,
        third * 2,
    ),
    "chaussures": (
        third * 2,
        HEIGHT,
    ),
}

place_in_zone(
    board,
    crop_rgba(
        resolve_path(haut)
    ),
    *zones["haut"],
)

place_in_zone(
    board,
    crop_rgba(
        resolve_path(bas)
    ),
    *zones["bas"],
)

place_in_zone(
    board,
    crop_rgba(
        resolve_path(chaussures)
    ),
    *zones["chaussures"],
)

board.convert(
    "RGB"
).save(
    BOARD_PATH
)


# ============================================================
# MASQUE COMPLET
# ============================================================

def load_mask(name):
    return Image.open(
        MASK_DIR / name
    ).convert("L").resize(
        (WIDTH, HEIGHT),
        Image.Resampling.NEAREST,
    )


mask = ImageChops.lighter(
    load_mask("mask_haut.png"),
    load_mask("mask_bas.png"),
)

mask = ImageChops.lighter(
    mask,
    load_mask("mask_chaussures.png"),
)

mask.save(
    MASK_PATH
)


# ============================================================
# PROMPT
# ============================================================

PROMPT = (
    "The left image is divided vertically into three equal sections. "

    "TOP THIRD: the exact burgundy sleeveless tank top. "
    "MIDDLE THIRD: the exact black wide-leg pants. "
    "BOTTOM THIRD: the exact black sneakers. "

    "Dress the person in the right image with exactly these three products. "

    "Each section represents one separate garment. "
    "Do not mix the garments together. "

    "The middle garment is BLACK WIDE-LEG PANTS. "
    "The pants must stay wide from the thighs to the ankles. "
    "The ankle openings must be loose and wide. "
    "No elastic cuffs. "
    "They are not joggers and not sweatpants. "

    "The bottom garment is BLACK SNEAKERS. "
    "Replace the person's white sneakers with the black sneakers "
    "from the bottom third of the left image. "

    "The top garment is a BURGUNDY SLEEVELESS TANK TOP. "
    "It must remain sleeveless. "

    "Preserve the exact garment colors and silhouettes shown "
    "in each section of the left image. "

    "Do not invent garments, colors, patterns, sleeves, cuffs or textures. "

    "Keep the person's face, hair, body, pose and background unchanged."
)


# ============================================================
# MFLUX : UNE SEULE PASSE
# ============================================================

print()
print("Chargement MFLUX...")

flux = Flux1InContextFill(
    model_config=ModelConfig.dev_fill_catvton(),
    quantize=4,
)

print("Génération 1/3 + 1/3 + 1/3...")

image = flux.generate_image(
    seed=1,
    prompt=PROMPT,
    width=WIDTH,
    height=HEIGHT,
    guidance=30.0,
    scheduler="linear",
    num_inference_steps=8,
    left_image_path=str(
        BOARD_PATH
    ),
    right_image_path=str(
        PERSON_PATH
    ),
    masked_image_path=str(
        MASK_PATH
    ),
)

image.get_right_half().save(
    path=OUTPUT_PATH,
    export_json_metadata=False,
)

print()
print("✅ TEST 1/3 TERMINÉ")
print(OUTPUT_PATH)
print()
print("Board utilisé :")
print(BOARD_PATH)
