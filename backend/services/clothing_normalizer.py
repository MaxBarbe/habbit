from __future__ import annotations

from pathlib import Path
from PIL import Image


def normalize_clothing(
    input_path: str | Path,
    output_path: str | Path,
    category: str | None = None,
) -> Path:
    """
    Normalisation géométrique d'un vêtement détouré.

    - conserve les pixels du vêtement
    - recadre selon le canal alpha
    - corrige automatiquement une orientation manifestement horizontale
    - centre le vêtement sur une toile transparente
    - ne déforme pas et ne recrée aucune partie du vêtement
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    image = Image.open(input_path).convert("RGBA")

    alpha = image.getchannel("A")
    bbox = alpha.getbbox()

    if bbox is None:
        raise ValueError(
            f"Aucun vêtement visible dans : {input_path}"
        )

    garment = image.crop(bbox)

    width, height = garment.size

    # --------------------------------------------------------
    # ORIENTATION
    # --------------------------------------------------------
    #
    # Pour les hauts / vêtements extérieurs :
    # une pièce beaucoup plus large que haute est probablement
    # photographiée couchée.
    #
    # On évite volontairement cette règle pour les pantalons et
    # chaussures.
    # --------------------------------------------------------

    category = (category or "").lower().strip()

    rotatable_categories = {
        "haut",
        "exterieur",
        "extérieur",
    }

    if (
        category in rotatable_categories
        and width > height * 1.15
    ):
        garment = garment.rotate(
            90,
            expand=True,
            resample=Image.Resampling.BICUBIC,
        )

        # Nouveau recadrage après rotation
        alpha = garment.getchannel("A")
        bbox = alpha.getbbox()

        if bbox is not None:
            garment = garment.crop(bbox)

    # --------------------------------------------------------
    # TOILE NORMALISEE
    # --------------------------------------------------------

    canvas_size = 1024
    margin = 80
    usable = canvas_size - (2 * margin)

    width, height = garment.size

    scale = min(
        usable / width,
        usable / height,
        1.0,
    )

    if scale < 1.0:
        garment = garment.resize(
            (
                max(1, round(width * scale)),
                max(1, round(height * scale)),
            ),
            Image.Resampling.LANCZOS,
        )

    canvas = Image.new(
        "RGBA",
        (canvas_size, canvas_size),
        (0, 0, 0, 0),
    )

    x = (canvas_size - garment.width) // 2
    y = (canvas_size - garment.height) // 2

    canvas.alpha_composite(
        garment,
        (x, y),
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    canvas.save(output_path, "PNG")

    return output_path
