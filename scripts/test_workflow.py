#!/usr/bin/env python3
"""
Step 1 & 2: Payload Verification + Real Processing.

Validates that the pipeline can transport real base64-encoded payloads
and that the new real processors (Pillow, stdlib wave, OpenCV) work correctly.

Usage:
    python scripts/test_workflow.py
"""

import asyncio
import base64
import io
import logging
import os
import struct
import sys
import tempfile
from typing import Callable
import wave
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.audio_agent import AudioAgent
from app.agents.image_agent import ImageAgent
from app.agents.video_agent import VideoAgent
from app.graph.workflow import Workflow
from app.state.state import AgentState
from app.tools.mcp_client import mcp_client

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

PASS = "✓"
FAIL = "✗"

# ── Payload generators ───────────────────────────────────────────


def make_tiny_png_bytes() -> bytes:
    """Minimal 1×1 red PNG (stdlib: struct + zlib)."""
    signature = b"\x89PNG\r\n\x1a\n"

    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
    ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)

    raw = b"\x00\xff\x00\x00"
    compressed = zlib.compress(raw)
    idat_crc = zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
    idat = struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc)

    iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

    return signature + ihdr + idat + iend


def make_tiny_wav_bytes() -> bytes:
    """Minimal valid WAV: 1 sec, 8 kHz, mono, 8-bit unsigned."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(1)
        wav.setframerate(8000)
        wav.writeframes(b"\x80" * 8000)
    return buf.getvalue()


def make_tiny_video_bytes() -> bytes | None:
    """Minimal 1-frame 2×2 video via OpenCV (may fail if codec unavailable)."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None

    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(tmp.name, fourcc, 1.0, (2, 2))
        if not out.isOpened():
            out.release()
            return None
        frame = np.zeros((2, 2, 3), dtype=np.uint8)
        out.write(frame)
        out.release()
        with open(tmp.name, "rb") as f:
            return f.read()
    except Exception:
        return None
    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


# ── Tests ────────────────────────────────────────────────────────


async def test_payload_integrity() -> bool:
    """Generate → base64 → decode → verify bytes match."""
    logger.info("── test_payload_integrity ─────────────────────")
    ok = True

    video_raw = make_tiny_video_bytes()
    generators = [("PNG", make_tiny_png_bytes), ("WAV", make_tiny_wav_bytes)]
    if video_raw:
        generators.append(("MP4", lambda: video_raw))

    for label, make_fn in generators:
        original = make_fn()
        encoded = b64(original)
        decoded = base64.b64decode(encoded)
        if decoded == original:
            logger.info(f"  {PASS} {label}: {len(original)} B -> {len(encoded)} chars -> {len(decoded)} B  OK")
        else:
            logger.error(f"  {FAIL} {label}: integrity check failed")
            ok = False
    return ok


async def test_run_parallel() -> bool:
    """Feed all three real payloads through workflow.run_parallel()."""
    logger.info("── test_run_parallel ──────────────────────────")

    wf = Workflow()
    img = b64(make_tiny_png_bytes())
    aud = b64(make_tiny_wav_bytes())
    vid_raw = make_tiny_video_bytes()
    vid = b64(vid_raw) if vid_raw else None

    logger.info(f"  image payload: {len(img):>8} chars")
    logger.info(f"  audio payload: {len(aud):>8} chars")
    logger.info(f"  video payload: {len(vid):>8} chars" if vid else "  video: skipped (codec unavailable)")

    kwargs = {"image_data": img, "audio_data": aud}
    if vid:
        kwargs["video_data"] = vid

    try:
        result = await wf.run_parallel(**kwargs)
        td = result.get("task_data", {})
        assert td.get("image_data") == img, "image_data mismatch"
        assert td.get("audio_data") == aud, "audio_data mismatch"
        if vid:
            assert td.get("video_data") == vid, "video_data mismatch"
        assert result.get("error") is None, f"error set: {result['error']}"
        logger.info(f"  {PASS} payloads preserved ({len(td)} keys), no errors")
        return True
    except Exception as e:
        logger.error(f"  {FAIL} {e}")
        return False


async def test_partial_payloads() -> bool:
    """run_parallel with only 1-2 payloads (None for others)."""
    logger.info("── test_partial_payloads ──────────────────────")
    wf = Workflow()
    ok = True

    cases = [
        ("only image", {"image_data": b64(make_tiny_png_bytes())}),
        ("only audio", {"audio_data": b64(make_tiny_wav_bytes())}),
        ("image+audio", {"image_data": b64(make_tiny_png_bytes()), "audio_data": b64(make_tiny_wav_bytes())}),
    ]

    for desc, kwargs in cases:
        try:
            result = await wf.run_parallel(**kwargs)
            td = result.get("task_data", {})
            for k in ("image_data", "audio_data", "video_data"):
                if k in kwargs:
                    assert td.get(k) == kwargs[k], f"{k} mismatch"
            logger.info(f"  {PASS} {desc}: keys = {list(td.keys())}")
        except Exception as e:
            logger.error(f"  {FAIL} {desc}: {e}")
            ok = False
    return ok


