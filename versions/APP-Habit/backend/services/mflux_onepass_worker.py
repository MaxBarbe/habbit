from __future__ import annotations

import json
import sys
from pathlib import Path

from mflux.models.common.config.model_config import ModelConfig
from mflux.models.flux.variants.in_context.flux_in_context_fill import (
    Flux1InContextFill,
)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: worker.py job.json")

    job_path = Path(sys.argv[1])
    job = json.loads(job_path.read_text())

    flux = Flux1InContextFill(
        model_config=ModelConfig.dev_fill_catvton(),
        quantize=int(job.get("quantize", 4)),
    )

    image = flux.generate_image(
        seed=int(job.get("seed", 1)),
        prompt=job["prompt"],
        width=int(job["width"]),
        height=int(job["height"]),
        guidance=float(job.get("guidance", 30.0)),
        scheduler="linear",
        num_inference_steps=int(job.get("steps", 8)),
        left_image_path=job["board"],
        right_image_path=job["person"],
        masked_image_path=job["mask"],
    )

    image.get_right_half().save(
        path=Path(job["output"]),
        export_json_metadata=False,
    )

    print(f"DONE:{job['output']}", flush=True)


if __name__ == "__main__":
    main()
