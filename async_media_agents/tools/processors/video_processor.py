"""Video processing logic using opencv-python-headless."""

import base64
import os
import tempfile
from typing import Any

import cv2


def process_video(video_data: str, format_hint: str = "mp4") -> dict[str, Any]:
    """Decode base64 video, extract metadata (fps, resolution, duration).

    OpenCV's ``VideoCapture`` requires a filesystem path, so the payload is
    written to a temporary file that is cleaned up before returning.
    """
    try:
        raw = base64.b64decode(video_data)
    except Exception as e:
        return {
            "status": "error",
            "tool": "process_video",
            "input_format": format_hint,
            "error": f"Invalid base64 payload: {e}",
        }

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{format_hint}", delete=False) as f:
            f.write(raw)
            tmp_path = f.name

        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return {
                "status": "error",
                "tool": "process_video",
                "input_format": format_hint,
                "error": "Could not open video stream – unsupported format or corrupted data",
            }

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0.0

        cap.release()

        return {
            "status": "success",
            "tool": "process_video",
            "input_format": format_hint,
            "result": "Video processed successfully",
            "metadata": {
                "duration_seconds": round(duration, 3),
                "fps": round(fps, 2) if fps > 0 else 0,
                "total_frames": total_frames,
                "width": width,
                "height": height,
                "resolution": f"{width}x{height}",
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "tool": "process_video",
            "input_format": format_hint,
            "error": f"Video processing failed: {e}",
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
