"""Engine registry — pluggable AI backend management.

Usage
-----
    from app.ai_engine.registry import registry

    # Register adapters at startup
    registry.register(claude_adapter)
    registry.register(metaso_adapter)

    # Use in pipeline
    engine = registry.resolve("claude")          # by name
    engine = registry.resolve()                   # auto-pick best available
    output = await engine.analyze(input)
"""

from __future__ import annotations

from typing import Optional

from app.ai_engine.base import BaseEngineAdapter, EngineInput, EngineOutput


class _EngineRegistry:
    """Manages available AI engine adapters."""

    def __init__(self):
        self._adapters: dict[str, BaseEngineAdapter] = {}

    # ── Registration ────────────────────────────────────────

    def register(self, adapter: BaseEngineAdapter) -> None:
        """Register an adapter by its `.name`."""
        self._adapters[adapter.name] = adapter

    def register_many(self, *adapters: BaseEngineAdapter) -> None:
        for a in adapters:
            self.register(a)

    # ── Lookup ──────────────────────────────────────────────

    def get(self, name: str) -> Optional[BaseEngineAdapter]:
        """Look up an adapter by name.  Returns None if unknown."""
        return self._adapters.get(name)

    def list(self) -> list[BaseEngineAdapter]:
        """Return all registered adapters."""
        return list(self._adapters.values())

    def list_available(self) -> list[BaseEngineAdapter]:
        """Return only adapters that are usable right now."""
        return [a for a in self._adapters.values() if a.is_available()]

    def resolve(self, preferred: Optional[str] = None) -> BaseEngineAdapter:
        """Return the best available adapter.

        1. If *preferred* is given and available → use it
        2. Else first available in registration order
        3. Last resort: raise RuntimeError
        """
        if preferred and preferred in self._adapters:
            candidate = self._adapters[preferred]
            if candidate.is_available():
                return candidate

        available = self.list_available()
        if available:
            return available[0]

        raise RuntimeError("No AI engine adapter is available. "
                           "Set CLAUDE_API_KEY or install a working engine.")

    async def analyze(
        self,
        inp: EngineInput,
        preferred: Optional[str] = None,
    ) -> EngineOutput:
        """Resolve an adapter and run the full pipeline."""
        engine = self.resolve(preferred)
        output = await engine.analyze(inp)
        output.engine_name = engine.name
        return output


# Singleton
registry = _EngineRegistry()
