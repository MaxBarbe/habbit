from __future__ import annotations

from itertools import product

from backend.database.wardrobe import get_all_clothes


# ============================================================
# COULEURS
# ============================================================

NEUTRALS = {
    "Noir",
    "Blanc",
    "Gris",
    "Gris clair",
    "Beige",
    "Crème",
}


COLOR_MATCHES = {
    "Bordeaux": {
        "Noir",
        "Blanc",
        "Gris",
        "Gris clair",
        "Beige",
        "Crème",
        "Bleu",
        "Bleu marine",
    },

    "Rouge": {
        "Noir",
        "Blanc",
        "Gris",
        "Beige",
        "Bleu",
        "Bleu marine",
    },

    "Rose": {
        "Blanc",
        "Gris",
        "Beige",
        "Crème",
        "Bleu",
        "Bleu marine",
    },

    "Bleu": {
        "Blanc",
        "Gris",
        "Beige",
        "Crème",
        "Noir",
        "Bordeaux",
        "Marron",
        "Kaki",
    },

    "Bleu marine": {
        "Blanc",
        "Gris",
        "Beige",
        "Crème",
        "Bordeaux",
        "Marron",
        "Kaki",
    },

    "Vert": {
        "Blanc",
        "Noir",
        "Beige",
        "Crème",
        "Gris",
        "Marron",
        "Bleu",
    },

    "Kaki": {
        "Noir",
        "Blanc",
        "Beige",
        "Crème",
        "Marron",
        "Bleu",
        "Bleu marine",
    },

    "Marron": {
        "Blanc",
        "Beige",
        "Crème",
        "Bleu",
        "Bleu marine",
        "Vert",
    },

    "Orange": {
        "Noir",
        "Blanc",
        "Beige",
        "Bleu",
        "Bleu marine",
    },

    "Jaune": {
        "Noir",
        "Blanc",
        "Gris",
        "Bleu",
        "Bleu marine",
    },

    "Violet": {
        "Noir",
        "Blanc",
        "Gris",
        "Beige",
        "Crème",
    },

    "Turquoise": {
        "Blanc",
        "Beige",
        "Crème",
        "Noir",
        "Bleu marine",
    },
}


# ============================================================
# PROFIL THERMIQUE
#
# 1 = très léger
# 2 = léger
# 3 = moyen
# 4 = chaud
# 5 = très chaud
# ============================================================

THERMAL_LEVEL = {
    "Débardeur": 1,
    "Top": 1,

    "T-shirt": 2,
    "Blouse": 2,
    "Chemise": 2,

    "Short": 1,
    "Jupe": 2,
    "Pantalon large": 2,

    "Pantalon": 3,
    "Cargo": 3,
    "Jean": 3,

    "Jogging": 4,

    "Cardigan": 3,
    "Sweat": 4,
    "Hoodie": 4,
    "Pull": 4,

    "Veste": 4,
    "Blouson": 4,
    "Trench": 4,

    "Parka": 5,
    "Doudoune": 5,
    "Manteau": 5,

    "Sandales": 1,
    "Baskets": 2,
    "Chaussures": 2,
    "Bottes": 4,
}


# ============================================================
# COMPATIBILITE ENTRE DEUX COULEURS
# ============================================================

def color_score(
    color_a: str | None,
    color_b: str | None,
) -> float:

    if not color_a or not color_b:
        return 0.50

    # Deux couleurs neutres
    if (
        color_a in NEUTRALS
        and color_b in NEUTRALS
    ):
        return 0.90

    # Une couleur + une base neutre
    if (
        color_a in NEUTRALS
        or color_b in NEUTRALS
    ):
        return 0.95

    # Même couleur
    if color_a == color_b:
        return 0.72

    # Couleurs compatibles
    if (
        color_b in COLOR_MATCHES.get(
            color_a,
            set(),
        )
        or
        color_a in COLOR_MATCHES.get(
            color_b,
            set(),
        )
    ):
        return 1.00

    # Association plus difficile
    return 0.45


