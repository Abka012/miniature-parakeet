"""Image processing tool using FastMCP."""

from fastmcp import FastMCP

from ..tools.mcp_client import mcp_client

# Create FastMCP instance
image_mcp = FastMCP(name="image_processor")


@image_mcp.tool()
async def process_image(
    image_data: str,
    format: str = "png",
) -> str:
    """Process image data and return results as string."""
    result = await mcp_client.process_image(image_data, format)
    return f"Image processed successfully: {result['result']}"


@image_mcp.tool()
async def extract_image_info(image_data: str) -> dict:
    """Extract metadata from image."""
    result = await mcp_client.process_image(image_data, "png")
    return {
        "status": result["status"],
        "width": result["metadata"]["width"],
        "height": result["metadata"]["height"],
    }
