from pathlib import Path
import hashlib
import time
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image

from fashn_vton import TryOnPipeline


APP_ROOT = Path(__file__).resolve().parents[2]

FASHN_ROOT = (
    APP_ROOT
    / "engines"
    / "fashn-vton"
)

WEIGHTS_DIR = FASHN_ROOT / "weights"

OUTPUT_DIR = (
    APP_ROOT
    / "backend"
    / "storage"
    / "person"
    / "fashn_generated"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


app = FastAPI(
    title="APP-HABITv2 FASHN VTON",
)


print()
print("=" * 60)
print("CHARGEMENT FASHN VTON")
print("=" * 60)

load_start = time.perf_counter()

pipeline = TryOnPipeline(
    weights_dir=str(WEIGHTS_DIR),
    device="mps",
)

# Apple MPS : une seule inférence FASHN à la fois.
inference_lock = threading.Lock()

print(
    f"✅ FASHN chargé en "
    f"{time.perf_counter() - load_start:.2f} s"
)


class OutfitRequest(BaseModel):
    person_path: str
    top_path: str | None = None
    bottom_path: str | None = None
    outfit_key: str | None = None
    force: bool = False


def absolute_path(value: str | None):
    if not value:
        return None

    path = Path(value)

    if not path.is_absolute():
        path = APP_ROOT / path

    return path


def make_cache_key(
    person_path,
    top_path,
    bottom_path,
    supplied_key=None,
):
    if supplied_key:
        base = supplied_key

    else:
        base = "|".join(
            [
                str(person_path),
                str(top_path or ""),
                str(bottom_path or ""),
            ]
        )

    return hashlib.sha256(
        base.encode("utf-8")
    ).hexdigest()[:24]


@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": "mps",
        "dtype": "float16",
        "timesteps": 8,
    }


@app.post("/outfit")
def generate_outfit(
    request: OutfitRequest,
):
    person_path = absolute_path(
        request.person_path
    )

    top_path = absolute_path(
        request.top_path
    )

    bottom_path = absolute_path(
        request.bottom_path
    )

    if not person_path or not person_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Personne introuvable",
        )

    if top_path and not top_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Haut introuvable",
        )

    if bottom_path and not bottom_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Bas introuvable",
        )

    if not top_path and not bottom_path:
        raise HTTPException(
            status_code=400,
            detail="Aucun vêtement fourni",
        )

    cache_key = make_cache_key(
        person_path,
        top_path,
        bottom_path,
        request.outfit_key,
    )

    output_path = (
        OUTPUT_DIR
        / f"look_{cache_key}.png"
    )

    if (
        output_path.exists()
        and not request.force
    ):
        return {
            "status": "cached",
            "path": str(output_path),
            "generation_time": 0.0,
        }

    current = Image.open(
        person_path
    ).convert("RGB")

    total_start = time.perf_counter()

    top_time = 0.0
    bottom_time = 0.0

    # ------------------------------------------------------
    # BAS EN PREMIER
    # ------------------------------------------------------

    if bottom_path:

        garment = Image.open(
            bottom_path
        ).convert("RGB")

        start = time.perf_counter()

        with inference_lock:
            result = pipeline(
                current,
                garment,
                category="bottoms",
                num_timesteps=8,
            )

        bottom_time = (
            time.perf_counter()
            - start
        )

        current = result.images[0]

    # ------------------------------------------------------
    # HAUT EN SECOND
    # ------------------------------------------------------

    if top_path:

        garment = Image.open(
            top_path
        ).convert("RGB")

        start = time.perf_counter()

        with inference_lock:
            result = pipeline(
                current,
                garment,
                category="tops",
                num_timesteps=8,
            )

        top_time = (
            time.perf_counter()
            - start
        )

        current = result.images[0]

    current.save(
        output_path
    )

    total_time = (
        time.perf_counter()
        - total_start
    )

    return {
        "status": "generated",
        "path": str(output_path),
        "top_time": top_time,
        "bottom_time": bottom_time,
        "generation_time": total_time,
    }


# ============================================================
# LANCEMENT SERVEUR
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8765,
        log_level="info",
    )
