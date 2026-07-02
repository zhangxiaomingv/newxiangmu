"""AI Engine — 3 core prompts for brand perception analysis."""

from app.config import CLAUDE_API_KEY, CLAUDE_MODEL
from app.models.schemas import AIPerceptionProfile, GapItem, ActionItem, RoadmapStage

# ── Prompt Templates ──────────────────────────────────────

PERCEPTION_PROMPT = """You are an AI brand perception analyst. Your job is to simulate how an AI system (like ChatGPT, Google AI, or DeepSeek) would perceive a given brand based on its public web presence.

Brand: {brand}
Website URL: {url}

Website Content:
{website_content}

About Page Content:
{about_content}

Structured Data Found:
{structured_data}

Analyze how AI systems would perceive this brand. Consider:
1. Is the brand clearly defined? Can AI tell what they do?
2. What key attributes would AI associate with this brand?
3. What is the brand known for vs. what do they actually do?
4. Where would AI be confused or ambiguous about this brand?
5. How does the brand position against competitors?

Return your analysis as a JSON object with these fields:
- summary (str): One-paragraph summary of AI's perception
- key_attributes (list[str]): 3-5 key attributes AI would associate
- known_for (list[str]): 2-4 things the brand is known for
- confusion_areas (list[str]): 2-4 areas of ambiguity or confusion
- competitor_context (str): Where the brand sits in competitive landscape

Be honest and critical — don't sugarcoat. If the brand's positioning is unclear, say so."""


GAP_PROMPT = """You are an AI visibility auditor. Based on the brand analysis below, identify what information is missing or insufficient for AI systems to properly understand this brand.

Brand: {brand}
Website URL: {url}

AI Perception Analysis:
{perception_analysis}

Website Content:
{website_content}

Identify gaps in these categories:
1. **Structure**: Missing schema.org markup, poor HTML semantics, missing meta tags
2. **Content**: Missing key information, unclear messaging, insufficient detail
3. **Authority**: Missing external validation, citations, social proof
4. **Clarity**: Ambiguous positioning, unclear value proposition

Return as a JSON array of gap items, each with:
- category (str): "structure" | "content" | "authority" | "clarity"
- severity (str): "critical" | "moderate" | "minor"
- description (str): What is missing or insufficient
- evidence (str): Evidence from the content that supports this gap

Be specific and actionable — not generic SEO advice."""


OPTIMIZATION_PROMPT = """You are an AI visibility strategist. Based on the brand analysis and identified gaps, generate concrete steps to improve AI visibility.

Brand: {brand}

Current AI Perception:
{perception_analysis}

Identified Gaps:
{gap_analysis}

Generate recommendations in two categories:

1. **Immediate Actions** (7 days): Quick wins — can be done with existing resources
2. **Medium Term** (30 days): More involved changes

Also generate a 5-stage AI visibility roadmap that shows the progression from basic to advanced presence.

Return as JSON:
{{
  "immediate_actions": [
    {{"title": "...", "description": "...", "effort": "low|medium|high", "impact": "low|medium|high"}}
  ],
  "medium_term_actions": [
    {{"title": "...", "description": "...", "effort": "low|medium|high", "impact": "low|medium|high"}}
  ],
  "roadmap": [
    {{"stage": 1, "title": "...", "description": "...", "actions": ["...", "..."]}},
    ... (5 stages total)
  ]
}}

Stage progression:
- Stage 1: Foundation — Get basic AI recognition
- Stage 2: Clarity — Ensure consistent AI understanding
- Stage 3: Authority — Build AI trust signals
- Stage 4: Rich Presence — Structured data + multi-source consistency
- Stage 5: AI-native — Optimized for AI ecosystem

Be specific and actionable — not generic advice."""


# ── AI Engine ─────────────────────────────────────────────

import json
from typing import Optional