async def test_individual_agents() -> bool:
    """Each agent called directly with a real base64 payload."""
    logger.info("── test_individual_agents ─────────────────────")
    ok = True

    specs: list[tuple[str, type[ImageAgent] | type[AudioAgent] | type[VideoAgent], str, str, Callable[[], bytes]]] = [
        ("ImageAgent", ImageAgent, "image_data", "image_agent", make_tiny_png_bytes),
        ("AudioAgent", AudioAgent, "audio_data", "audio_agent", make_tiny_wav_bytes),
    ]

    video_raw = make_tiny_video_bytes()
    if video_raw:
        specs.append(("VideoAgent", VideoAgent, "video_data", "video_agent", lambda: video_raw))

    for name, AgentCls, data_key, result_key, payload_fn in specs:
        try:
            agent = AgentCls()
            state: AgentState = {
                "messages": [],
                "task_type": result_key,
                "task_data": {data_key: b64(payload_fn())},
                "results": {},
                "metadata": {},
                "current_agent": "",
                "error": None,
            }
            result = await agent.run(state)
            r = result.get("results", {}).get(result_key, {})
            assert r.get("status") == "completed", f"status not completed: {r}"
            logger.info(f"  {PASS} {name}: status={r['status']} result={r.get('processing_result', '<none>')}")
        except Exception as e:
            logger.error(f"  {FAIL} {name}: {e}")
            ok = False
    return ok


async def test_mcp_client_batch() -> bool:
    """MCPClient.batch_process with all available payloads."""
    logger.info("── test_mcp_client_batch ──────────────────────")
    try:
        inputs = {"image_data": b64(make_tiny_png_bytes()), "audio_data": b64(make_tiny_wav_bytes())}
        video_raw = make_tiny_video_bytes()
        if video_raw:
            inputs["video_data"] = b64(video_raw)

        results = await mcp_client.batch_process(**inputs)
        assert "process_image" in results
        assert "process_audio" in results
        for name, r in results.items():
            assert r["status"] == "success", f"{name}: {r}"
        logger.info(f"  {PASS} {len(results)} tools returned success")
        return True
    except Exception as e:
        logger.error(f"  {FAIL} {e}")
        return False


async def test_real_image_processor() -> bool:
    """Verify the image processor extracts correct metadata from the tiny PNG."""
    logger.info("── test_real_image_processor ──────────────────")
    try:
        result = await mcp_client.process_image(b64(make_tiny_png_bytes()))
        assert result["status"] == "success"
        meta = result["metadata"]
        assert meta["original"]["width"] == 1
        assert meta["original"]["height"] == 1
        assert meta["original"]["format"] == "PNG"
        logger.info(f"  {PASS} metadata: {meta['original']}")
        return True
    except Exception as e:
        logger.error(f"  {FAIL} {e}")
        return False


async def test_real_audio_processor() -> bool:
    """Verify the audio processor extracts correct metadata from the tiny WAV."""
    logger.info("── test_real_audio_processor ──────────────────")
    try:
        result = await mcp_client.process_audio(b64(make_tiny_wav_bytes()))
        assert result["status"] == "success"
        meta = result["metadata"]
        assert meta["sample_rate"] == 8000
        assert meta["channels"] == 1
        assert meta["duration_seconds"] == 1.0
        logger.info(f"  {PASS} metadata: {meta}")
        return True
    except Exception as e:
        logger.error(f"  {FAIL} {e}")
        return False


async def test_robust_error_handling() -> bool:
    """Verify processors gracefully reject invalid/corrupted payloads."""
    logger.info("── test_robust_error_handling ─────────────────")
    ok = True

    corrupted = "this-is-not-valid-base64!!"
    garbage = b64(os.urandom(4096))

    for label, call in [
        ("image (corrupt base64)", mcp_client.process_image(corrupted)),
        ("image (random bytes)", mcp_client.process_image(garbage)),
        ("audio (corrupt base64)", mcp_client.process_audio(corrupted)),
        ("audio (random bytes)", mcp_client.process_audio(garbage)),
    ]:
        try:
            result = await call
            assert result["status"] == "error", f"expected error for {label}, got {result['status']}"
            assert "error" in result, f"no error message in result for {label}"
            logger.info(f"  {PASS} {label} -> {result['status']}")
        except Exception as e:
            logger.error(f"  {FAIL} {label}: {e}")
            ok = False

    return ok


async def main() -> bool:
    logger.info("")
    logger.info("╔══════════════════════════════════════════════════╗")
    logger.info("║   Payload Verification + Real Processing        ║")
    logger.info("╚══════════════════════════════════════════════════╝")
    logger.info("")

    tests = [
        ("payload_integrity", test_payload_integrity()),
        ("real_image_processor", test_real_image_processor()),
        ("real_audio_processor", test_real_audio_processor()),
        ("run_parallel (all)", test_run_parallel()),
        ("partial_payloads", test_partial_payloads()),
        ("individual_agents", test_individual_agents()),
        ("mcp_client_batch", test_mcp_client_batch()),
        ("robust_error_handling", test_robust_error_handling()),
    ]

    results: dict[str, bool] = {}
    for name, coro in tests:
        results[name] = await coro
        logger.info("")

    logger.info("════════════════════════════════════════════════════")
    logger.info(" SUMMARY")
    for name, passed in results.items():
        sym = PASS if passed else FAIL
        logger.info(f"  {sym}  {name}")

    all_pass = all(results.values())
    logger.info("")
    if all_pass:
        logger.info(f" {PASS} All tests passed. Real processing pipeline is working.")
    else:
        logger.warning(f" {FAIL} Some tests failed. Review above.")
    logger.info("")

    return all_pass


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