# ============================================================
# PALETTE GLOBALE
# ============================================================

def palette_score(
    garments: list[dict],
) -> tuple[float, str]:

    colors = [
        garment.get("couleur")
        for garment in garments
        if garment.get("couleur")
    ]

    if not colors:
        return (
            0.50,
            "palette inconnue",
        )

    unique_colors = set(colors)

    neutral_count = sum(
        color in NEUTRALS
        for color in colors
    )

    non_neutral_count = (
        len(colors)
        - neutral_count
    )

    pair_scores = []

    # Compatibilité de chaque couleur
    # avec toutes les autres.
    for i in range(len(colors)):

        for j in range(
            i + 1,
            len(colors),
        ):

            pair_scores.append(
                color_score(
                    colors[i],
                    colors[j],
                )
            )

    if pair_scores:

        compatibility = (
            sum(pair_scores)
            / len(pair_scores)
        )

    else:

        compatibility = 1.0

    score = compatibility
    reasons = []

    # Une couleur principale entourée
    # de plusieurs neutres.
    if (
        non_neutral_count == 1
        and neutral_count >= 2
    ):

        score += 0.05

        reasons.append(
            "couleur principale équilibrée "
            "par des neutres"
        )

    # Trop de couleurs différentes
    if len(unique_colors) >= 4:

        score -= 0.08

        reasons.append(
            "palette très variée"
        )

    # Tenue entièrement neutre
    if non_neutral_count == 0:

        score += 0.02

        reasons.append(
            "palette neutre cohérente"
        )

    # Rappel de couleur
    if len(unique_colors) < len(colors):

        score += 0.02

        reasons.append(
            "rappel de couleur"
        )

    score = max(
        0.0,
        min(
            score,
            1.0,
        ),
    )

    if not reasons:

        reasons.append(
            "palette équilibrée"
        )

    return (
        score,
        ", ".join(reasons),
    )


# ============================================================
# SCORE COULEUR GLOBAL
# ============================================================

def outfit_color_score(
    top: dict,
    bottom: dict,
    shoes: dict,
    outerwear: dict | None = None,
) -> tuple[float, str]:

    garments = [
        top,
        bottom,
        shoes,
    ]

    if outerwear is not None:

        garments.append(
            outerwear
        )

    return palette_score(
        garments
    )


# ============================================================
# TEMPERATURE CIBLE
# ============================================================

def target_thermal_level(
    apparent_temperature: float,
) -> float:

    if apparent_temperature >= 30:
        return 1.0

    if apparent_temperature >= 25:
        return 1.5

    if apparent_temperature >= 20:
        return 2.0

    if apparent_temperature >= 15:
        return 3.0

    if apparent_temperature >= 10:
        return 4.0

    return 5.0


# ============================================================
# SCORE THERMIQUE D'UN VETEMENT
# ============================================================

def garment_temperature_score(
    garment: dict,
    apparent_temperature: float,
) -> float:

    level = THERMAL_LEVEL.get(
        garment.get("type"),
        3,
    )

    target = target_thermal_level(
        apparent_temperature
    )

    difference = abs(
        level - target
    )

    score = (
        1.0
        - difference * 0.25
    )

    return max(
        0.0,
        score,
    )


# ============================================================
# CONFORT THERMIQUE TENUE
# ============================================================

