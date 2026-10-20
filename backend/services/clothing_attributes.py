from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image

import backend.services.clothing_recognition as cr


# ============================================================
# MATIERES
# ============================================================

MATERIALS = {
    "Coton": "a cotton fabric clothing item",
    "Laine": "a wool fabric clothing item",
    "Denim": "a denim fabric clothing item",
    "Lin": "a linen fabric clothing item",
    "Cuir": "a leather clothing item",
    "Maille": "a knitted fabric clothing item",
    "Polyester": "a polyester synthetic fabric clothing item",
    "Satin": "a satin fabric clothing item",
    "Soie": "a silk fabric clothing item",
    "Velours": "a velvet fabric clothing item",
}


# ============================================================
# PALETTE COULEURS
# ============================================================

COLORS = {
    "Noir": (25, 25, 25),
    "Blanc": (235, 235, 235),
    "Gris": (128, 128, 128),

    "Beige": (205, 190, 160),
    "Crème": (235, 225, 195),
    "Marron": (115, 75, 50),

    "Rouge": (190, 40, 45),
    "Bordeaux": (105, 30, 45),
    "Rose": (220, 120, 150),

    "Orange": (220, 115, 35),
    "Jaune": (225, 195, 50),

    "Vert": (60, 130, 75),
    "Kaki": (105, 110, 65),

    "Bleu": (55, 105, 175),
    "Bleu marine": (35, 50, 85),

    "Violet": (115, 70, 145),
}


# ============================================================
# COULEUR
# ============================================================

