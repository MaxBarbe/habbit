from pathlib import Path
import sqlite3

from PIL import Image, ImageChops

from mflux.models.common.config.model_config import ModelConfig
from mflux.models.flux.variants.in_context.flux_in_context_fill import (
    Flux1InContextFill,
)


ROOT = Path("/Users/maxime/Documents/Projets_IA/Habillage/APP-Habit")

WIDTH = 576
HEIGHT = 768

PERSON = ROOT / "backend/storage/person/reference_v1.jpg"

MASK_DIR = ROOT / "backend/storage/person/masks_v1"

OUTPUT_DIR = ROOT / "backend/storage/person/tryon_onepass"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BOARD_PATH = OUTPUT_DIR / "outfit_board.png"
MASK_PATH = OUTPUT_DIR / "combined_mask.png"
PERSON_PATH = OUTPUT_DIR / "person.png"
OUTPUT_PATH = OUTPUT_DIR / "look_onepass.png"


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
        raise RuntimeError(f"ID {clothing_id} introuvable")

    return dict(row)


def resolve_path(item):
    value = (
        item.get("cutout_path")
        or item.get("original_path")
    )

    if not value:
        raise RuntimeError(
            f"Aucune image pour ID {item['id']}"
        )

    p = Path(value)

    if not p.is_absolute():
        p = ROOT / p

    return p


def crop_rgba(path):
    img = Image.open(path).convert("RGBA")

    alpha = img.getchannel("A")
    bbox = alpha.getbbox()

    if bbox:
        img = img.crop(bbox)

    return img


def fit(img, max_w, max_h):
    ratio = min(
        max_w / img.width,
        max_h / img.height,
    )

    w = max(1, int(img.width * ratio))
    h = max(1, int(img.height * ratio))

    return img.resize(
        (w, h),
        Image.Resampling.LANCZOS,
    )


def place_center(canvas, img, center_x, center_y):
    x = int(center_x - img.width / 2)
    y = int(center_y - img.height / 2)

    canvas.alpha_composite(
        img,
        (x, y),
    )


haut = get_item(1)
bas = get_item(5)
chaussures = get_item(13)

print("TENUE")
print("Haut :", haut["type"], haut["couleur"])
print("Bas :", bas["type"], bas["couleur"])
print("Chaussures :", chaussures["type"], chaussures["couleur"])


# ============================================================
# PERSONNE
# ============================================================

person = Image.open(PERSON).convert("RGB")

person = person.resize(
    (WIDTH, HEIGHT),
    Image.Resampling.LANCZOS,
)

person.save(PERSON_PATH)


# ============================================================
# PLANCHE UNIQUE DES 3 VÊTEMENTS
# ============================================================

board = Image.new(
    "RGBA",
    (WIDTH, HEIGHT),
    (255, 255, 255, 255),
)

top_img = fit(
    crop_rgba(resolve_path(haut)),
    300,
    220,
)

bottom_img = fit(
    crop_rgba(resolve_path(bas)),
    330,
    330,
)

shoes_img = fit(
    crop_rgba(resolve_path(chaussures)),
    260,
    150,
)

place_center(
    board,
    top_img,
    WIDTH / 2,
    135,
)

place_center(
    board,
    bottom_img,
    WIDTH / 2,
    390,
)

place_center(
    board,
    shoes_img,
    WIDTH / 2,
    665,
)

board.convert("RGB").save(BOARD_PATH)


# ============================================================
# MASQUE UNIQUE
# ============================================================

mask_top = Image.open(
    MASK_DIR / "mask_haut.png"
).convert("L").resize(
    (WIDTH, HEIGHT),
    Image.Resampling.NEAREST,
)

mask_bottom = Image.open(
    MASK_DIR / "mask_bas.png"
).convert("L").resize(
    (WIDTH, HEIGHT),
    Image.Resampling.NEAREST,
)

mask_shoes = Image.open(
    MASK_DIR / "mask_chaussures.png"
).convert("L").resize(
    (WIDTH, HEIGHT),
    Image.Resampling.NEAREST,
)

combined = ImageChops.lighter(
    mask_top,
    mask_bottom,
)

combined = ImageChops.lighter(
    combined,
    mask_shoes,
)

combined.save(MASK_PATH)


# ============================================================
# MFLUX — UNE SEULE PASSE
# ============================================================

PROMPT = (
    "The left image contains one complete outfit consisting of "
    "a burgundy sleeveless top, black wide-leg pants and black sneakers. "
    "Dress the person in the right image with exactly these garments. "
    "Preserve the garment colors, shapes, proportions and materials. "
    "Do not invent sleeves, patterns, textures or additional clothing. "
    "Keep the person's face, hair, body, pose and background unchanged. "
    "The result must show the same person wearing the complete outfit."
)

print()
print("Chargement MFLUX...")

flux = Flux1InContextFill(
    model_config=ModelConfig.dev_fill_catvton(),
    quantize=4,
)

print("Génération ONE-PASS...")

image = flux.generate_image(
    seed=1,
    prompt=PROMPT,
    width=WIDTH,
    height=HEIGHT,
    guidance=30.0,
    scheduler="linear",
    num_inference_steps=8,
    left_image_path=str(BOARD_PATH),
    right_image_path=str(PERSON_PATH),
    masked_image_path=str(MASK_PATH),
)

image.get_right_half().save(
    path=OUTPUT_PATH,
    export_json_metadata=False,
)

print()
print("✅ ONE-PASS TERMINÉ")
print(OUTPUT_PATH)
