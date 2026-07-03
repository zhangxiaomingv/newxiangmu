"""AI Engine — pluggable analysis backends.

Usage
-----
    from app.ai_engine import registry, EngineInput

    result = await registry.analyze(
        EngineInput(brand="Acme", url="https://acme.com", …),
        preferred="claude",           # or "metaso", "mock"
    )

Available engines (auto-detected at startup):
  - claude  → Claude API (needs CLAUDE_API_KEY)
  - metaso  → 秘塔 AI 搜索 (free, no login)
  - mock    → Canned data for dev/demo
"""

from app.ai_engine.base import EngineInput, EngineOutput
from app.ai_engine.registry import registry

# ── Register built-in adapters ──────────────────────────────
from app.ai_engine.claude_adapter import ClaudeAdapter
from app.ai_engine.metaso_adapter import HeuristicAdapter
from app.ai_engine.mock_adapter import MockAdapter

registry.register_many(
    ClaudeAdapter(),     # needs CLAUDE_API_KEY
    HeuristicAdapter(),  # built-in heuristic (always available)
    MockAdapter(),       # canned demo data (always available)
)

# ── Re-export key symbols ──────────────────────────────────
__all__ = [
    "registry",
    "EngineInput",
    "EngineOutput",
]
