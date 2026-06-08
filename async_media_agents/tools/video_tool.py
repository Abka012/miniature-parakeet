"""Video processing tool using FastMCP."""

from fastmcp import FastMCP

from ..tools.mcp_client import mcp_client

# Create FastMCP instance
video_mcp = FastMCP(name="video_processor")


@video_mcp.tool()
async def process_video(
    video_data: str,
    format: str = "mp4",
) -> str:
    """Process video data and return results as string."""
    result = await mcp_client.process_video(video_data, format)
    return f"Video processed successfully: {result['result']}"


@video_mcp.tool()
async def extract_video_info(video_data: str) -> dict:
    """Extract metadata from video."""
    result = await mcp_client.process_video(video_data, "mp4")
    return {
        "status": result["status"],
        "duration": result["metadata"]["duration"],
        "fps": result["metadata"]["fps"],
    }
