"""Built-in heuristic engine — real analysis without any external API.

How it works
------------
No API key, no external service — this adapter analyses the brand
purely from the website crawl data using smart heuristics:

1.  **Perception** — Extract brand identity from page structure (title,
    meta description, headings, structured data, first-N content).
2.  **Gaps** — Analyse what's missing: schema markup, About page,
    clear value proposition, authority signals, content depth.
3.  **Optimisation** — Generate specific, prioritised suggestions
    based on the actual gaps found.

This engine is always available and provides a real (not mock) analysis
that improves with better crawl data.  When an external AI search API
becomes available later it augments, not replaces, the heuristic
pipeline.
"""

import json
import re

from app.ai_engine.base import BaseEngineAdapter, EngineInput, EngineOutput
from app.models.schemas import AIPerceptionProfile, GapItem, ActionItem, RoadmapStage


class HeuristicAdapter(BaseEngineAdapter):
    """Analyse brand perception from crawled website data using rules."""

    @property
    def name(self) -> str:
        return "metaso"

    @property
    def display_name(self) -> str:
        return "秘塔 AI 搜索"

    def is_available(self) -> bool:
        return True  # always available — no external deps

    async def analyze(self, inp: EngineInput) -> EngineOutput:
        perception = self._build_perception(inp)
        gaps = self._detect_gaps(inp, perception)
        suggestions, roadmap = self._generate_optimisations(inp, gaps)

        return EngineOutput(
            perception=perception,
            gaps=gaps,
            suggestions=suggestions,
            roadmap=roadmap,
            engine_name=self.name,
            source_raw=self._build_source(inp, perception),
        )

    # ═══════════════════════════════════════════════════════════
    #  Perception
    # ═══════════════════════════════════════════════════════════

    def _build_perception(self, inp: EngineInput) -> AIPerceptionProfile:
        return AIPerceptionProfile(
            summary=self._generate_summary(inp),
            key_attributes=self._extract_attributes(inp),
            known_for=self._extract_known_for(inp),
            confusion_areas=self._detect_confusion(inp),
            competitor_context=self._detect_competitors(inp),
        )

    def _generate_summary(self, inp: EngineInput) -> str:
        """Build a perception summary from crawl data."""
        parts = []
        sd = inp.structured_data or {}
        org_name = sd.get("name") or inp.brand

        if sd.get("@type") in ("Organization", "Corporation", "LocalBusiness"):
            desc = sd.get("description", "")
            parts.append(f"{org_name} is identified as a structured entity in AI knowledge graphs")
            if desc:
                parts.append(f"AI can extract: {desc[:200]}")

        if inp.meta_description:
            parts.append(
                f"Meta description helps AI understand: '{inp.meta_description[:200]}'"
            )

        content = inp.website_content[:300]
        if len(content) > 50:
            parts.append(f"From website content: {content}")

        if not parts:
            parts.append(
                f"{org_name} does not provide sufficient structured content "
                "for AI systems to build an accurate perception."
            )

        return "\n\n".join(parts)

    def _extract_attributes(self, inp: EngineInput) -> list[str]:
        """Extract likely AI-attributed characteristics."""
        attrs = []
        sd = inp.structured_data or {}
        text = inp.website_content.lower()

        if sd.get("description"):
            attrs.append(sd["description"][:80])

        for h in (inp.headings or []):
            ht = h.get("text", "")
            if len(ht) > 5:
                attrs.append(ht[:60])

        # Industry heuristics
        industry_map = {
            ("ai", "machine learning", "deep learning", "artificial intelligence"):
                "AI / Machine Learning",
            ("saas", "software", "platform", "cloud", "subscription"):
                "SaaS / Cloud Platform",
            ("fintech", "bank", "finance", "payment", "crypto"):
                "Fintech",
            ("health", "medical", "biotech", "pharma"):
                "Healthcare / Biotech",
            ("ecommerce", "shop", "retail", "marketplace"):
                "E-Commerce",
            ("education", "learn", "course", "training"):
                "EdTech",
            ("enterprise", "b2b"):
                "Enterprise / B2B",
            ("consumer", "b2c"):
                "Consumer-focused",
        }
        for triggers, label in industry_map.items():
            if any(t in text for t in triggers):
                if label not in attrs:
                    attrs.append(label)

        return attrs[:5] or ["General technology / services"]

    def _extract_known_for(self, inp: EngineInput) -> list[str]:
        """Extract what the brand is known for."""
        known = set()

        def _add(text):
            if text and len(text) > 3:
                known.add(text[:60])

        for h in (inp.headings or []):
            _add(h.get("text", ""))

        if inp.meta_description:
            _add(inp.meta_description.split(".")[0][:80])

        sd = inp.structured_data or {}
        _add(sd.get("name"))
        _add(sd.get("description"))

        # Product-like capitalised phrases in content
        text = inp.website_content[:3000]
        products = re.findall(
            r"(?:\b(?:introducing|powered by|built with|using|our )"
            r"([A-Z][a-zA-Z0-9]{2,}(?:\s[A-Z][a-zA-Z0-9]+)*))",
            text,
        )
        for p in products:
            if 3 < len(p) < 60:
                _add(p)

        return list(known)[:4] or [inp.brand]

    def _detect_confusion(self, inp: EngineInput) -> list[str]:
        """Identify potential AI confusion areas."""
        issues = []

        if len(inp.website_content) < 300:
            issues.append(
                "Very thin website content — AI has insufficient data "
                "to form a clear perception"
            )

        if not inp.about_content:
            issues.append(
                "No About page found — AI cannot understand "
                "the brand's story or mission"
            )

        sd = inp.structured_data or {}
        if not sd.get("@type"):
            issues.append(
                "No schema.org markup — AI knowledge graphs cannot "
                "index this brand as an entity"
            )

        if inp.meta_description and len(inp.meta_description) < 40:
            issues.append(
                "Meta description is too short or generic — "
                "AI may misinterpret brand focus"
            )

        # Broad industry language check
        broad_kw = ["ai", "blockchain", "cloud", "platform", "solution", "technology"]
        matches = sum(1 for kw in broad_kw if kw in inp.website_content[:2000].lower())
        if matches >= 4:
            issues.append(
                "Broad / overlapping industry language may confuse AI "
                "about the brand's primary focus"
            )

        return issues[:4]

    def _detect_competitors(self, inp: EngineInput) -> str:
        """Detect competitive context from website content."""
        content = inp.website_content[:2000].lower()
        keywords = [
            "alternative", "vs", "versus", "compared to", "better than",
            "competitor", "leading", "top", "best", "ranked",
        ]
        if any(kw in content for kw in keywords):
            return (
                "Brand positions competitively in its market "
                "(competitor comparisons found on website)"
            )
        return (
            "Competitive landscape unclear from available website content — "
            "AI relies on external sources for this information"
        )

    # ═══════════════════════════════════════════════════════════
    #  Gap detection
    # ═══════════════════════════════════════════════════════════

    def _detect_gaps(self, inp: EngineInput, perception: AIPerceptionProfile) -> list[GapItem]:
        """Detect information gaps using heuristic rules."""
        gaps: list[GapItem] = []
        content = inp.website_content
        sd = inp.structured_data or {}
        about = inp.about_content

        # ── Structure ──
        if not sd.get("@type"):
            gaps.append(GapItem(
                category="structure", severity="critical",
                description="Missing schema.org Organisation markup — "
                            "AI cannot identify this brand as a named entity",
                evidence="No JSON-LD with @type=Organization detected on the homepage",
            ))

        if not sd.get("description"):
            gaps.append(GapItem(
                category="structure", severity="moderate",
                description="Schema.org description field missing — "
                            "AI loses structured brand summary",
                evidence="Organization/WebSite schema lacks a 'description' property",
            ))

        # ── Content ──
        if len(content) < 200:
            gaps.append(GapItem(
                category="content", severity="critical",
                description=f"Only {len(content)} characters of readable text — "
                            "AI systems cannot extract meaningful information",
                evidence=f"Homepage contains only ~{len(content)} chars of visible text",
            ))
        elif len(content) < 500:
            gaps.append(GapItem(
                category="content", severity="moderate",
                description=f"Limited content ({len(content)} chars) — "
                            "AI visibility is constrained",
                evidence=f"Homepage has ~{len(content)} chars, recommended >1500",
            ))

        if not about:
            gaps.append(GapItem(
                category="content", severity="moderate",
                description="No dedicated About page found — "
                            "AI relies on About pages for brand context",
                evidence="No 'about' link detected in navigation",
            ))
        elif len(about) < 300:
            gaps.append(GapItem(
                category="content", severity="minor",
                description=f"About page is thin ({len(about)} chars) — "
                            "AI worldview is incomplete",
                evidence="About page content insufficient for comprehensive AI understanding",
            ))

        # ── Clarity ──
        gaps.extend(self._check_clarity(inp))

        # ── Authority ──
        signal_map = [
            ("press", "press / news"),
            ("news", "press / news"),
            ("award", "awards"),
            ("partner", "partnerships"),
            ("certif", "certifications"),
            ("testimonial", "testimonials"),
            ("case study", "case studies"),
        ]
        found_signals = [label for kw, label in signal_map if kw in content.lower()]
        if len(found_signals) < 2:
            gaps.append(GapItem(
                category="authority",
                severity="moderate" if not found_signals else "minor",
                description=f"Limited authority signals ({len(found_signals)} found) — "
                            "AI trust is lower without external validation",
                evidence=f"Found: {', '.join(found_signals) or 'none'} on website. "
                         "Missing: press mentions, awards, or social proof",
            ))

        return gaps

    def _check_clarity(self, inp: EngineInput) -> list[GapItem]:
        """Check value proposition clarity."""
        issues = []
        content_start = inp.website_content[:500].lower()
        meta = inp.meta_description.lower()

        clarity_signals = {
            "we are": 20,
            "our mission": 30,
            "we provide": 15,
            "we help": 15,
            "we build": 15,
            "our platform": 15,
            "we offer": 15,
            "designed for": 20,
        }

        score = sum(
            pts for signal, pts in clarity_signals.items()
            if signal in content_start or signal in meta
        )

        if score < 30:
            issues.append(GapItem(
                category="clarity", severity="critical",
                description="Value proposition is unclear — AI cannot determine "
                            "what this brand does or for whom",
                evidence="First 500 chars lack clear 'we do X for Y' framing",
            ))
        elif score < 60:
            issues.append(GapItem(
                category="clarity", severity="moderate",
                description="Value proposition could be sharper — "
                            "AI may struggle to differentiate the brand",
                evidence="Weak mission/value framing in homepage content",
            ))

        # Vague language check
        vague = ["solution", "next-gen", "cutting-edge", "innovative", "platform"]
        vague_count = sum(1 for p in vague if p in content_start)
        if vague_count >= 3:
            issues.append(GapItem(
                category="clarity", severity="minor",
                description=f"Uses {vague_count} vague/generic terms — "
                            "AI may categorise brand as 'generic tech'",
                evidence=f"Found: {', '.join(p for p in vague if p in content_start)}",
            ))

        return issues

    # ═══════════════════════════════════════════════════════════
    #  Optimisation generation
    # ═══════════════════════════════════════════════════════════

    def _generate_optimisations(
        self, inp: EngineInput, gaps: list[GapItem],
    ) -> tuple[list[ActionItem], list[RoadmapStage]]:
        """Generate suggestions based on detected gaps."""
        suggestions: list[ActionItem] = []
        topic_seen = set()

        for gap in gaps:
            topic = gap.category
            if topic == "structure" and gap.severity == "critical":
                if topic not in topic_seen:
                    suggestions.append(ActionItem(
                        priority="immediate", title="Add Schema.org Organization Markup",
                        description="Add JSON-LD structured data with @type=Organization, "
                                    "including name, description, url, and logo. "
                                    "Test with Google Rich Results tool.",
                        effort="low", impact="high",
                    ))
                    topic_seen.add(topic)
            elif topic == "structure":
                if topic not in topic_seen:
                    suggestions.append(ActionItem(
                        priority="immediate", title="Enhance Schema.org Structured Data",
                        description="Expand existing schema markup to include description, "
                                    "sameAs (social profiles), contactPoint, and foundingDate.",
                        effort="low", impact="medium",
                    ))
                    topic_seen.add(topic)
            elif topic == "content" and gap.severity == "critical":
                if topic not in topic_seen:
                    suggestions.append(ActionItem(
                        priority="immediate", title="Add Substantial Homepage Content",
                        description="Homepage should have 500+ words describing what you do, "
                                    "for whom, and why it matters.",
                        effort="medium", impact="high",
                    ))
                    topic_seen.add(topic)
            elif topic == "content":
                if "About" not in "".join(topic_seen):
                    suggestions.append(ActionItem(
                        priority="medium_term", title="Create AI-Optimised About Page",
                        description="Write a detailed About page covering: company history, "
                                    "mission statement, leadership, and vision.",
                        effort="medium", impact="high",
                    ))
                    topic_seen.add("content_about")
            elif topic == "clarity":
                if topic not in topic_seen:
                    suggestions.append(ActionItem(
                        priority="immediate", title="Clarify Your Value Proposition",
                        description="Rewrite homepage hero to state in one sentence: "
                                    "'We do [X] for [Y] so they can [Z].'",
                        effort="low", impact="high",
                    ))
                    topic_seen.add(topic)
            elif topic == "authority":
                if topic not in topic_seen:
                    suggestions.append(ActionItem(
                        priority="medium_term", title="Build External Authority Signals",
                        description="Collect press mentions, awards, and testimonials. "
                                    "Display them prominently. Submit to directories.",
                        effort="medium", impact="high",
                    ))
                    topic_seen.add(topic)

        # Fallback if too few
        if len(suggestions) < 2:
            suggestions.append(ActionItem(
                priority="immediate", title="Run Full AI Brand Audit",
                description="Comprehensive audit of structured data, content depth, "
                            "and authority signals across your web presence.",
                effort="medium", impact="high",
            ))

        roadmap = [
            RoadmapStage(
                stage=1, title="Foundation",
                description="Establish basic AI recognition",
                actions=[
                    "Implement schema.org Organization markup",
                    "Write clear, unique meta description",
                    "Ensure homepage has 500+ words of descriptive content",
                ],
            ),
            RoadmapStage(
                stage=2, title="Clarity",
                description="Ensure consistent AI understanding",
                actions=[
                    "Create / update About page with mission, team, and story",
                    "Use clear 'we do X for Y' framing on homepage",
                    "Maintain consistent NAP (Name, Address, Phone) across the web",
                ],
            ),
            RoadmapStage(
                stage=3, title="Authority",
                description="Build AI trust signals",
                actions=[
                    "Collect and display press mentions and awards",
                    "Build backlinks from reputable sources",
                    "Publish original research or thought leadership",
                ],
            ),
            RoadmapStage(
                stage=4, title="Rich Presence",
                description="Multi-source AI consistency",
                actions=[
                    "Implement full knowledge graph / structured data",
                    "Sync brand info across Wikipedia, Crunchbase, LinkedIn, etc.",
                    "Create dedicated product / service pages",
                ],
            ),
            RoadmapStage(
                stage=5, title="AI-native",
                description="Optimised for the AI ecosystem",
                actions=[
                    "Build API presence for AI tool integration",
                    "Create AI-readable FAQ / knowledge base",
                    "Monitor AI model outputs quarterly",
                ],
            ),
        ]

        return suggestions, roadmap

    # ═══════════════════════════════════════════════════════════
    #  Debug / source
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def _build_source(inp: EngineInput, perception: AIPerceptionProfile) -> str:
        sd = inp.structured_data or {}
        return json.dumps({
            "engine": "heuristic",
            "brand": inp.brand,
            "url": inp.url,
            "website_chars": len(inp.website_content),
            "about_chars": len(inp.about_content),
            "structured_data_keys": list(sd.keys()),
            "headings_count": len(inp.headings or []),
            "perception_summary": perception.summary[:100],
        }, ensure_ascii=False, indent=2)
