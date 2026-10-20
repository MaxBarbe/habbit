from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


# ============================================================
# MFLUX
# ============================================================

from mflux.models.common.config.model_config import (
    ModelConfig,
)

from mflux.models.flux.variants.in_context.flux_in_context_fill import (
    Flux1InContextFill,
)


# ============================================================
# DEFAULT CATVTON PROMPT
# ============================================================

PROMPT = (
    "The pair of images highlights a clothing and "
    "its styling on a model, high resolution, 4K, 8K; "
    "[IMAGE1] Detailed product shot of a clothing; "
    "[IMAGE2] The same cloth is worn by a model "
    "in a lifestyle setting."
)


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 2:
        print(
            "Usage: "
            "mflux_catvton_worker.py job.json"
        )
        sys.exit(1)

    config_path = Path(
        sys.argv[1]
    )

    if not config_path.exists():
        print(
            "Configuration introuvable:",
            config_path,
        )
        sys.exit(1)

    config = json.loads(
        config_path.read_text(
            encoding="utf-8"
        )
    )

    person_image = Path(
        config[
            "person_image"
        ]
    )

    pieces = config[
        "pieces"
    ]

    # Steps par défaut
    steps_default = int(
        config.get(
            "steps",
            6,
        )
    )

    width = int(
        config.get(
            "width",
            576,
        )
    )

    height = int(
        config.get(
            "height",
            768,
        )
    )

    quantize = int(
        config.get(
            "quantize",
            4,
        )
    )

    output = Path(
        config[
            "output"
        ]
    )

    temp_dir = Path(
        config[
            "temp_dir"
        ]
    )

    temp_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # LOAD MODEL ONCE
    # ========================================================

    print()
    print(
        "========================================"
    )
    print(
        "[MFLUX] Chargement FLUX CatVTON..."
    )
    print(
        "[MFLUX] Le modèle ne sera chargé "
        "qu'une seule fois."
    )
    print(
        "========================================"
    )
    print()

    flux = Flux1InContextFill(
        model_config=(
            ModelConfig
            .dev_fill_catvton()
        ),
        quantize=quantize,
    )

    print()
    print(
        "[MFLUX] Modèle chargé."
    )
    print()

    # ========================================================
    # SEQUENTIAL TRY-ON
    # ========================================================

    current_person = (
        person_image
    )

    total = len(
        pieces
    )

    for index, piece in enumerate(
        pieces,
        start=1,
    ):

        categorie = piece[
            "categorie"
        ]

        type_vetement = piece.get(
            "type",
            "",
        )

        garment = Path(
            piece[
                "garment"
            ]
        )

        mask = Path(
            piece[
                "mask"
            ]
        )

        # ====================================================
        # STEPS PAR PIECE
        # ====================================================

        steps_piece = int(
            piece.get(
                "steps",
                steps_default,
            )
        )

        print()
        print(
            "----------------------------------------"
        )
        print(
            f"[MFLUX] Pièce {index}/{total}"
        )
        print(
            f"[MFLUX] Catégorie : {categorie}"
        )
        print(
            f"[MFLUX] Type : {type_vetement}"
        )
        print(
            f"[MFLUX] Steps : {steps_piece}"
        )
        print(
            f"[MFLUX] Personne : {current_person}"
        )
        print(
            f"[MFLUX] Vêtement : {garment}"
        )
        print(
            f"[MFLUX] Masque : {mask}"
        )
        print(
            "----------------------------------------"
        )
        print()

        # ----------------------------------------------------
        # GENERATION
        # ----------------------------------------------------

        image = flux.generate_image(
            seed=1,
            prompt=PROMPT,
            width=width,
            height=height,
            guidance=30.0,
            scheduler="linear",
            num_inference_steps=steps_piece,

            # CatVTON :
            # IMAGE1 = vêtement
            left_image_path=str(
                garment
            ),

            # IMAGE2 = personne
            right_image_path=str(
                current_person
            ),

            # Zone à modifier
            masked_image_path=str(
                mask
            ),
        )

        stage_output = (
            temp_dir
            / (
                f"look_{index}_"
                f"{categorie}.png"
            )
        )

        # Le CLI CatVTON garde uniquement
        # la moitié droite contenant la personne.
        image.get_right_half().save(
            path=stage_output,
            export_json_metadata=False,
        )

        current_person = (
            stage_output
        )

        print(
            "PROGRESS:"
            + json.dumps(
                {
                    "piece":
                        index,

                    "total":
                        total,

                    "categorie":
                        categorie,

                    "type":
                        type_vetement,

                    "steps":
                        steps_piece,
                }
            ),
            flush=True,
        )

        print()
        print(
            f"[MFLUX] {categorie} terminé."
        )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    shutil.copy2(
        current_person,
        output,
    )

    print()
    print(
        "========================================"
    )
    print(
        "[MFLUX] LOOK COMPLET TERMINÉ"
    )
    print(
        "[MFLUX] Sortie :",
        output,
    )
    print(
        "========================================"
    )
    print()


if __name__ == "__main__":
    main()