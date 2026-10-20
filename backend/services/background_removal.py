from __future__ import annotations

import atexit
import os
import subprocess
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


# ============================================================
# CONFIG
# ============================================================

OLD_PROJECT_ROOT = (
    Path.home()
    / "Documents"
    / "AI-Background-Remover"
)

DEFAULT_CANDLE_ENGINE = (
    OLD_PROJECT_ROOT
    / "engines"
    / "candle-birefnet"
    / "target"
    / "release"
    / "examples"
    / "infer_stream"
)

CANDLE_ENGINE = Path(os.environ.get("HABBIT_CANDLE_ENGINE", str(DEFAULT_CANDLE_ENGINE))).expanduser()

DEFAULT_AI_RESOLUTION = 1024

_processes: dict[int, subprocess.Popen] = {}
_locks: dict[int, threading.Lock] = {}


# ============================================================
# ENGINE
# ============================================================

def _check_engine() -> None:
    if not CANDLE_ENGINE.exists():
        raise RuntimeError(
            f"Moteur BiRefNet introuvable : {CANDLE_ENGINE}"
        )


def _read_exactly(stream, byte_count: int) -> bytes:
    result = bytearray()

    while len(result) < byte_count:
        chunk = stream.read(
            byte_count - len(result)
        )

        if not chunk:
            raise RuntimeError(
                "Le moteur BiRefNet s'est arrêté pendant l'inférence."
            )

        result.extend(chunk)

    return bytes(result)


def _start_engine(size: int) -> subprocess.Popen:
    _check_engine()

    print()
    print("=" * 60)
    print("[BACKGROUND] BiRefNet / Candle / Metal")
    print(f"[BACKGROUND] Résolution IA : {size}x{size}")
    print("[BACKGROUND] Chargement du moteur...")
    print("=" * 60)

    process = subprocess.Popen(
        [
            str(CANDLE_ENGINE),
            str(size),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
        bufsize=0,
    )

    if process.stdin is None or process.stdout is None:
        process.kill()
        raise RuntimeError(
            "Pipes BiRefNet indisponibles."
        )

    return process


def _get_engine(size: int) -> subprocess.Popen:
    process = _processes.get(size)

    if process is None or process.poll() is not None:
        process = _start_engine(size)
        _processes[size] = process

    return process


def _get_lock(size: int) -> threading.Lock:
    if size not in _locks:
        _locks[size] = threading.Lock()

    return _locks[size]


def _stop_engines() -> None:
    for process in _processes.values():
        try:
            if process.stdin:
                process.stdin.close()
        except Exception:
            pass

        try:
            process.wait(timeout=2)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


atexit.register(_stop_engines)


# ============================================================
# MASK
# ============================================================

def _calculate_mask(
    image_rgb: Image.Image,
    size: int,
) -> tuple[np.ndarray, float]:

    engine = _get_engine(size)
    lock = _get_lock(size)

    ai_image = image_rgb.resize(
        (size, size),
        Image.Resampling.LANCZOS,
    )

    array = np.asarray(
        ai_image,
        dtype=np.uint8,
    )

    array = np.ascontiguousarray(array)

    with lock:
        if engine.poll() is not None:
            _processes.pop(size, None)
            engine = _get_engine(size)

        start = time.perf_counter()

        engine.stdin.write(
            array.tobytes()
        )
        engine.stdin.flush()

        mask_bytes = _read_exactly(
            engine.stdout,
            size * size,
        )

        duration = (
            time.perf_counter()
            - start
        )

    mask = np.frombuffer(
        mask_bytes,
        dtype=np.uint8,
    ).reshape(
        (size, size)
    )

    return mask, duration


def _clean_alpha(
    alpha: Image.Image,
    low_threshold: int = 3,
    high_threshold: int = 252,
) -> Image.Image:

    alpha = alpha.convert("L")

    alpha = alpha.filter(
        ImageFilter.MedianFilter(size=3)
    )

    alpha = alpha.point(
        lambda p: (
            0
            if p <= low_threshold
            else (
                255
                if p >= high_threshold
                else p
            )
        )
    )

    return alpha


# ============================================================
# PUBLIC SERVICE
# ============================================================

def remove_background(
    image: Image.Image,
    *,
    ai_resolution: int = DEFAULT_AI_RESOLUTION,
    clean_edges: bool = True,
) -> Image.Image:

    if image is None:
        raise ValueError(
            "Aucune image fournie."
        )

    original = image.convert("RGBA")

    width, height = original.size

    rgb = original.convert("RGB")

    print()
    print(
        f"[BACKGROUND] Original : {width}x{height}"
    )
    print(
        f"[BACKGROUND] IA : {ai_resolution}x{ai_resolution}"
    )

    mask, duration = _calculate_mask(
        rgb,
        ai_resolution,
    )

    print(
        f"[BACKGROUND] BiRefNet : {duration:.3f} s"
    )

    alpha = Image.fromarray(
        mask,
        mode="L",
    )

    alpha = alpha.resize(
        (width, height),
        Image.Resampling.LANCZOS,
    )

    if clean_edges:
        alpha = _clean_alpha(alpha)

    result = original.copy()
    result.putalpha(alpha)

    return result


def remove_background_file(
    input_path: str | Path,
    output_path: str | Path,
    *,
    ai_resolution: int = DEFAULT_AI_RESOLUTION,
) -> str:

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Image introuvable : {input_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image = Image.open(input_path)

    result = remove_background(
        image,
        ai_resolution=ai_resolution,
    )

    result.save(
        output_path,
        format="PNG",
    )

    return str(output_path)
