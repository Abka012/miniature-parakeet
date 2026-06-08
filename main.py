#!/usr/bin/env python3
"""Main entry point for the multi-agent system."""

import asyncio
import base64
import io
import os
import struct
import tempfile
import wave
import zlib

from async_media_agents.agents.supervisor import SupervisorAgent
from async_media_agents.graph.workflow import Workflow


def _tiny_png() -> str:
    """Return base64-encoded 1x1 red PNG."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    crc = zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF
    ihdr_chunk = struct.pack(">I", 13) + b"IHDR" + ihdr + struct.pack(">I", crc)
    raw = zlib.compress(b"\x00\xff\x00\x00")
    crc = zlib.crc32(b"IDAT" + raw) & 0xFFFFFFFF
    idat = struct.pack(">I", len(raw)) + b"IDAT" + raw + struct.pack(">I", crc)
    crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", crc)
    return base64.b64encode(sig + ihdr_chunk + idat + iend).decode()


def _tiny_wav() -> str:
    """Return base64-encoded 1s 8kHz mono WAV."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1) 
        w.setsampwidth(1) 
        w.setframerate(8000)
        w.writeframes(b"\x80" * 8000)
    return base64.b64encode(buf.getvalue()).decode()


def _tiny_video() -> str | None:
    """Return base64-encoded 1-frame 2x2 MP4, or None if codec unavailable."""
    try:
        import cv2
        import numpy as np
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        try:
            out = cv2.VideoWriter(tmp.name, cv2.VideoWriter_fourcc(*"mp4v"), 1.0, (2, 2))
            if not out.isOpened():
                return None
            out.write(np.zeros((2, 2, 3), dtype=np.uint8))
            out.release()
            with open(tmp.name, "rb") as f:
                return base64.b64encode(f.read()).decode()
        finally:
            os.unlink(tmp.name)
    except ImportError:
        return None


async def main():
    """Run the multi-agent system."""
    print("=" * 60)
    print("Multi-Agent POC: Async Image/Audio/Video Processing")
    print("=" * 60)

    workflow = Workflow()

    # Example 1: Text-based workflow
    print("\n[Example 1] Text-based task routing")
    print("-" * 40)
    user_input = "Can you analyze this image for me?"
    print(f"User input: '{user_input}'")
    result = await workflow.run(user_input)
    print(f"Result: {result.get('results', {})}")

    # Example 2: Parallel media processing
    print("\n[Example 2] Parallel media processing")
    print("-" * 40)
    img = _tiny_png()
    aud = _tiny_wav()
    vid = _tiny_video()
    print(f"  image: {len(img)} chars  audio: {len(aud)} chars  video: {len(vid) if vid else 0} chars")
    result = await workflow.run_parallel(
        image_data=img,
        audio_data=aud,
        video_data=vid,
    )
    r = result.get("results", {})
    print(f"  image_agent:  {r.get('image_agent', {}).get('processing_result', '<missing>')}")
    print(f"  audio_agent:  {r.get('audio_agent', {}).get('processing_result', '<missing>')}")
    print(f"  video_agent:  {r.get('video_agent', {}).get('processing_result', '<missing>')}")
    print(f"  agents: {r.get('agents_executed', [])}")

    # Example 3: Supervisor workflow
    print("\n[Example 3] Supervisor agent workflow")
    print("-" * 40)
    supervisor = SupervisorAgent()
    supervisor_input = "Process an audio file and extract metadata"
    print(f"Supervisor input: '{supervisor_input}'")
    result = await supervisor.run(supervisor_input)
    print(f"Supervisor result: {result}")

    print("\n" + "=" * 60)
    print("Multi-agent system completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
