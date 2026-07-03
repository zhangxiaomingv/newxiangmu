"""Claude API adapter — the default reasoning engine."""

import json

from app.config import CLAUDE_API_KEY, CLAUDE_MODEL
from app.ai_engine.base import BaseEngineAdapter, EngineInput, EngineOutput
from app.ai_engine.prompts import PERCEPTION_PROMPT, GAP_PROMPT, OPTIMIZATION_PROMPT
from app.models.schemas import AIPerceptionProfile, GapItem, ActionItem, RoadmapStage


class ClaudeAdapter(BaseEngineAdapter):
    """Adapter that calls the Anthropic Claude API directly."""

    @property
    def name(self) -> str:
        return "claude"

    @property
    def display_name(self) -> str:
        return "Claude API"

    def is_available(self) -> bool:
        return bool(CLAUDE_API_KEY)

    async def analyze(self, inp: EngineInput) -> EngineOutput:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=CLAUDE_API_KEY)
        output_language = inp.output_language

        # ── Step 1: Perception ──────────────────────────────
        prompt = PERCEPTION_PROMPT.format(
            brand=inp.brand,
            url=inp.url,
            website_content=inp.website_content[:8000],
            about_content=inp.about_content[:4000],
            structured_data=str(inp.structured_data)[:2000],
            output_language=output_language,
        )
        raw_perception = await self._call(client, prompt)
        perception_data = _parse_json(raw_perception)
        perception = AIPerceptionProfile(
            summary=perception_data.get("summary", "Analysis pending"),
            key_attributes=perception_data.get("key_attributes", []),
            known_for=perception_data.get("known_for", []),
            confusion_areas=perception_data.get("confusion_areas", []),
            competitor_context=perception_data.get("competitor_context", ""),
        )

        # ── Step 2: Gaps ──────────────────────────────────
        prompt = GAP_PROMPT.format(
            brand=inp.brand,
            url=inp.url,
            perception_analysis=perception.model_dump_json(indent=2),
            website_content=inp.website_content[:8000],
            output_language=output_language,
        )
        raw_gaps = await self._call(client, prompt)
        gaps_data = _parse_json(raw_gaps)
        if isinstance(gaps_data, list):
            gaps = [
                GapItem(category=g.get("category", "content"),
                        severity=g.get("severity", "moderate"),
                        description=g.get("description", ""),
                        evidence=g.get("evidence", ""))
                for g in gaps_data
            ]
        else:
            gaps = []

        # ── Step 3: Optimisation ─────────────────────────
        prompt = OPTIMIZATION_PROMPT.format(
            brand=inp.brand,
            perception_analysis=perception.model_dump_json(indent=2),
            gap_analysis=json.dumps([g.model_dump() for g in gaps], indent=2),
            output_language=output_language,
        )
        raw_opt = await self._call(client, prompt)
        opt_data = _parse_json(raw_opt)

        immediate = opt_data.get("immediate_actions", [])
        medium = opt_data.get("medium_term_actions", [])
        suggestions = []
        for a in immediate:
            suggestions.append(ActionItem(priority="immediate", **a))
        for a in medium:
            suggestions.append(ActionItem(priority="medium_term", **a))

        roadmap = [RoadmapStage(**s) for s in opt_data.get("roadmap", [])]

        return EngineOutput(
            perception=perception,
            gaps=gaps,
            suggestions=suggestions,
            roadmap=roadmap,
            engine_name=self.name,
            source_raw=raw_perception,
        )

    async def _call(self, client, prompt: str) -> str:
        kwargs = {
            "model": CLAUDE_MODEL,
            "max_tokens": 4096,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = await client.messages.create(**kwargs)
        return resp.content[0].text


# ── Shared JSON parser ──────────────────────────────────────

def _parse_json(raw: str) -> dict | list:
    """Extract JSON from LLM response (handles markdown fences)."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    first_char = text[0] if text else ""

    if first_char == "[":
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end >= 0:
            text = text[start: end + 1]
    elif first_char == "{":
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= 0:
            text = text[start: end + 1]
    else:
        start = text.find("[")
        if start >= 0:
            end = text.rfind("]")
            if end >= 0:
                text = text[start: end + 1]
            first_char = "["
        else:
            start = text.find("{")
            if start >= 0:
                end = text.rfind("}")
                if end >= 0:
                    text = text[start: end + 1]
                first_char = "{"

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return [] if first_char == "[" else {}
