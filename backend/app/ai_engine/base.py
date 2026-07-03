"""Abstract base for AI engine adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from app.models.schemas import (
    AIPerceptionProfile,
    GapItem,
    ActionItem,
    RoadmapStage,
)


@dataclass
class EngineInput:
    """Standardised input for every adapter.

    The crawler populates all text/content fields; adapters use them
    to produce a perception analysis, gap detection, and optimisation
    suggestions.
    """
    brand: str
    url: str
    website_content: str
    about_content: str
    structured_data: dict
    output_language: str = "English"

    # Optional extra metadata from the crawler (used by heuristic adapters)
    page_title: str = ""
    meta_description: str = ""
    headings: list[dict] = field(default_factory=list)  # [{"level": "h1", "text": "..."}, ...]


@dataclass
class EngineOutput:
    """Standardised output from every adapter."""
    perception: AIPerceptionProfile
    gaps: list[GapItem]
    suggestions: list[ActionItem]
    roadmap: list[RoadmapStage]
    engine_name: str = ""       # which adapter produced this
    source_raw: str = ""        # raw AI search text when applicable


class BaseEngineAdapter(ABC):
    """Each adapter wraps one AI backend (Claude, 秘塔, Perplexity, …)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique adapter identifier, e.g. 'claude', 'metaso', 'mock'."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name shown in UI, e.g. 'Claude API', '秘塔 AI 搜索'."""
        ...

    @abstractmethod
    async def analyze(self, inp: EngineInput) -> EngineOutput:
        """Run the full analysis pipeline and return structured output.

        Every adapter must implement the 3-step pipeline:
          1. Perceive — how does the AI see this brand
          2. Detect gaps — what's missing
          3. Generate optimisations — what to do about it
        """
        ...

    def is_available(self) -> bool:
        """Returns True if this engine is usable right now.

        Override for engines that need runtime checks (API key present,
        network reachable, etc.).  Defaults to True.
        """
        return True