def outfit_temperature_score(
    top: dict,
    bottom: dict,
    shoes: dict,
    apparent_temperature: float,
    outerwear: dict | None = None,
) -> float:
    """
    Calcule le confort thermique de la tenue complète.

    La couche extérieure devient importante lorsqu'elle est présente,
    particulièrement quand la température baisse.
    """

    top_score = garment_temperature_score(
        top,
        apparent_temperature,
    )

    bottom_score = garment_temperature_score(
        bottom,
        apparent_temperature,
    )

    shoes_score = garment_temperature_score(
        shoes,
        apparent_temperature,
    )

    # --------------------------------------------------------
    # PAS DE COUCHE EXTERIEURE
    # --------------------------------------------------------

    if outerwear is None:
        return (
            top_score * 0.55
            + bottom_score * 0.30
            + shoes_score * 0.15
        )

    # --------------------------------------------------------
    # AVEC COUCHE EXTERIEURE
    # --------------------------------------------------------

    outer_score = garment_temperature_score(
        outerwear,
        apparent_temperature,
    )

    # Plus il fait froid, plus la couche extérieure
    # influence le confort global.
    if apparent_temperature < 5:
        outer_weight = 0.50

    elif apparent_temperature < 10:
        outer_weight = 0.45

    elif apparent_temperature < 16:
        outer_weight = 0.35

    else:
        outer_weight = 0.25

    remaining_weight = 1.0 - outer_weight

    inner_score = (
        top_score * 0.55
        + bottom_score * 0.30
        + shoes_score * 0.15
    )

    return (
        inner_score * remaining_weight
        + outer_score * outer_weight
    )

# ============================================================
# COUCHE EXTERIEURE NECESSAIRE ?
# ============================================================

def outerwear_required(
    apparent_temperature: float,
    rain: float,
    wind: float,
) -> bool:

    # Température fraîche/froide
    if apparent_temperature < 16:

        return True

    # Pluie significative
    if rain >= 1.0:

        return True

    # Vent important si température
    # pas suffisamment chaude.
    if (
        wind >= 30
        and apparent_temperature < 22
    ):

        return True

    return False


# ============================================================
# SCORE COUCHE EXTERIEURE
# ============================================================

def outerwear_score(
    garment: dict,
    apparent_temperature: float,
    rain: float,
    wind: float,
) -> float:

    garment_type = (
        garment.get("type")
    )

    score = (
        garment_temperature_score(
            garment,
            apparent_temperature,
        )
    )

    # Bonus en cas de pluie
    if rain >= 1.0:

        if garment_type in {
            "Veste",
            "Blouson",
            "Trench",
            "Parka",
            "Manteau",
        }:

            score += 0.15

    # Bonus en cas de vent fort
    if wind >= 30:

        if garment_type in {
            "Veste",
            "Blouson",
            "Trench",
            "Parka",
            "Manteau",
        }:

            score += 0.10

    return max(
        0.0,
        min(
            score,
            1.0,
        ),
    )


# ============================================================
# CHAUSSURES + METEO
# ============================================================

def shoes_weather_score(
    shoes: dict,
    apparent_temperature: float,
    rain: float,
) -> float:

    shoe_type = (
        shoes.get("type")
    )

    score = (
        garment_temperature_score(
            shoes,
            apparent_temperature,
        )
    )

    if rain >= 1.0:

        # Sandales sous la pluie
        if shoe_type == "Sandales":

            score -= 0.40

        # Bottes favorisées
        elif shoe_type == "Bottes":

            score += 0.15

    return max(
        0.0,
        min(
            score,
            1.0,
        ),
    )


# ============================================================
# SAISON
# ============================================================

def season_score(
    garments: list[dict],
    current_season: str,
) -> float:

    if not garments:

        return 0.50

    compatible = sum(
        current_season
        in garment.get(
            "saisons",
            [],
        )
        for garment in garments
    )

    return (
        compatible
        / len(garments)
    )


# ============================================================
# QUALITE DE RECONNAISSANCE
# ============================================================

def data_quality_score(
    garments: list[dict],
) -> float:

    if not garments:

        return 0.0

    values = [
        float(
            item.get(
                "confidence"
            )
            or 0
        )
        for item in garments
    ]

    return (
        sum(values)
        / len(values)
    )


# ============================================================
# IDENTITE D'UNE TENUE DE BASE
#
# Une même combinaison haut + bas
# n'apparaît qu'une fois dans le Top 3.
# ============================================================

def base_outfit_key(
    outfit: dict,
) -> tuple:

    return (
        outfit["haut"]["id"],
        outfit["bas"]["id"],
    )


# ============================================================
# DIVERSIFICATION TOP 3
# ============================================================

