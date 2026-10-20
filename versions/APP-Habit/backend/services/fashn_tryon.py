from __future__ import annotations

from pathlib import Path
import hashlib

import requests


APP_ROOT = Path(
    __file__
).resolve().parents[2]

PERSON_IMAGE = (
    APP_ROOT
    / "backend"
    / "storage"
    / "person"
    / "reference.png"
)

FASHN_URL = (
    "http://127.0.0.1:8765"
)


def _image_path(
    item: dict | None,
) -> Path | None:

    if not item:
        return None

    value = item.get(
        "cutout_path"
    )

    if not value:
        return None

    path = Path(value)

    if not path.is_absolute():
        path = APP_ROOT / path

    if not path.exists():
        return None

    return path


def _outfit_key(
    outfit: dict,
) -> str:

    parts = []

    for name in (
        "haut",
        "bas",
    ):
        item = outfit.get(name)

        if item:
            parts.append(
                str(
                    item.get("id")
                    or item.get(
                        "cutout_path"
                    )
                )
            )

    raw = "|".join(parts)

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:24]


def fashn_available() -> bool:

    try:
        response = requests.get(
            f"{FASHN_URL}/health",
            timeout=2,
        )

        return (
            response.status_code
            == 200
        )

    except Exception:
        return False


def generate_outfit_tryon(
    outfit: dict,
    force: bool = False,
) -> str:

    top_path = _image_path(
        outfit.get("haut")
    )

    bottom_path = _image_path(
        outfit.get("bas")
    )

    if (
        top_path is None
        and bottom_path is None
    ):
        raise RuntimeError(
            "Aucun haut ou bas utilisable."
        )

    payload = {
        "person_path": str(
            PERSON_IMAGE
        ),
        "top_path": (
            str(top_path)
            if top_path
            else None
        ),
        "bottom_path": (
            str(bottom_path)
            if bottom_path
            else None
        ),
        "outfit_key": _outfit_key(
            outfit
        ),
        "force": force,
    }

    try:

        response = requests.post(
            f"{FASHN_URL}/outfit",
            json=payload,
            timeout=300,
        )

    except requests.ConnectionError:

        raise RuntimeError(
            "Le serveur FASHN "
            "n'est pas démarré."
        )

    except requests.Timeout:

        raise RuntimeError(
            "FASHN a dépassé "
            "le temps limite."
        )

    if response.status_code != 200:

        try:
            detail = (
                response
                .json()
                .get(
                    "detail",
                    response.text,
                )
            )
        except Exception:
            detail = response.text

        raise RuntimeError(
            f"Erreur FASHN : {detail}"
        )

    data = response.json()

    generated_path = Path(
        data["path"]
    )

    if not generated_path.exists():
        raise RuntimeError(
            "Image FASHN introuvable."
        )

    return str(
        generated_path
    )
