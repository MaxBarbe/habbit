from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops


PROJECT_ROOT = Path(__file__).resolve().parents[2]

WIDTH = 576
HEIGHT = 768

PERSON_IMAGE = (
    PROJECT_ROOT
    / "backend"
    / "storage"
    / "person"
    / "reference_v1.jpg"
)

MASK_DIR = (
    PROJECT_ROOT
    / "backend"
    / "storage"
    / "person"
    / "masks_v1"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "backend"
    / "storage"
    / "person"
    / "tryon_onepass"
)

WORKER = (
    PROJECT_ROOT
    / "backend"
    / "services"
    / "mflux_onepass_worker.py"
)

MFLUX_PYTHON = Path(
    "/Users/maxime/.local/share/uv/tools/mflux/bin/python"
)

CATEGORY_ORDER = [
    "haut",
    "bas",
    "exterieur",
    "chaussures",
]


def _resolve_path(item: dict) -> Path | None:
    value = (
        item.get("cutout_path")
        or item.get("image_path")
        or item.get("original_path")
        or item.get("path")
        or item.get("chemin")
    )

    if not value:
        return None

    path = Path(value)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path


def _crop_rgba(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")

    alpha = image.getchannel("A")
    bbox = alpha.getbbox()

    if bbox:
        image = image.crop(bbox)

    return image


def _fit(
    image: Image.Image,
    max_width: int,
    max_height: int,
) -> Image.Image:
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


def _place(
    canvas: Image.Image,
    image: Image.Image,
    center_x: int,
    center_y: int,
):
    x = int(
        center_x
        - image.width / 2
    )

    y = int(
        center_y
        - image.height / 2
    )

    canvas.alpha_composite(
        image,
        (x, y),
    )


def _outfit_key(outfit: dict) -> str:
    values = []

    for category in CATEGORY_ORDER:
        item = outfit.get(category)

        if not item:
            continue

        values.append(
            f"{category}:{item.get('id')}:{item.get('cutout_path')}"
        )

    raw = "|".join(values)

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:20]


def _build_prompt(outfit: dict) -> str:
    descriptions = []

    for category in CATEGORY_ORDER:
        item = outfit.get(category)

        if not item:
            continue

        garment_type = (
            item.get("type")
            or category
        )

        color = (
            item.get("couleur")
            or ""
        )

        text = f"{color} {garment_type}".strip()
        descriptions.append(text)

    garments = ", ".join(descriptions)

    return (
        "The left image contains the exact garments of one complete outfit: "
        f"{garments}. "
        "Dress the person in the right image with these exact garments. "
        "Preserve the original garment colors, shapes, proportions, lengths, "
        "materials and silhouettes. "
        "Do not invent sleeves, patterns, textures, accessories or additional clothing. "
        "Do not change one garment into another garment type. "
        "Keep the person's identity, face, hair, body shape, pose and background unchanged. "
        "Create one realistic full-body image of the same person wearing the complete outfit."
    )


def _prepare_person(
    temp_dir: Path,
) -> Path:
    output = temp_dir / "person.png"

    image = Image.open(
        PERSON_IMAGE
    ).convert("RGB")

    image = image.resize(
        (WIDTH, HEIGHT),
        Image.Resampling.LANCZOS,
    )

    image.save(output)

    return output


