"""Audio processing logic using stdlib ``wave`` (zero extra dependencies)."""

import base64
import io
from typing import Any

import wave


def process_audio(audio_data: str, format_hint: str = "wav") -> dict[str, Any]:
    """Decode base64 audio and extract WAV metadata (duration, sample rate, etc.).

    WAV is handled natively via stdlib.  Non-WAV data will raise a ``wave.Error``
    and return a clean error dict.
    """
    try:
        raw = base64.b64decode(audio_data)
    except Exception as e:
        return {
            "status": "error",
            "tool": "process_audio",
            "input_format": format_hint,
            "error": f"Invalid base64 payload: {e}",
        }

    try:
        with wave.open(io.BytesIO(raw), "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            channels = wav.getnchannels()
            sampwidth = wav.getsampwidth()
            duration = frames / rate if rate > 0 else 0.0

        return {
            "status": "success",
            "tool": "process_audio",
            "input_format": format_hint,
            "result": "Audio processed successfully",
            "metadata": {
                "duration_seconds": round(duration, 3),
                "sample_rate": rate,
                "channels": channels,
                "sample_width_bytes": sampwidth,
                "total_frames": frames,
            },
        }
    except wave.Error as e:
        return {
            "status": "error",
            "tool": "process_audio",
            "input_format": format_hint,
            "error": f"Audio processing failed (WAV format required): {e}",
        }
    except Exception as e:
        return {
            "status": "error",
            "tool": "process_audio",
            "input_format": format_hint,
            "error": f"Audio processing failed: {e}",
        }