def diversify_outfits(
    outfits: list[dict],
    limit: int = 3,
) -> list[dict]:

    selected = []

    used_base_combinations = set()

    # Les outfits arrivent déjà
    # triés du meilleur au moins bon.
    for outfit in outfits:

        key = base_outfit_key(
            outfit
        )

        # On évite la même tenue avec
        # seulement une autre paire
        # de chaussures.
        if key in used_base_combinations:

            continue

        selected.append(
            outfit
        )

        used_base_combinations.add(
            key
        )

        if len(selected) >= limit:

            break

    return selected


# ============================================================
# MOTEUR PRINCIPAL
# ============================================================
# ============================================================
# SCORE DU MODE SPECIAL
# ============================================================

def mode_score(
    outfit: dict,
    mode: str,
) -> float:

    column_by_mode = {
        "soiree": "style_soiree",
        "sport": "style_sport",
        "elegant": "style_elegant",
    }

    column = column_by_mode.get(mode)

    if column is None:
        return 0.0

    garments = [
        outfit["haut"],
        outfit["bas"],
        outfit["chaussures"],
    ]

    if outfit.get("exterieur") is not None:
        garments.append(
            outfit["exterieur"]
        )

    scores = []

    for garment in garments:

        value = garment.get(column)

        if value is not None:
            scores.append(
                float(value)
            )

    if not scores:
        return 0.0

    return (
        sum(scores)
        / len(scores)
    )


# ============================================================
# MOTEUR PRINCIPAL
# ============================================================

