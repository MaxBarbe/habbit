from pathlib import Path
import sqlite3

from PIL import Image, ImageFilter

from mflux.models.common.config.model_config import ModelConfig
from mflux.models.flux.variants.in_context.flux_in_context_fill import (
    Flux1InContextFill,
)

ROOT = Path("/Users/maxime/Documents/Projets_IA/Habillage/APP-Habit")

WIDTH = 576
HEIGHT = 768

PERSON = ROOT / "backend/storage/person/reference_v1.jpg"
MASK_DIR = ROOT / "backend/storage/person/masks_v1"

OUTPUT_DIR = ROOT / "backend/storage/person/tryon_independent"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PERSON_PREP = OUTPUT_DIR / "person.png"

TOP_RESULT = OUTPUT_DIR / "top.png"
BOTTOM_RESULT = OUTPUT_DIR / "bottom.png"
SHOES_RESULT = OUTPUT_DIR / "shoes.png"

FINAL = OUTPUT_DIR / "look_independent.png"


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


def prepare_garment(item, name):
    source = Image.open(
        resolve_path(item)
    ).convert("RGBA")

    bbox = source.getchannel("A").getbbox()

    if bbox:
        source = source.crop(bbox)

    ratio = min(
        470 / source.width,
        640 / source.height,
    )

    source = source.resize(
        (
            max(1, int(source.width * ratio)),
            max(1, int(source.height * ratio)),
        ),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (255, 255, 255, 255),
    )

    x = (WIDTH - source.width) // 2
    y = (HEIGHT - source.height) // 2

    canvas.alpha_composite(
        source,
        (x, y),
    )

    path = OUTPUT_DIR / f"garment_{name}.png"

    canvas.convert("RGB").save(path)

    return path


def prepare_mask(filename, name):
    mask = Image.open(
        MASK_DIR / filename
    ).convert("L")

    mask = mask.resize(
        (WIDTH, HEIGHT),
        Image.Resampling.NEAREST,
    )

    path = OUTPUT_DIR / f"mask_{name}.png"
    mask.save(path)

    return path


def generate(
    flux,
    garment,
    mask,
    output,
    prompt,
    steps=6,
):
    image = flux.generate_image(
        seed=1,
        prompt=prompt,
        width=WIDTH,
        height=HEIGHT,
        guidance=30.0,
        scheduler="linear",
        num_inference_steps=steps,
        left_image_path=str(garment),
        right_image_path=str(PERSON_PREP),
        masked_image_path=str(mask),
    )

    image.get_right_half().save(
        path=output,
        export_json_metadata=False,
    )


haut = get_item(1)
bas = get_item(5)
shoes = get_item(13)


# ============================================================
# PERSONNE ORIGINALE
# ============================================================

person = Image.open(
    PERSON
).convert("RGB")

person = person.resize(
    (WIDTH, HEIGHT),
    Image.Resampling.LANCZOS,
)

person.save(PERSON_PREP)


# ============================================================
# PREPARATION
# ============================================================

top_garment = prepare_garment(
    haut,
    "top",
)

bottom_garment = prepare_garment(
    bas,
    "bottom",
)

shoes_garment = prepare_garment(
    shoes,
    "shoes",
)


top_mask = prepare_mask(
    "mask_haut.png",
    "top",
)

bottom_mask = prepare_mask(
    "mask_bas.png",
    "bottom",
)

shoes_mask = prepare_mask(
    "mask_chaussures.png",
    "shoes",
)


# ============================================================
# MODELE CHARGE UNE SEULE FOIS
# ============================================================

print("Chargement MFLUX...")

flux = Flux1InContextFill(
    model_config=ModelConfig.dev_fill_catvton(),
    quantize=4,
)


# ============================================================
# 1/3 — HAUT
# ============================================================

print("1/3 HAUT...")

generate(
    flux,
    top_garment,
    top_mask,
    TOP_RESULT,
    (
        "The left image shows the exact burgundy sleeveless tank top. "
        "Dress the person with exactly this garment. "
        "Keep it sleeveless. "
        "Preserve its burgundy color, shape and length. "
        "Do not modify pants, shoes, face, hair or background."
    ),
    6,
)


# ============================================================
# 2/3 — BAS
# ============================================================

print("2/3 BAS...")

generate(
    flux,
    bottom_garment,
    bottom_mask,
    BOTTOM_RESULT,
    (
        "The left image shows the exact black wide-leg pants. "
        "Dress the person with exactly these pants. "
        "They must be loose wide-leg pants from hip to ankle. "
        "The ankle openings must remain wide and straight. "
        "No elastic cuffs. "
        "They are not joggers and not sweatpants. "
        "Preserve the exact black color and silhouette. "
        "Do not modify the top, shoes, face, hair or background."
    ),
    8,
)


# ============================================================
# 3/3 — CHAUSSURES
# ============================================================

print("3/3 CHAUSSURES...")

generate(
    flux,
    shoes_garment,
    shoes_mask,
    SHOES_RESULT,
    (
        "The left image shows the exact black sneakers. "
        "Replace the person's white shoes with exactly these black sneakers. "
        "The shoes must be black. "
        "Preserve their design and proportions. "
        "Do not modify pants, top, legs, body, face or background."
    ),
    6,
)


# ============================================================
# FUSION DES 3 GENERATIONS IA
# ============================================================

base = Image.open(
    PERSON_PREP
).convert("RGB")

top_image = Image.open(
    TOP_RESULT
).convert("RGB")

bottom_image = Image.open(
    BOTTOM_RESULT
).convert("RGB")

shoes_image = Image.open(
    SHOES_RESULT
).convert("RGB")


def feather(path, radius=3):
    return (
        Image.open(path)
        .convert("L")
        .filter(
            ImageFilter.GaussianBlur(radius)
        )
    )


# BAS d'abord
result = Image.composite(
    bottom_image,
    base,
    feather(bottom_mask, 3),
)

# HAUT ensuite
result = Image.composite(
    top_image,
    result,
    feather(top_mask, 3),
)

# CHAUSSURES en dernier
result = Image.composite(
    shoes_image,
    result,
    feather(shoes_mask, 2),
)

result.save(FINAL)

print()
print("✅ TEST TERMINÉ")
print(FINAL)