def _rgb_to_hsv(rgb: np.ndarray) -> tuple[float, float, float]:
    """RGB 0-255 -> HSV avec H 0-360, S/V 0-1."""
    import colorsys

    r, g, b = [float(x) / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    return h * 360.0, s, v


def _classify_color(rgb: np.ndarray) -> str:
    """
    Classification couleur basée sur HSV.
    Plus robuste qu'une simple distance RGB.
    """

    h, s, v = _rgb_to_hsv(rgb)

    # Couleurs neutres
    if v <= 0.24:
        return "Noir"

    if s <= 0.12:
        if v >= 0.88:
            return "Blanc"
        if v >= 0.68:
            return "Gris clair"
        if v >= 0.35:
            return "Gris"
        return "Noir"

    # Blanc / crème / beige
    if s <= 0.28 and v >= 0.82:
        if 30 <= h <= 65:
            return "Crème"
        return "Blanc"

    if 28 <= h <= 55 and s <= 0.48 and v >= 0.55:
        return "Beige"

    # Couleurs chromatiques
    if h < 12 or h >= 350:
        if v < 0.45:
            return "Bordeaux"
        return "Rouge"

    if h < 25:
        if v < 0.48:
            return "Marron"
        return "Orange"

    if h < 48:
        if v < 0.48:
            return "Marron"
        return "Jaune"

    if h < 72:
        if s < 0.45:
            return "Beige"
        return "Jaune"

    if h < 105:
        if v < 0.48:
            return "Kaki"
        return "Vert"

    if h < 170:
        if v < 0.42:
            return "Kaki"
        return "Vert"

    if h < 195:
        return "Turquoise"

    if h < 250:
        if v < 0.35:
            return "Bleu marine"
        return "Bleu"

    if h < 285:
        if v < 0.35:
            return "Bleu marine"
        return "Violet"

    if h < 330:
        if v >= 0.65:
            return "Rose"
        return "Violet"

    if v < 0.45:
        return "Bordeaux"

    return "Rose"


def _color_difference(
    rgb1: list[int],
    rgb2: list[int],
) -> dict:

    h1, s1, v1 = _rgb_to_hsv(np.array(rgb1))
    h2, s2, v2 = _rgb_to_hsv(np.array(rgb2))

    hue = abs(h1 - h2)
    hue = min(hue, 360.0 - hue)

    return {
        "hue": hue,
        "saturation": abs(s1 - s2),
        "brightness": abs(v1 - v2),
    }


def _is_real_secondary(
    primary: dict,
    secondary: dict,
) -> bool:
    """
    Détermine si la seconde couleur représente réellement
    une autre couleur du vêtement et non une ombre/reflet.
    """

    # Une zone secondaire doit être importante.
    if secondary["pourcentage"] < 0.20:
        return False

    p_name = primary["couleur"]
    s_name = secondary["couleur"]

    if p_name == s_name:
        return False

    diff = _color_difference(
        primary["rgb"],
        secondary["rgb"],
    )

    # --------------------------------------------------------
    # Ombres et reflets sur vêtements très sombres
    # --------------------------------------------------------

    _, p_sat, p_val = _rgb_to_hsv(
        np.array(primary["rgb"])
    )

    _, s_sat, s_val = _rgb_to_hsv(
        np.array(secondary["rgb"])
    )

    # Deux zones qui restent toutes les deux sombres sont
    # généralement le même tissu sous un éclairage différent.
    #
    # Exemple réel :
    # Noir [39, 32, 22]
    # Bordeaux [76, 52, 52]
    #
    # On évite donc de déclarer artificiellement le vêtement
    # comme multicolore.
    if (
        p_val < 0.35
        and s_val < 0.40
        and abs(p_val - s_val) < 0.22
    ):
        return False

    # --------------------------------------------------------
    # Cas achromatiques :
    # noir/gris/blanc sont souvent des variations de lumière.
    # --------------------------------------------------------

    neutrals = {
        "Noir",
        "Gris",
        "Gris clair",
        "Blanc",
    }

    if p_name in neutrals and s_name in neutrals:

        # Il faut une très forte différence de luminosité
        # pour considérer noir + blanc comme deux vraies couleurs.
        return diff["brightness"] >= 0.55

    # --------------------------------------------------------
    # Familles proches
    # --------------------------------------------------------

    same_families = [
        {"Noir", "Bordeaux", "Marron"},
        {"Bleu", "Bleu marine", "Turquoise"},
        {"Vert", "Kaki"},
        {"Beige", "Crème", "Marron"},
        {"Rouge", "Bordeaux", "Rose"},
    ]

    for family in same_families:

        if p_name in family and s_name in family:

            # Si la teinte reste proche, on considère
            # qu'il s'agit du même tissu sous une autre lumière.
            if diff["hue"] < 35:
                return False

    # --------------------------------------------------------
    # Très faible changement de teinte
    # --------------------------------------------------------

    if (
        diff["hue"] < 20
        and diff["saturation"] < 0.30
    ):
        return False

    # --------------------------------------------------------
    # Reflet / ombre :
    # grosse variation de luminosité mais teinte similaire.
    # --------------------------------------------------------

    if (
        diff["hue"] < 30
        and diff["brightness"] >= 0.20
    ):
        return False

    return True


def detect_dominant_color(image_path: str | Path) -> dict:

    image = Image.open(image_path).convert("RGBA")

    image.thumbnail((400, 400))

    data = np.asarray(image)

    rgb = data[:, :, :3].astype(np.float32)
    alpha = data[:, :, 3]

    pixels = rgb[alpha >= 180]

    if len(pixels) == 0:
        return {
            "couleur": "Inconnue",
            "couleur_secondaire": None,
            "multicolore": False,
            "palette": [],
            "rgb": None,
        }

    if len(pixels) > 30000:
        step = max(
            1,
            len(pixels) // 30000
        )

        pixels = pixels[::step][:30000]

    # Quantification RGB
    quantized = (
        np.round(pixels / 24.0) * 24.0
    ).clip(0, 255)

    unique, counts = np.unique(
        quantized.astype(np.uint8),
        axis=0,
        return_counts=True,
    )

    order = np.argsort(counts)[::-1]

    grouped = {}

    for index in order[:100]:

        rgb_value = unique[index].astype(
            np.float32
        )

        count = int(counts[index])

        name = _classify_color(
            rgb_value
        )

        if name not in grouped:

            grouped[name] = {
                "count": 0,
                "rgb_sum": np.zeros(
                    3,
                    dtype=np.float64,
                ),
            }

        grouped[name]["count"] += count

        grouped[name]["rgb_sum"] += (
            rgb_value * count
        )

    total = sum(
        value["count"]
        for value in grouped.values()
    )

    palette = []

    for name, value in grouped.items():

        percentage = (
            value["count"] / total
        )

        mean_rgb = (
            value["rgb_sum"]
            / value["count"]
        )

        palette.append({
            "couleur": name,
            "pourcentage": percentage,
            "rgb": [
                int(round(mean_rgb[0])),
                int(round(mean_rgb[1])),
                int(round(mean_rgb[2])),
            ],
        })

    palette.sort(
        key=lambda item: item["pourcentage"],
        reverse=True,
    )

    primary = palette[0]

    # --------------------------------------------------------
    # Recherche d'une VRAIE couleur secondaire.
    #
    # On ne prend plus simplement palette[1].
    # --------------------------------------------------------

    secondary = None

    for candidate in palette[1:]:

        if _is_real_secondary(
            primary,
            candidate,
        ):
            secondary = candidate
            break

    multicolor = secondary is not None

    # Palette informative :
    # on garde les couleurs significatives pour le debug,
    # même si elles ne sont pas considérées multicolores.
    debug_palette = [
        item
        for item in palette
        if item["pourcentage"] >= 0.08
    ][:5]

    return {
        "couleur": primary["couleur"],

        "couleur_secondaire": (
            secondary["couleur"]
            if secondary
            else None
        ),

        "multicolore": multicolor,

        "palette": [
            {
                "couleur": item["couleur"],
                "pourcentage": round(
                    item["pourcentage"],
                    4,
                ),
                "rgb": item["rgb"],
            }
            for item in debug_palette
        ],

        "rgb": primary["rgb"],
    }


# ============================================================
# MATIERE
# ============================================================

def detect_material(image_path: str | Path) -> dict:

    cr._load_model()

    image = Image.open(image_path).convert("RGB")

    tensor = (
        cr._preprocess(image)
        .unsqueeze(0)
        .to(cr._device)
    )

    names = list(MATERIALS.keys())
    prompts = list(MATERIALS.values())

    tokens = cr._tokenizer(prompts).to(cr._device)

    with torch.no_grad():

        image_features = cr._model.encode_image(
            tensor,
            normalize=True,
        )

        text_features = cr._model.encode_text(
            tokens,
            normalize=True,
        )

        logits = (
            100.0
            * image_features
            @ text_features.T
        )

        probabilities = logits.softmax(dim=-1)[0]

    results = sorted(
        zip(names, probabilities.tolist()),
        key=lambda x: x[1],
        reverse=True,
    )

    detected_name, score = results[0]

    if score >= 0.70:
        status = "fiable"
        displayed_material = detected_name

    elif score >= 0.45:
        status = "probable"
        displayed_material = detected_name

    else:
        status = "incertaine"
        displayed_material = "Incertaine"

    return {
        "matiere": displayed_material,
        "matiere_detectee": detected_name,
        "matiere_confidence": round(float(score), 4),
        "matiere_statut": status,
        "matiere_top3": [
            {
                "matiere": name,
                "confidence": round(float(value), 4),
            }
            for name, value in results[:3]
        ],
    }


# ============================================================
# SAISON
# ============================================================

def detect_season(
    clothing_type: str,
    material: str,
    material_confidence: float = 0.0,
) -> list[str]:

    # Types fortement saisonniers
    if clothing_type in {
        "Débardeur",
        "Short",
        "Sandales",
    }:
        return ["printemps", "été"]

    if clothing_type in {
        "Doudoune",
        "Parka",
        "Manteau",
    }:
        return ["automne", "hiver"]

    if clothing_type in {
        "Pull",
        "Hoodie",
        "Sweat",
    }:
        return ["automne", "hiver"]

    # La matière ne modifie la saison que si
    # FashionCLIP est suffisamment sûr.
    if material_confidence >= 0.70:

        if material in {
            "Laine",
            "Maille",
            "Velours",
        }:
            return ["automne", "hiver"]

        if material in {
            "Lin",
        }:
            return ["printemps", "été"]

    # Types polyvalents
    if clothing_type in {
        "T-shirt",
        "Chemise",
        "Blouse",
        "Top",
        "Jean",
        "Pantalon",
        "Pantalon large",
        "Cargo",
        "Jupe",
        "Baskets",
        "Chaussures",
    }:
        return [
            "printemps",
            "été",
            "automne",
        ]

    if clothing_type in {
        "Veste",
        "Blouson",
        "Cardigan",
        "Bottes",
    }:
        return [
            "printemps",
            "automne",
            "hiver",
        ]

    return [
        "printemps",
        "été",
        "automne",
        "hiver",
    ]


# ============================================================
# ANALYSE COMPLETE
# ============================================================

def analyze_attributes(
    image_path: str | Path,
    clothing_result: dict | None = None,
) -> dict:

    if clothing_result is None:
        clothing_result = cr.recognize_clothing(
            image_path
        )

    color = detect_dominant_color(
        image_path
    )

    material = detect_material(
        image_path
    )

    seasons = detect_season(
        clothing_result["type"],
        material["matiere_detectee"],
        material["matiere_confidence"],
    )

    return {
        **clothing_result,
        **color,
        **material,
        "saisons": seasons,
    }