def recommend_outfits(
    context: dict,
    limit: int = 3,
    mode: str | None = None,
) -> list[dict]:

    valid_modes = {
        None,
        "soiree",
        "sport",
        "elegant",
    }

    if mode not in valid_modes:
        raise ValueError(
            "Mode invalide : "
            "None, 'soiree', 'sport' ou 'elegant'"
        )

    clothes = get_all_clothes()

    # --------------------------------------------------------
    # RECUPERATION DES CATEGORIES
    # --------------------------------------------------------

    tops = [
        item
        for item in clothes
        if item["categorie"] == "haut"
    ]

    bottoms = [
        item
        for item in clothes
        if item["categorie"] == "bas"
    ]

    shoes_list = [
        item
        for item in clothes
        if item["categorie"] == "chaussures"
    ]

    outerwear_list = [
        item
        for item in clothes
        if item["categorie"] == "exterieur"
    ]

    if (
        not tops
        or not bottoms
        or not shoes_list
    ):
        return []

    # --------------------------------------------------------
    # CONTEXTE
    # --------------------------------------------------------

    weather = context["meteo"]

    apparent_temperature = float(
        weather["temperature_ressentie"]
    )

    rain = float(
        weather["pluie"]
    )

    wind = float(
        weather["vent"]
    )

    current_season = context["saison"]

    # --------------------------------------------------------
    # COUCHE EXTERIEURE
    # --------------------------------------------------------

    need_outerwear = outerwear_required(
        apparent_temperature,
        rain,
        wind,
    )

    if (
        need_outerwear
        and outerwear_list
    ):
        outerwear_options = (
            outerwear_list
        )

    else:
        outerwear_options = [None]

    outfits = []

    # --------------------------------------------------------
    # GENERATION DES COMBINAISONS
    # --------------------------------------------------------

    for (
        top,
        bottom,
        shoes,
        outerwear,
    ) in product(
        tops,
        bottoms,
        shoes_list,
        outerwear_options,
    ):

        garments = [
            top,
            bottom,
            shoes,
        ]

        if outerwear is not None:
            garments.append(
                outerwear
            )

        # ----------------------------------------------------
        # COULEURS
        # ----------------------------------------------------

        (
            c_score,
            palette_reason,
        ) = outfit_color_score(
            top,
            bottom,
            shoes,
            outerwear,
        )

        # ----------------------------------------------------
        # TEMPERATURE
        # ----------------------------------------------------

        t_score = outfit_temperature_score(
            top,
            bottom,
            shoes,
            apparent_temperature,
            outerwear,
        )

        # ----------------------------------------------------
        # CHAUSSURES
        # ----------------------------------------------------

        shoe_score = shoes_weather_score(
            shoes,
            apparent_temperature,
            rain,
        )

        # ----------------------------------------------------
        # COUCHE EXTERIEURE
        # ----------------------------------------------------

        if outerwear is not None:

            o_score = outerwear_score(
                outerwear,
                apparent_temperature,
                rain,
                wind,
            )

        else:
            o_score = 1.0

        # ----------------------------------------------------
        # SAISON
        # ----------------------------------------------------

        s_score = season_score(
            garments,
            current_season,
        )

        # ----------------------------------------------------
        # QUALITE DES DONNEES
        # ----------------------------------------------------

        q_score = data_quality_score(
            garments
        )

        # ----------------------------------------------------
        # SCORE FINAL NORMAL
        # ----------------------------------------------------

        final_score = (
            t_score * 0.35
            + c_score * 0.30
            + shoe_score * 0.15
            + o_score * 0.10
            + s_score * 0.05
            + q_score * 0.05
        )

        outfits.append({
            "score": round(
                final_score,
                4,
            ),

            "haut": top,
            "bas": bottom,
            "chaussures": shoes,
            "exterieur": outerwear,

            "exterieur_necessaire":
                need_outerwear,

            "score_temperature":
                round(t_score, 4),

            "score_couleur":
                round(c_score, 4),

            "score_chaussures":
                round(shoe_score, 4),

            "score_exterieur":
                round(o_score, 4),

            "score_saison":
                round(s_score, 4),

            "score_donnees":
                round(q_score, 4),

            "raison_palette":
                palette_reason,
        })

    # ========================================================
    # CLASSEMENT NORMAL
    # ========================================================

    outfits.sort(
        key=lambda item:
            item["score"],
        reverse=True,
    )

    # ========================================================
    # PROPOSITIONS 1 ET 2
    # ========================================================

    normal_outfits = diversify_outfits(
        outfits,
        limit=2,
    )

    selected = []

    if len(normal_outfits) >= 1:

        first = normal_outfits[0].copy()

        first["proposition"] = (
            "recommandee"
        )

        first["mode"] = None

        selected.append(first)

    if len(normal_outfits) >= 2:

        second = normal_outfits[1].copy()

        second["proposition"] = (
            "alternative"
        )

        second["mode"] = None

        selected.append(second)

    # ========================================================
    # PROPOSITION 3 — AUTOMATIQUE
    # ========================================================

    if mode is None:

        automatic = diversify_outfits(
            outfits,
            limit=3,
        )

        if len(automatic) >= 3:

            third = automatic[2].copy()

            third["proposition"] = (
                "mode"
            )

            third["mode"] = None

            selected.append(third)

        return selected[:limit]

    # ========================================================
    # PROPOSITION 3 — MODE SPECIAL
    # ========================================================

    used_base = {
        base_outfit_key(outfit)
        for outfit in selected
    }

    special_candidates = []

    for outfit in outfits:

        # Ne pas reprendre le même haut + bas
        # que les propositions 1 et 2.
        if (
            base_outfit_key(outfit)
            in used_base
        ):
            continue

        style_score = mode_score(
            outfit,
            mode,
        )

        # Le style influence fortement le Mode 3,
        # mais la tenue doit rester cohérente
        # avec météo / couleurs / confort.
        special_score = (
            outfit["score"] * 0.60
            + style_score * 0.40
        )

        candidate = outfit.copy()

        candidate["proposition"] = (
            "mode"
        )

        candidate["mode"] = mode

        candidate["score_mode"] = round(
            style_score,
            4,
        )

        candidate[
            "score_mode_final"
        ] = round(
            special_score,
            4,
        )

        special_candidates.append(
            candidate
        )

    special_candidates.sort(
        key=lambda item:
            item["score_mode_final"],
        reverse=True,
    )

    if special_candidates:

        selected.append(
            special_candidates[0]
        )

    return selected[:limit]
