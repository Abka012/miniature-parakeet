"""Image processing logic using Pillow."""

import base64
import io
from typing import Any

from PIL import Image


def process_image(image_data: str, format_hint: str = "png") -> dict[str, Any]:
    """Decode base64 image, extract metadata, and perform a basic thumbnail resize.

    Returns a structured dict with ``status``, ``metadata``, or an error message.
    """
    try:
        raw = base64.b64decode(image_data)
    except Exception as e:
        return {
            "status": "error",
            "tool": "process_image",
            "input_format": format_hint,
            "error": f"Invalid base64 payload: {e}",
        }

    try:
        img = Image.open(io.BytesIO(raw))

        original = {"width": img.width, "height": img.height, "format": img.format or format_hint, "mode": img.mode}

        img.thumbnail((256, 256))
        if img.mode != "RGB":
            img = img.convert("RGB")

        out = io.BytesIO()
        img.save(out, format="PNG")
        thumbnail_b64 = base64.b64encode(out.getvalue()).decode("ascii")

        return {
            "status": "success",
            "tool": "process_image",
            "input_format": format_hint,
            "result": "Image processed successfully",
            "metadata": {
                "original": original,
                "thumbnail_size_bytes": len(out.getvalue()),
                "thumbnail": thumbnail_b64,
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "tool": "process_image",
            "input_format": format_hint,
            "error": f"Image processing failed: {e}",
        }
