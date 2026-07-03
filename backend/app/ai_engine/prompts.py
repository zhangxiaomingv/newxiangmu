"""Shared prompt templates for all adapters.

Every adapter feeds these prompts to its backend LLM / AI service.
Adapters that don't call an LLM directly (e.g. 秘塔 search) can
use the prompt outputs as parsing guides instead.
"""

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

Be honest and critical — don't sugarcoat. If the brand's positioning is unclear, say so.

IMPORTANT: Write your response in {output_language}."""

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

Be specific and actionable — not generic SEO advice.

IMPORTANT: Write your response in {output_language}."""

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

Be specific and actionable — not generic advice.

IMPORTANT: Write your response in {output_language}."""
