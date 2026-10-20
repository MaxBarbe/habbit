from __future__ import annotations

from pathlib import Path

import open_clip
import torch
from PIL import Image


# ============================================================
# CONFIG
# ============================================================

MODEL_NAME = "hf-hub:Marqo/marqo-fashionCLIP"

LABELS = {
    # HAUTS
    "Débardeur": {
        "categorie": "haut",
        "prompt": "a sleeveless tank top clothing item",
    },
    "T-shirt": {
        "categorie": "haut",
        "prompt": "a short sleeve t-shirt clothing item",
    },
    "Chemise": {
        "categorie": "haut",
        "prompt": "a button-up shirt clothing item",
    },
    "Blouse": {
        "categorie": "haut",
        "prompt": "a blouse clothing item",
    },
    "Top": {
        "categorie": "haut",
        "prompt": "a women's top clothing item",
    },
    "Pull": {
        "categorie": "haut",
        "prompt": "a knitted sweater or pullover clothing item",
    },
    "Sweat": {
        "categorie": "haut",
        "prompt": "a sweatshirt without a hood",
    },
    "Hoodie": {
        "categorie": "haut",
        "prompt": "a hooded sweatshirt",
    },

    # EXTERIEURS
    "Cardigan": {
        "categorie": "exterieur",
        "prompt": "a cardigan sweater worn open over other clothes",
    },
    "Veste": {
        "categorie": "exterieur",
        "prompt": "a jacket outerwear clothing item",
    },
    "Blouson": {
        "categorie": "exterieur",
        "prompt": "a short jacket outerwear clothing item",
    },
    "Manteau": {
        "categorie": "exterieur",
        "prompt": "a long coat outerwear clothing item",
    },
    "Doudoune": {
        "categorie": "exterieur",
        "prompt": "a padded puffer jacket",
    },
    "Trench": {
        "categorie": "exterieur",
        "prompt": "a trench coat",
    },
    "Parka": {
        "categorie": "exterieur",
        "prompt": "a parka jacket",
    },

    # BAS
    "Jean": {
        "categorie": "bas",
        "prompt": "denim jeans trousers",
    },
    "Pantalon": {
        "categorie": "bas",
        "prompt": "regular trousers or pants",
    },
    "Pantalon large": {
        "categorie": "bas",
        "prompt": "wide leg trousers",
    },
    "Cargo": {
        "categorie": "bas",
        "prompt": "cargo pants with large pockets",
    },
    "Jogging": {
        "categorie": "bas",
        "prompt": "sweatpants or jogger pants",
    },
    "Short": {
        "categorie": "bas",
        "prompt": "short pants",
    },
    "Jupe": {
        "categorie": "bas",
        "prompt": "a skirt",
    },

    # CHAUSSURES
    "Baskets": {
        "categorie": "chaussures",
        "prompt": "sneakers footwear",
    },
    "Chaussures": {
        "categorie": "chaussures",
        "prompt": "shoes footwear",
    },
    "Bottes": {
        "categorie": "chaussures",
        "prompt": "boots footwear",
    },
    "Sandales": {
        "categorie": "chaussures",
        "prompt": "sandals footwear",
    },
}


# ============================================================
# MODEL CACHE
# ============================================================

_model = None
_preprocess = None
_tokenizer = None
_device = None
_text_features = None
_names = list(LABELS.keys())


# ============================================================
# LOAD MODEL
# ============================================================

def _load_model() -> None:

    global _model
    global _preprocess
    global _tokenizer
    global _device
    global _text_features

    if _model is not None:
        return

    print()
    print("=" * 60)
    print("[CLOTHING] Chargement Marqo-FashionCLIP...")
    print("=" * 60)

    _device = (
        "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )

    _model, _, _preprocess = (
        open_clip.create_model_and_transforms(
            MODEL_NAME
        )
    )

    _tokenizer = open_clip.get_tokenizer(
        MODEL_NAME
    )

    _model = _model.to(_device)
    _model.eval()

    prompts = [
        LABELS[name]["prompt"]
        for name in _names
    ]

    tokens = _tokenizer(
        prompts
    ).to(_device)

    with torch.no_grad():
        _text_features = _model.encode_text(
            tokens,
            normalize=True,
        )

    print(
        f"[CLOTHING] Device : {_device}"
    )
    print(
        "[CLOTHING] Modèle prêt."
    )
    print()


# ============================================================
# RECOGNITION
# ============================================================

def recognize_clothing(
    image_path: str | Path,
) -> dict:

    _load_model()

    image_path = Path(
        image_path
    )

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image introuvable : {image_path}"
        )

    image = Image.open(
        image_path
    ).convert("RGB")

    image_tensor = (
        _preprocess(image)
        .unsqueeze(0)
        .to(_device)
    )

    with torch.no_grad():

        image_features = (
            _model.encode_image(
                image_tensor,
                normalize=True,
            )
        )

        logits = (
            100.0
            * image_features
            @ _text_features.T
        )

        probabilities = (
            logits.softmax(
                dim=-1
            )[0]
        )

    results = sorted(
        zip(
            _names,
            probabilities.tolist(),
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    best_name, best_score = (
        results[0]
    )

    category = (
        LABELS[
            best_name
        ][
            "categorie"
        ]
    )

    print()
    print("=" * 45)
    print("[CLOTHING] TOP 5")
    print("=" * 45)

    for name, score in results[:5]:
        print(
            f"{name:<18} "
            f"{score * 100:6.2f}%"
        )

    print()
    print(
        "[CLOTHING] Reconnaissance :",
        best_name,
    )
    print(
        "[CLOTHING] Catégorie :",
        category,
    )
    print()

    return {
        "type": best_name,
        "categorie": category,
        "confidence": round(
            float(best_score),
            4,
        ),
    }