def _prepare_board(
    outfit: dict,
    temp_dir: Path,
) -> Path:
    board = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (255, 255, 255, 255),
    )

    items = {
        category: outfit.get(category)
        for category in CATEGORY_ORDER
        if outfit.get(category)
    }

    # Configuration validée pour haut + bas + chaussures
    if "exterieur" not in items:
        slots = {
            "haut": (
                WIDTH // 2,
                135,
                300,
                220,
            ),
            "bas": (
                WIDTH // 2,
                390,
                330,
                330,
            ),
            "chaussures": (
                WIDTH // 2,
                665,
                260,
                150,
            ),
        }

    # Tenue 4 pièces : haut + extérieur en haut de la planche
    else:
        slots = {
            "haut": (
                170,
                150,
                245,
                245,
            ),
            "exterieur": (
                410,
                150,
                245,
                245,
            ),
            "bas": (
                WIDTH // 2,
                425,
                320,
                330,
            ),
            "chaussures": (
                WIDTH // 2,
                675,
                250,
                130,
            ),
        }

    for category, item in items.items():
        path = _resolve_path(item)

        if (
            path is None
            or not path.exists()
            or category not in slots
        ):
            continue

        cx, cy, max_w, max_h = slots[category]

        garment = _crop_rgba(path)

        garment = _fit(
            garment,
            max_w,
            max_h,
        )

        _place(
            board,
            garment,
            cx,
            cy,
        )

    output = temp_dir / "outfit_board.png"

    board.convert(
        "RGB"
    ).save(output)

    return output


def _prepare_mask(
    outfit: dict,
    temp_dir: Path,
) -> Path:
    combined = Image.new(
        "L",
        (WIDTH, HEIGHT),
        0,
    )

    mask_files = {
        "haut": "mask_haut.png",
        "bas": "mask_bas.png",
        "exterieur": "mask_exterieur.png",
        "chaussures": "mask_chaussures.png",
    }

    for category, filename in mask_files.items():
        if not outfit.get(category):
            continue

        path = MASK_DIR / filename

        mask = Image.open(
            path
        ).convert("L")

        mask = mask.resize(
            (WIDTH, HEIGHT),
            Image.Resampling.NEAREST,
        )

        combined = ImageChops.lighter(
            combined,
            mask,
        )

    output = temp_dir / "combined_mask.png"

    combined.save(output)

    return output


def generate_outfit_tryon(
    outfit: dict,
    *,
    force: bool = False,
) -> str:
    if not PERSON_IMAGE.exists():
        raise RuntimeError(
            f"Personne V1 introuvable : {PERSON_IMAGE}"
        )

    if not MFLUX_PYTHON.exists():
        raise RuntimeError(
            f"MFLUX introuvable : {MFLUX_PYTHON}"
        )

    if not WORKER.exists():
        raise RuntimeError(
            f"Worker introuvable : {WORKER}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    key = _outfit_key(outfit)

    final_output = (
        OUTPUT_DIR
        / f"look_{key}.png"
    )

    if (
        final_output.exists()
        and not force
    ):
        print(
            "[VTON] Cache utilisé :",
            final_output,
        )

        return str(final_output)

    temp_dir = Path(
        tempfile.mkdtemp(
            prefix="app_habit_onepass_"
        )
    )

    person = _prepare_person(
        temp_dir
    )

    board = _prepare_board(
        outfit,
        temp_dir,
    )

    mask = _prepare_mask(
        outfit,
        temp_dir,
    )

    prompt = _build_prompt(
        outfit
    )

    job = {
        "person": str(person),
        "board": str(board),
        "mask": str(mask),
        "output": str(final_output),
        "prompt": prompt,
        "width": WIDTH,
        "height": HEIGHT,
        "steps": 8,
        "guidance": 30.0,
        "quantize": 4,
        "seed": 1,
    }

    job_path = (
        temp_dir
        / "job.json"
    )

    job_path.write_text(
        json.dumps(
            job,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "=========================================="
    )
    print(
        "[VTON] ONE-PASS"
    )
    print(
        f"[VTON] Cache key : {key}"
    )
    print(
        "=========================================="
    )
    print()

    process = subprocess.Popen(
        [
            str(MFLUX_PYTHON),
            "-u",
            str(WORKER),
            str(job_path),
        ],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    if process.stdout:
        for line in process.stdout:
            print(
                line.rstrip(),
                flush=True,
            )

    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError(
            "Erreur pendant la génération MFLUX ONE-PASS."
        )

    if not final_output.exists():
        raise RuntimeError(
            "MFLUX n'a pas créé l'image finale."
        )

    return str(final_output)
