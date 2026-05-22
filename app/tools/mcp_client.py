"""MCP client wrapper for FastMCP integration."""

import asyncio
from typing import Any

from .mcp_server import MCPServer, mcp_server


class MCPClient:
    """Client for interacting with MCP tools."""

    def __init__(self) -> None:
        self.server: MCPServer = mcp_server

    async def process_image(
        self, image_data: str, format: str = "png"
    ) -> dict[str, Any]:
        """Process image using MCP tool."""
        return await self.server.run_image_tool(image_data, format)

    async def process_audio(
        self, audio_data: str, format: str = "mp3"
    ) -> dict[str, Any]:
        """Process audio using MCP tool."""
        return await self.server.run_audio_tool(audio_data, format)

    async def process_video(
        self, video_data: str, format: str = "mp4"
    ) -> dict[str, Any]:
        """Process video using MCP tool."""
        return await self.server.run_video_tool(video_data, format)

    async def batch_process(
        self,
        image_data: str | None = None,
        audio_data: str | None = None,
        video_data: str | None = None,
    ) -> dict[str, Any]:
        """Process multiple types in parallel."""
        results = {}

        # Run all processing tasks in parallel
        tasks = []
        if image_data:
            tasks.append(self.process_image(image_data))
        if audio_data:
            tasks.append(self.process_audio(audio_data))
        if video_data:
            tasks.append(self.process_video(video_data))

        if tasks:
            processed_results = await asyncio.gather(*tasks)
            for result in processed_results:
                results[result["tool"]] = result

        return results


# Singleton instance
mcp_client = MCPClient()
