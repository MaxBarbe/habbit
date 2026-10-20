from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image

import backend.services.clothing_recognition as cr


# ============================================================
# STYLES ANALYSES
# ============================================================

STYLE_PROMPTS = {
    "soiree": [
        "fashion clothing suitable for going out at night",
        "stylish evening clothing",
        "fashionable clothing for a night out",
        "dressy evening fashion",
    ],

    "sport": [
        "sportswear athletic clothing",
        "clothing designed for sport and exercise",
        "athletic performance fashion",
        "gym and running clothing",
    ],

    "elegant": [
        "elegant sophisticated clothing",
        "smart refined fashion",
        "formal stylish clothing",
        "chic elegant fashion",
    ],

    "casual": [
        "casual everyday clothing",
        "relaxed daily fashion",
        "basic everyday clothing",
        "casual street clothing",
    ],
}


_text_features = None


# ============================================================
# DEVICE
# ============================================================

def _get_device():

    if torch.backends.mps.is_available():
        return torch.device("mps")

    return torch.device("cpu")


# ============================================================
# RECUPERATION DU MODELE FASHIONCLIP
# ============================================================

def _get_fashionclip():

    # Dans clothing_recognition.py,
    # _load_model() charge les variables globales
    # mais ne retourne pas le modèle.
    cr._load_model()

    model = cr._model
    preprocess = cr._preprocess
    tokenizer = cr._tokenizer

    return (
        model,
        preprocess,
        tokenizer,
    )


# ============================================================
# EMBEDDINGS TEXTE
# ============================================================

def _get_text_features():

    global _text_features

    if _text_features is not None:
        return _text_features

    (
        model,
        _,
        tokenizer,
    ) = _get_fashionclip()

    device = _get_device()

    features_by_style = {}

    with torch.no_grad():

        for style, prompts in STYLE_PROMPTS.items():

            tokens = tokenizer(
                prompts
            ).to(device)

            features = model.encode_text(
                tokens
            )

            features = (
                features
                / features.norm(
                    dim=-1,
                    keepdim=True,
                )
            )

            # Moyenne des différents prompts
            # représentant le même style.
            prototype = features.mean(
                dim=0,
                keepdim=True,
            )

            prototype = (
                prototype
                / prototype.norm(
                    dim=-1,
                    keepdim=True,
                )
            )

            features_by_style[
                style
            ] = prototype

    _text_features = (
        features_by_style
    )

    return _text_features


# ============================================================
# DETECTION DU STYLE
# ============================================================

def detect_clothing_style(
    image_path: str | Path,
) -> dict:

    image_path = Path(
        image_path
    )

    (
        model,
        preprocess,
        _,
    ) = _get_fashionclip()

    device = _get_device()

    text_features = (
        _get_text_features()
    )

    # Fond blanc pour éviter que la transparence
    # influence inutilement FashionCLIP.
    image_rgba = (
        Image.open(image_path)
        .convert("RGBA")
    )

    background = Image.new(
        "RGBA",
        image_rgba.size,
        (255, 255, 255, 255),
    )

    background.alpha_composite(
        image_rgba
    )

    image = background.convert(
        "RGB"
    )

    image_tensor = (
        preprocess(image)
        .unsqueeze(0)
        .to(device)
    )

    # ========================================================
    # EMBEDDING IMAGE
    # ========================================================

    with torch.no_grad():

        image_features = (
            model.encode_image(
                image_tensor
            )
        )

        image_features = (
            image_features
            / image_features.norm(
                dim=-1,
                keepdim=True,
            )
        )

        similarities = []

        style_names = list(
            STYLE_PROMPTS.keys()
        )

        for style in style_names:

            prototype = (
                text_features[style]
            )

            similarity = (
                image_features
                @ prototype.T
            )

            similarities.append(
                similarity.squeeze()
            )

        similarities = torch.stack(
            similarities
        )

        # ----------------------------------------------------
        # SOFTMAX
        #
        # Ce ne sont pas des probabilités absolues.
        # C'est une distribution relative entre
        # les 4 styles proposés.
        # ----------------------------------------------------

        probabilities = torch.softmax(
            similarities / 0.07,
            dim=0,
        )

    scores = {
        style_names[i]:
            float(
                probabilities[i]
                .detach()
                .cpu()
                .item()
            )

        for i in range(
            len(style_names)
        )
    }

    ranking = sorted(
        scores.items(),
        key=lambda item:
            item[1],
        reverse=True,
    )

    best_style = ranking[0][0]

    return {
        "style_principal":
            best_style,

        "soiree":
            round(
                scores["soiree"],
                4,
            ),

        "sport":
            round(
                scores["sport"],
                4,
            ),

        "elegant":
            round(
                scores["elegant"],
                4,
            ),

        "casual":
            round(
                scores["casual"],
                4,
            ),

        "top_styles": [
            {
                "style": style,
                "score": round(
                    score,
                    4,
                ),
            }
            for style, score
            in ranking
        ],
    }
