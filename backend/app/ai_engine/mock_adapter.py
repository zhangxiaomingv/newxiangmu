"""Mock adapter — returns canned data for development / demo.

Used when no real AI engine is configured (no CLAUDE_API_KEY, no
other engine available).  Always available.
"""

import json

from app.ai_engine.base import BaseEngineAdapter, EngineInput, EngineOutput
from app.models.schemas import AIPerceptionProfile, GapItem, ActionItem, RoadmapStage


MOCK_PERCEPTION = {
    "summary": "Mock analysis — set CLAUDE_API_KEY for real results, "
               "or use the 秘塔 engine for AI search based analysis.",
    "key_attributes": ["innovative", "technology-driven", "user-focused"],
    "known_for": ["digital solutions", "technology products"],
    "confusion_areas": ["unclear positioning", "broad market focus"],
    "competitor_context": "Operates in a competitive landscape with several established players.",
}

MOCK_GAPS = [
    GapItem(category="structure", severity="critical",
            description="Missing schema.org Organization markup",
            evidence="No JSON-LD found on homepage"),
    GapItem(category="content", severity="moderate",
            description="Value proposition not immediately clear",
            evidence="Meta description lacks unique selling points"),
    GapItem(category="authority", severity="minor",
            description="Limited external references found",
            evidence="No press mentions or certifications mentioned"),
]

MOCK_SUGGESTIONS = [
    ActionItem(priority="immediate", title="Add Organization Schema",
               description="Add schema.org/Organization JSON-LD markup",
               effort="low", impact="high"),
    ActionItem(priority="immediate", title="Clarify Meta Description",
               description="Rewrite meta description with clear value prop",
               effort="low", impact="medium"),
    ActionItem(priority="medium_term", title="Build Knowledge Base",
               description="Create comprehensive about page with team/product/vision",
               effort="medium", impact="high"),
]

MOCK_ROADMAP = [
    RoadmapStage(stage=1, title="Foundation",
                 description="Basic AI recognition",
                 actions=["Add schema markup", "Optimize meta tags"]),
    RoadmapStage(stage=2, title="Clarity",
                 description="Consistent AI understanding",
                 actions=["Clear value prop", "About page content"]),
    RoadmapStage(stage=3, title="Authority",
                 description="AI trust signals",
                 actions=["Get press mentions", "Build backlinks"]),
    RoadmapStage(stage=4, title="Rich Presence",
                 description="Multi-source consistency",
                 actions=["Knowledge graph", "Social proof"]),
    RoadmapStage(stage=5, title="AI-native",
                 description="AI ecosystem optimized",
                 actions=["AI-friendly content structure", "API-first presence"]),
]


class MockAdapter(BaseEngineAdapter):
    """Returns canned data.  Always available; useful for dev/demo."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def display_name(self) -> str:
        return "Demo (Mock)"

    def is_available(self) -> bool:
        return True

    async def analyze(self, inp: EngineInput) -> EngineOutput:
        return EngineOutput(
            perception=AIPerceptionProfile(**MOCK_PERCEPTION),
            gaps=MOCK_GAPS,
            suggestions=MOCK_SUGGESTIONS,
            roadmap=MOCK_ROADMAP,
            engine_name=self.name,
            source_raw=json.dumps(MOCK_PERCEPTION, indent=2),
        )
