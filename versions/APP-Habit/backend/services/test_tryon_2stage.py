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

OUTPUT_DIR = ROOT / "backend/storage/person/tryon_2stage"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PERSON_PREP = OUTPUT_DIR / "person.png"
BOARD_CLOTHES = OUTPUT_DIR / "board_clothes.png"
MASK_CLOTHES = OUTPUT_DIR / "mask_clothes.png"
STAGE1 = OUTPUT_DIR / "stage1_top_bottom.png"

BOARD_SHOES = OUTPUT_DIR / "board_shoes.png"
MASK_SHOES = OUTPUT_DIR / "mask_shoes.png"
FINAL = OUTPUT_DIR / "look_2stage.png"


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
        raise RuntimeError("Image vêtement introuvable")

    path = Path(value)

    if not path.is_absolute():
        path = ROOT / path

    return path


def crop_rgba(path):
    img = Image.open(path).convert("RGBA")

    bbox = img.getchannel("A").getbbox()

    if bbox:
        img = img.crop(bbox)

    return img


def fit(img, max_w, max_h):
    ratio = min(
        max_w / img.width,
        max_h / img.height,
    )

    return img.resize(
        (
            max(1, int(img.width * ratio)),
            max(1, int(img.height * ratio)),
        ),
        Image.Resampling.LANCZOS,
    )


def place(canvas, img, cx, cy):
    canvas.alpha_composite(
        img,
        (
            int(cx - img.width / 2),
            int(cy - img.height / 2),
        ),
    )


haut = get_item(1)
bas = get_item(5)
shoes = get_item(13)


# ------------------------------------------------------------
# PERSONNE
# ------------------------------------------------------------

person = Image.open(PERSON).convert("RGB")
person = person.resize(
    (WIDTH, HEIGHT),
    Image.Resampling.LANCZOS,
)
person.save(PERSON_PREP)


# ------------------------------------------------------------
# STAGE 1 : HAUT + BAS UNIQUEMENT
# ------------------------------------------------------------

board = Image.new(
    "RGBA",
    (WIDTH, HEIGHT),
    (255, 255, 255, 255),
)

haut_img = fit(
    crop_rgba(resolve_path(haut)),
    340,
    270,
)

bas_img = fit(
    crop_rgba(resolve_path(bas)),
    390,
    410,
)

place(
    board,
    haut_img,
    WIDTH // 2,
    170,
)

place(
    board,
    bas_img,
    WIDTH // 2,
    500,
)

board.convert("RGB").save(
    BOARD_CLOTHES
)

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

mask_clothes = ImageChops.lighter(
    mask_top,
    mask_bottom,
)

mask_clothes.save(
    MASK_CLOTHES
)


PROMPT_CLOTHES = (
    "The left image contains exactly two garments: "
    "a burgundy sleeveless tank top and black wide-leg pants. "
    "Dress the person in the right image with exactly those two garments. "
    "The black pants must have a loose wide-leg silhouette from hip to ankle. "
    "The leg openings must remain wide and straight. "
    "They are NOT joggers, NOT sweatpants and must NOT have elastic cuffs. "
    "The burgundy top must remain sleeveless. "
    "Preserve the exact colors and garment silhouettes from the left image. "
    "Keep the face, hair, pose, shoes and background unchanged."
)


print("Chargement MFLUX...")

flux = Flux1InContextFill(
    model_config=ModelConfig.dev_fill_catvton(),
    quantize=4,
)

print("PASS 1/2 : haut + pantalon...")

image = flux.generate_image(
    seed=1,
    prompt=PROMPT_CLOTHES,
    width=WIDTH,
    height=HEIGHT,
    guidance=30.0,
    scheduler="linear",
    num_inference_steps=8,
    left_image_path=str(BOARD_CLOTHES),
    right_image_path=str(PERSON_PREP),
    masked_image_path=str(MASK_CLOTHES),
)

image.get_right_half().save(
    path=STAGE1,
    export_json_metadata=False,
)


# ------------------------------------------------------------
# STAGE 2 : CHAUSSURES UNIQUEMENT
# ------------------------------------------------------------

board = Image.new(
    "RGBA",
    (WIDTH, HEIGHT),
    (255, 255, 255, 255),
)

shoe_img = fit(
    crop_rgba(resolve_path(shoes)),
    400,
    300,
)

place(
    board,
    shoe_img,
    WIDTH // 2,
    HEIGHT // 2,
)

board.convert("RGB").save(
    BOARD_SHOES
)


shoe_mask = Image.open(
    MASK_DIR / "mask_chaussures.png"
).convert("L").resize(
    (WIDTH, HEIGHT),
    Image.Resampling.NEAREST,
)

shoe_mask.save(
    MASK_SHOES
)


PROMPT_SHOES = (
    "The left image shows the exact pair of black sneakers "
    "that must replace the shoes of the person in the right image. "
    "Replace ONLY the shoes inside the mask. "
    "The sneakers must be black, matching the exact product in the left image. "
    "Do not change the pants, top, legs, body, face, hair, pose or background."
)


print("PASS 2/2 : baskets noires...")

image = flux.generate_image(
    seed=1,
    prompt=PROMPT_SHOES,
    width=WIDTH,
    height=HEIGHT,
    guidance=30.0,
    scheduler="linear",
    num_inference_steps=6,
    left_image_path=str(BOARD_SHOES),
    right_image_path=str(STAGE1),
    masked_image_path=str(MASK_SHOES),
)

image.get_right_half().save(
    path=FINAL,
    export_json_metadata=False,
)

print()
print("✅ TEST 2-STAGE TERMINÉ")
print(FINAL)
