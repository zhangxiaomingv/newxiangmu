"""AI Engine — pluggable analysis backends.

Usage
-----
    from app.ai_engine import registry, EngineInput

    result = await registry.analyze(
        EngineInput(brand="Acme", url="https://acme.com", …),
        preferred="dual",              # or "claude", "metaso", "mock"
    )

Available engines (auto-detected at startup):
  - dual    → 豆包 + DeepSeek 双模型检测 (needs DOUBAO_API_KEY / DEEPSEEK_API_KEY)
  - claude  → Claude API (needs CLAUDE_API_KEY)
  - metaso  → Built-in heuristic (always available)
  - mock    → Canned data for dev/demo
"""

from app.ai_engine.base import EngineInput, EngineOutput
from app.ai_engine.registry import registry

# ── Register built-in adapters ──────────────────────────────
from app.ai_engine.claude_adapter import ClaudeAdapter
from app.ai_engine.metaso_adapter import HeuristicAdapter
from app.ai_engine.mock_adapter import MockAdapter
from app.ai_engine.dual_model_engine import DualModelEngine

registry.register_many(
    DualModelEngine(),    # 豆包 + DeepSeek 双模型 (needs API keys)
    ClaudeAdapter(),      # Claude API (needs CLAUDE_API_KEY)
    HeuristicAdapter(),   # Built-in heuristic (always available)
    MockAdapter(),        # Canned demo data (always available)
)

# ── Re-export key symbols ──────────────────────────────────
__all__ = [
    "registry",
    "EngineInput",
    "EngineOutput",
]