async def _call_llm(prompt: str, system: str = "") -> str:
    """Call Claude API."""
    if not CLAUDE_API_KEY:
        return _mock_response(prompt)

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=CLAUDE_API_KEY)
    messages = [{"role": "user", "content": prompt}]
    kwargs = {
        "model": CLAUDE_MODEL,
        "max_tokens": 4096,
        "temperature": 0.3,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    resp = await client.messages.create(**kwargs)
    return resp.content[0].text


def _mock_response(prompt: str) -> str:
    """Return mock JSON when no API key is set (for dev/testing)."""
    if "AI brand perception analyst" in prompt:
        return json.dumps({
            "summary": "Mock analysis — set CLAUDE_API_KEY for real results.",
            "key_attributes": ["innovative", "technology-driven", "user-focused"],
            "known_for": ["digital solutions", "technology products"],
            "confusion_areas": ["unclear positioning", "broad market focus"],
            "competitor_context": "Operates in a competitive landscape with several established players."
        })
    if "AI visibility auditor" in prompt:
        return json.dumps([
            {"category": "structure", "severity": "critical", "description": "Missing schema.org Organization markup", "evidence": "No JSON-LD found on homepage"},
            {"category": "content", "severity": "moderate", "description": "Value proposition not immediately clear", "evidence": "Meta description lacks unique selling points"},
            {"category": "authority", "severity": "minor", "description": "Limited external references found", "evidence": "No press mentions or certifications mentioned"},
        ])
    if "AI visibility strategist" in prompt:
        return json.dumps({
            "immediate_actions": [
                {"title": "Add Organization Schema", "description": "Add schema.org/Organization JSON-LD markup", "effort": "low", "impact": "high"},
                {"title": "Clarify Meta Description", "description": "Rewrite meta description with clear value prop", "effort": "low", "impact": "medium"},
            ],
            "medium_term_actions": [
                {"title": "Build Knowledge Base", "description": "Create comprehensive about page with team/product/vision", "effort": "medium", "impact": "high"},
            ],
            "roadmap": [
                {"stage": 1, "title": "Foundation", "description": "Basic AI recognition", "actions": ["Add schema markup", "Optimize meta tags"]},
                {"stage": 2, "title": "Clarity", "description": "Consistent AI understanding", "actions": ["Clear value prop", "About page content"]},
                {"stage": 3, "title": "Authority", "description": "AI trust signals", "actions": ["Get press mentions", "Build backlinks"]},
                {"stage": 4, "title": "Rich Presence", "description": "Multi-source consistency", "actions": ["Knowledge graph", "Social proof"]},
                {"stage": 5, "title": "AI-native", "description": "AI ecosystem optimized", "actions": ["AI-friendly content structure", "API-first presence"]},
            ]
        })
    return "{}"


async def analyze_perception(
    brand: str, url: str, website_content: str, about_content: str, structured_data: str
) -> AIPerceptionProfile:
    """Prompt 1: Simulate AI brand perception."""
    prompt = PERCEPTION_PROMPT.format(
        brand=brand,
        url=url,
        website_content=website_content[:8000],
        about_content=about_content[:4000],
        structured_data=str(structured_data)[:2000],
    )
    raw = await _call_llm(prompt)
    data = _parse_json(raw)
    return AIPerceptionProfile(
        summary=data.get("summary", "Analysis pending"),
        key_attributes=data.get("key_attributes", []),
        known_for=data.get("known_for", []),
        confusion_areas=data.get("confusion_areas", []),
        competitor_context=data.get("competitor_context", ""),
    )


async def detect_gaps(
    brand: str, url: str, perception: AIPerceptionProfile, website_content: str
) -> list[GapItem]:
    """Prompt 2: Identify information gaps."""
    prompt = GAP_PROMPT.format(
        brand=brand,
        url=url,
        perception_analysis=perception.model_dump_json(indent=2),
        website_content=website_content[:8000],
    )
    raw = await _call_llm(prompt)
    data = _parse_json(raw)
    if isinstance(data, list):
        return [
            GapItem(category=g.get("category", "content"), severity=g.get("severity", "moderate"),
                    description=g.get("description", ""), evidence=g.get("evidence", ""))
            for g in data
        ]
    return []


async def generate_optimizations(
    brand: str, perception: AIPerceptionProfile, gaps: list[GapItem]
) -> tuple[list[ActionItem], list[RoadmapStage]]:
    """Prompt 3: Generate optimization suggestions and roadmap."""
    prompt = OPTIMIZATION_PROMPT.format(
        brand=brand,
        perception_analysis=perception.model_dump_json(indent=2),
        gap_analysis=json.dumps([g.model_dump() for g in gaps], indent=2),
    )
    raw = await _call_llm(prompt)
    data = _parse_json(raw)

    immediate = data.get("immediate_actions", [])
    medium = data.get("medium_term_actions", [])

    suggestions = []
    for a in immediate:
        suggestions.append(ActionItem(priority="immediate", **a))
    for a in medium:
        suggestions.append(ActionItem(priority="medium_term", **a))

    roadmap = [RoadmapStage(**s) for s in data.get("roadmap", [])]

    return suggestions, roadmap


def _parse_json(raw: str) -> dict | list:
    """Extract JSON from LLM response (handles markdown fences)."""
    # Remove markdown code block fences
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    # Determine if response is an array or object
    first_char = text[0] if text else ""

    if first_char == "[":
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end >= 0:
            text = text[start : end + 1]
    elif first_char == "{":
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= 0:
            text = text[start : end + 1]
    else:
        # Try to find either structure
        start = text.find("[")
        if start >= 0:
            end = text.rfind("]")
            if end >= 0:
                text = text[start : end + 1]
            first_char = "["
        else:
            start = text.find("{")
            if start >= 0:
                end = text.rfind("}")
                if end >= 0:
                    text = text[start : end + 1]
                first_char = "{"

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return [] if first_char == "[" else {}
