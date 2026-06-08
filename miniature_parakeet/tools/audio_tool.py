"""Audio processing tool using FastMCP."""

from fastmcp import FastMCP

from ..tools.mcp_client import mcp_client

# Create FastMCP instance
audio_mcp = FastMCP(name="audio_processor")


@audio_mcp.tool()
async def process_audio(
    audio_data: str,
    format: str = "mp3",
) -> str:
    """Process audio data and return results as string."""
    result = await mcp_client.process_audio(audio_data, format)
    return f"Audio processed successfully: {result['result']}"


@audio_mcp.tool()
async def extract_audio_info(audio_data: str) -> dict:
    """Extract metadata from audio."""
    result = await mcp_client.process_audio(audio_data, "mp3")
    return {
        "status": result["status"],
        "duration": result["metadata"]["duration"],
        "sample_rate": result["metadata"]["sample_rate"],
    }
