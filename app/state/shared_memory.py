"""Shared state utilities for multi-agent system."""

from typing import Any


class SharedMemory:
    """Shared memory/context for agent coordination."""

    def __init__(self) -> None:
        self._memory: dict[str, Any] = {}
        self._lock: Any = None  # Can be used with asyncio.Lock

    async def get(self, key: str) -> Any | None:
        """Get value from shared memory."""
        return self._memory.get(key)

    async def set(self, key: str, value: Any) -> None:
        """Set value in shared memory."""
        self._memory[key] = value

    async def update(self, key: str, value: Any) -> None:
        """Update value in shared memory."""
        if key in self._memory:
            if isinstance(self._memory[key], dict) and isinstance(value, dict):
                self._memory[key].update(value)
            else:
                self._memory[key] = value
        else:
            self._memory[key] = value

    async def delete(self, key: str) -> bool:
        """Delete value from shared memory."""
        if key in self._memory:
            del self._memory[key]
            return True
        return False

    async def clear(self) -> None:
        """Clear all memory."""
        self._memory.clear()

    async def get_all(self) -> dict[str, Any]:
        """Get all memory."""
        return self._memory.copy()

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory."""
        return key in self._memory


# Global shared memory instance
shared_memory = SharedMemory()
