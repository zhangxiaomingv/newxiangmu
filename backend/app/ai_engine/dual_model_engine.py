"""Dual-model analysis engine — Doubao + DeepSeek + Claude evaluator.

This is the main engine for ZKONER v2, replacing the heuristic adapter.
Pipeline:
  1. Extract ground truth from crawled website
  2. Query Doubao & DeepSeek with 5 standard questions
  3. Use Claude to evaluate each model's responses against ground truth
  4. Cross-model comparison → final score + report

Fallback behavior:
  - If Claude API key missing → heuristic evaluation instead of Claude
  - If Doubao API key missing → skip Doubao, only use DeepSeek (+ vice versa)
  - If both model APIs missing → fall back to heuristic engine

Environment variables:
  DOUBAO_API_KEY   — 火山引擎 API key (required for Doubao)
  DOUBAO_BASE_URL  — default: https://ark.cn-beijing.volces.com/api/v3
  DOUBAO_MODEL     — default: doubao-pro-32k
  DEEPSEEK_API_KEY — DeepSeek API key
  DEEPSEEK_BASE_URL— default: https://api.deepseek.com
  DEEPSEEK_MODEL   — default: deepseek-chat
"""

from __future__ import annotations

import json
import os
import re
from typing import Optional

from openai import AsyncOpenAI

from app.ai_engine.base import BaseEngineAdapter, EngineInput, EngineOutput
from app.ai_engine.prompts import (
    get_brand_queries,
    get_ground_truth_prompt,
    get_analysis_prompt,
    get_comparison_prompt,
    DOUBAO_SYSTEM_PROMPT,
    DEEPSEEK_SYSTEM_PROMPT,
)
from app.models.schemas import AIPerceptionProfile, GapItem, ActionItem, RoadmapStage


class _ModelClient:
    """Thin wrapper around OpenAI-compatible APIs."""

    def __init__(self, name: str, base_url: str, api_key: str, model: str, system_prompt: str):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def ask(self, question: str, max_tokens: int = 1024) -> str:
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return resp.choices[0].message.content or ""


class DualModelEngine(BaseEngineAdapter):
    """Query Doubao + DeepSeek, evaluate with Claude, produce brand report."""

    def __init__(self):
        self._doubao_client: Optional[_ModelClient] = None
        self._deepseek_client: Optional[_ModelClient] = None
        self._claude_client: Optional[AsyncOpenAI] = None   # also OpenAI-compatible
        self._init_clients()

    def _init_clients(self):
        # Doubao
        doubao_key = os.getenv("DOUBAO_API_KEY", "")
        if doubao_key:
            self._doubao_client = _ModelClient(
                name="doubao",
                base_url=os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
                api_key=doubao_key,
                model=os.getenv("DOUBAO_MODEL", "doubao-pro-32k"),
                system_prompt=DOUBAO_SYSTEM_PROMPT,
            )

        # DeepSeek
        deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        if deepseek_key:
            self._deepseek_client = _ModelClient(
                name="deepseek",
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                api_key=deepseek_key,
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                system_prompt=DEEPSEEK_SYSTEM_PROMPT,
            )

        # Claude (via OpenAI-compatible endpoint, or direct Anthropic SDK)
        # We use OPENAI-compatible path so we can also use any LLM as evaluator
        evaluator_key = os.getenv("CLAUDE_API_KEY", "")
        evaluator_base = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1")
        if evaluator_key:
            self._claude_client = AsyncOpenAI(base_url=evaluator_base, api_key=evaluator_key)

    # ── Adapter interface ──────────────────────────────────

    @property
    def name(self) -> str:
        return "dual"

    @property
    def display_name(self) -> str:
        parts = []
        if self._doubao_client:
            parts.append("豆包")
        if self._deepseek_client:
            parts.append("DeepSeek")
        return " + ".join(parts) + " 双模型检测" if parts else "双模型检测 (未配置)"

    def is_available(self) -> bool:
        return bool(self._doubao_client or self._deepseek_client)

    # ── Main pipeline ──────────────────────────────────────

    async def analyze(self, inp: EngineInput) -> EngineOutput:
        queries = get_brand_queries(inp.brand)

        # 1. Extract ground truth from crawl data
        ground_truth = await self._extract_ground_truth(inp)

        # 2. Query each available model
        doubao_responses = {}
        deepseek_responses = {}
        if self._doubao_client:
            doubao_responses = await self._query_model(self._doubao_client, queries)
        if self._deepseek_client:
            deepseek_responses = await self._query_model(self._deepseek_client, queries)

        # 3. Evaluate responses (pass inp for heuristic fallback gap generation)
        doubao_eval = None
        deepseek_eval = None
        if doubao_responses:
            doubao_eval = await self._evaluate_responses(inp.brand, ground_truth, doubao_responses, inp)
        if deepseek_responses:
            deepseek_eval = await self._evaluate_responses(inp.brand, ground_truth, deepseek_responses, inp)

        # 4. Cross-model comparison (if both available)
        combined = None
        if doubao_eval and deepseek_eval:
            combined = await self._compare_models(
                inp.brand, ground_truth,
                json.dumps(doubao_eval, ensure_ascii=False),
                json.dumps(deepseek_eval, ensure_ascii=False),
            )
        elif doubao_eval:
            combined = self._single_model_result(doubao_eval)
        elif deepseek_eval:
            combined = self._single_model_result(deepseek_eval)
        else:
            raise RuntimeError("No model responses available — cannot produce analysis")

        # 5. Build output
        return self._build_output(inp, combined, doubao_eval, deepseek_eval, doubao_responses, deepseek_responses)

    # ── Step 1: Ground truth ───────────────────────────────

    async def _extract_ground_truth(self, inp: EngineInput) -> str:
        """Try Claude for ground truth; fall back to heuristic extraction."""
        if self._claude_client:
            try:
                prompt = get_ground_truth_prompt(inp.brand, {
                    "raw_text": inp.website_content,
                    "about_text": inp.about_content,
                    "structured_data": inp.structured_data,
                    "title": inp.page_title,
                    "meta_description": inp.meta_description,
                })
                resp = await self._claude_client.chat.completions.create(
                    model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024,
                    temperature=0.3,
                )
                return resp.choices[0].message.content or self._heuristic_ground_truth(inp)
            except Exception:
                pass
        return self._heuristic_ground_truth(inp)

    @staticmethod
    def _heuristic_ground_truth(inp: EngineInput) -> str:
        """Build a simple ground truth from crawl data without any LLM."""
        sd = inp.structured_data or {}
        parts = [f"品牌名称: {inp.brand}"]
        if sd.get("description"):
            parts.append(f"描述: {sd['description'][:200]}")
        if inp.meta_description:
            parts.append(f"Meta描述: {inp.meta_description[:200]}")
        if inp.page_title:
            parts.append(f"页面标题: {inp.page_title}")
        if inp.about_content:
            parts.append(f"About: {inp.about_content[:300]}")
        parts.append(f"网站内容({len(inp.website_content)}字): {inp.website_content[:500]}")
        if inp.headings:
            parts.append("页面结构: " + "; ".join(
                h.get("text", "")[:60] for h in inp.headings[:5] if h.get("text")
            ))
        return "\n\n".join(parts)

    # ── Step 2: Query a model ──────────────────────────────

    async def _query_model(self, client: _ModelClient, queries: list[dict]) -> dict[str, str]:
        """Send 5 questions to a model, return {id: response_text}."""
        results = {}
        for q in queries:
            try:
                results[q["id"]] = await client.ask(q["question"])
            except Exception as e:
                results[q["id"]] = f"[查询失败: {e}]"
        return results

    # ── Step 3: Evaluate with Claude ────────────────────────

    async def _evaluate_responses(self, brand: str, ground_truth: str, responses: dict,
                                    inp: Optional[EngineInput] = None) -> dict:
        """Use Claude (or heuristic) to score model responses against ground truth."""
        if self._claude_client:
            try:
                prompt = get_analysis_prompt(brand, ground_truth, responses)
                resp = await self._claude_client.chat.completions.create(
                    model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2048,
                    temperature=0.2,
                )
                text = resp.choices[0].message.content or ""
                return self._parse_json(text)
            except Exception:
                pass
        return self._heuristic_evaluate(brand, responses, ground_truth, inp)

    def _heuristic_evaluate(self, brand: str, responses: dict, ground_truth: str = "",
                             inp: Optional[EngineInput] = None) -> dict:
        """Heuristic scoring + gap detection when Claude is unavailable."""
        dims = {}
        all_text = " ".join(responses.values())

        for qid, response in responses.items():
            length = len(response)
            if length > 500:
                score = 70 + min(20, length // 100)
            elif length > 200:
                score = 45 + min(25, length // 20)
            elif length > 50:
                score = 20 + min(25, length // 10)
            else:
                score = max(5, length)

            dims[qid] = {
                "score": min(score, 95),
                "analysis": f"基于回答长度({length}字)的启发式评估。配置 Claude API Key 可获得 AI 语义评估。",
                "errors": [],
                "hallucinations": [],
                "competitors_mentioned": [],
                "missed_competitors": [],
                "shallow_areas": [],
                "confessed_unknowns": [],
                "misunderstandings": [],
            }

        # Extract entities from responses
        mentioned_competitors = self._extract_competitors(all_text)
        mentioned_products = self._extract_products(all_text)
        has_numbers = bool(re.search(r'\d+[万亿]?[\d.]*|[%％]', all_text))
        has_vague = any(w in all_text for w in ["可能", "maybe", "perhaps", "generally", "通常", "一些"])

        overall = sum(d["score"] * [20, 30, 15, 20, 15][i] / 100 for i, (_, d) in enumerate(dims.items()))

        # Generate gaps by comparing responses against ground truth
        gaps = []
        if not mentioned_competitors:
            gaps.append({
                "category": "competition",
                "severity": "moderate",
                "description": f"AI 对 {brand} 的竞争对手信息不足，无法提供竞争格局分析。",
                "evidence": "AI 回答中未提及任何竞争者名称。",
            })
        if not has_numbers:
            gaps.append({
                "category": "depth",
                "severity": "moderate",
                "description": f"AI 对 {brand} 的描述缺乏具体数据（数字、时间、百分比），理解停留在表层。",
                "evidence": "AI 回答中未包含具体数字或统计数据。",
            })
        if has_vague:
            gaps.append({
                "category": "clarity",
                "severity": "minor",
                "description": f"AI 对 {brand} 的描述使用了模糊/不确定用语，品牌定位不够清晰。",
                "evidence": "回答包含'可能''也许''一般来说'等不确定用语。",
            })
        # Check if responses are too short (thin content)
        for qid, resp in responses.items():
            if len(resp) < 100:
                gaps.append({
                    "category": "content",
                    "severity": "moderate",
                    "description": f"AI 对 '{qid}' 维度回答过短（{len(resp)}字），品牌在此维度的 AI 认知薄弱。",
                    "evidence": f"回答长度不足100字，需要更丰富的品牌信息。",
                })
                break

        # Generate actions from gaps
        actions = []
        for g in gaps:
            if g["category"] == "competition":
                actions.append({
                    "priority": "medium_term",
                    "title": f"强化 {brand} 的竞争定位描述",
                    "description": "在官网和品牌资料中清晰标注主要竞争对手和差异化优势，帮助 AI 准确理解市场定位。",
                    "effort": "medium", "impact": "high",
                })
            elif g["category"] == "depth":
                actions.append({
                    "priority": "immediate",
                    "title": f"在官网增加具体数据和事实",
                    "description": "使用具体数字、年份、市场份额等数据描述品牌成就，提升 AI 认知的准确性。",
                    "effort": "low", "impact": "high",
                })
            elif g["category"] == "clarity":
                actions.append({
                    "priority": "immediate",
                    "title": f"为 {brand} 撰写清晰的品牌定位声明",
                    "description": "在官网首页用一句话明确描述「品牌是什么、为谁服务、独特之处」。",
                    "effort": "low", "impact": "high",
                })
            elif g["category"] == "content":
                actions.append({
                    "priority": "medium_term",
                    "title": f"丰富 {brand} 在各维度的品牌信息",
                    "description": "确保官网和公开资料全面覆盖品牌的核心业务、产品、技术能力和市场地位。",
                    "effort": "medium", "impact": "high",
                })

        perception_summary = f"基于 {brand} 的启发式分析。"
        if mentioned_competitors:
            perception_summary += f" AI 提到了竞品: {', '.join(mentioned_competitors[:3])}。"
        if mentioned_products:
            perception_summary += f" 识别到产品: {', '.join(mentioned_products[:3])}。"

        return {
            "overall_score": round(overall, 1),
            "dimensions": dims,
            "perception_summary": perception_summary,
            "key_attributes_from_ai": mentioned_products[:3] or [brand],
            "confusion_areas": ["配置 Claude API Key 可获取语义级混淆检测"],
            "gaps": gaps,
            "actions": actions,
        }

    @staticmethod
    def _extract_competitors(text: str) -> list[str]:
        """Extract likely competitor names from model response."""
        # Known brand names that commonly appear as competitors
        known_brands = [
            "Tesla", "BYD", "比亚迪", "NIO", "蔚来", "XPeng", "小鹏", "Li Auto", "理想",
            "Google", "Microsoft", "微软", "Apple", "苹果", "Amazon", "Meta", "OpenAI",
            "Anthropic", "DeepSeek", "字节跳动", "ByteDance", "阿里巴巴", "Alibaba",
            "腾讯", "Tencent", "百度", "Baidu", "华为", "Huawei", "Xiaomi", "小米",
        ]
        found = []
        for b in known_brands:
            if b.lower() in text.lower():
                found.append(b)
        # Also look for capitalized words followed by "competitor" or "rival"
        competitors = re.findall(r'(?:competitor|rival|competition|vs\.?|versus)\s+([A-Z][a-zA-Z]+)', text)
        found.extend(competitors)
        return list(set(found))[:5]

    @staticmethod
    def _extract_products(text: str) -> list[str]:
        """Extract likely product/service names from model response."""
        products = re.findall(r'([A-Z][a-zA-Z0-9]{2,}(?:\s[A-Z][a-zA-Z0-9]+){0,3})', text)
        # Filter out common words and short strings
        skip = {"The", "This", "That", "These", "What", "When", "Where", "How", "Why",
                "They", "There", "Their", "Your", "Our", "Its", "Are", "Has", "Had",
                "Will", "Can", "May", "Must", "Should", "Would", "Could", "Being",
                "Having", "Doing", "Also", "Very", "Just", "Only", "More", "Most"}
        return [p for p in products if p not in skip and len(p) > 3][:5]

    # ── Step 4: Cross-model comparison ──────────────────────

    async def _compare_models(self, brand: str, ground_truth: str,
                              doubao_eval_str: str, deepseek_eval_str: str) -> dict:
        if self._claude_client:
            try:
                prompt = get_comparison_prompt(brand, ground_truth, doubao_eval_str, deepseek_eval_str)
                resp = await self._claude_client.chat.completions.create(
                    model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2048,
                    temperature=0.2,
                )
                text = resp.choices[0].message.content or ""
                return self._parse_json(text)
            except Exception:
                pass

        # Heuristic combination
        doubao = self._parse_json(doubao_eval_str) if isinstance(doubao_eval_str, str) else doubao_eval_str
        deepseek = self._parse_json(deepseek_eval_str) if isinstance(deepseek_eval_str, str) else deepseek_eval_str

        d_score = doubao.get("overall_score", 50)
        s_score = deepseek.get("overall_score", 50)
        winner = "tie" if abs(d_score - s_score) < 5 else ("doubao" if d_score > s_score else "deepseek")

        # Collect gaps and attributes from individual evals
        all_gaps = []
        seen_gap = set()
        for src in [doubao, deepseek]:
            for g in (src.get("gaps") or []):
                key = g.get("description", "")[:40]
                if key not in seen_gap:
                    seen_gap.add(key)
                    all_gaps.append(g)
        all_attrs = (doubao.get("key_attributes_from_ai", []) or
                     deepseek.get("key_attributes_from_ai", []))

        return {
            "overall_score": round(max(d_score, s_score), 1),
            "consistency": round(100 - abs(d_score - s_score), 1),
            "model_winner": winner,
            "consensus_strengths": [],
            "consensus_gaps": all_gaps,
            "divergence_areas": [],
            "summary": f"豆包评分 {d_score}，DeepSeek 评分 {s_score}。配置 Claude API Key 可获取详细语义对比。",
            "key_attributes_from_ai": all_attrs,
            "known_for": [],
            "confusion_areas": [],
            "competitor_context": "",
            "gaps": all_gaps,
        }

    @staticmethod
    def _single_model_result(eval_data: dict) -> dict:
        return {
            "overall_score": eval_data.get("overall_score", 50),
            "consistency": 100,
            "model_winner": "single",
            "consensus_strengths": [],
            "consensus_gaps": [],
            "divergence_areas": [],
            "summary": eval_data.get("perception_summary", ""),
            "key_attributes_from_ai": eval_data.get("key_attributes_from_ai", []),
            "known_for": eval_data.get("known_for", []),
            "confusion_areas": eval_data.get("confusion_areas", []),
            "competitor_context": eval_data.get("competitor_context", ""),
        }

    # ── Step 5: Build output ───────────────────────────────

    def _build_output(self, inp: EngineInput, combined: dict,
                      doubao_eval: dict | None, deepseek_eval: dict | None,
                      doubao_raw: dict, deepseek_raw: dict) -> EngineOutput:

        perception = AIPerceptionProfile(
            summary=self._build_final_summary(combined, doubao_eval, deepseek_eval),
            key_attributes=combined.get("key_attributes_from_ai", [inp.brand]),
            known_for=combined.get("known_for", combined.get("consensus_strengths", [])),
            confusion_areas=combined.get("confusion_areas", []),
            competitor_context=combined.get("competitor_context", ""),
        )

        gaps = self._collect_gaps(doubao_eval, deepseek_eval, combined)
        suggestions = self._collect_suggestions(doubao_eval, deepseek_eval, combined)
        roadmap = self._build_roadmap(gaps)

        return EngineOutput(
            perception=perception,
            gaps=gaps,
            suggestions=suggestions,
            roadmap=roadmap,
            engine_name=self.name,
            source_raw=json.dumps({
                "engine": "dual_model",
                "brand": inp.brand,
                "models_queried": [
                    m for m in ["doubao", "deepseek"]
                    if (m == "doubao" and doubao_raw) or (m == "deepseek" and deepseek_raw)
                ],
                "doubao_raw_queries": list(doubao_raw.keys()) if doubao_raw else [],
                "deepseek_raw_queries": list(deepseek_raw.keys()) if deepseek_raw else [],
                "doubao_overall": doubao_eval.get("overall_score") if doubao_eval else None,
                "deepseek_overall": deepseek_eval.get("overall_score") if deepseek_eval else None,
                "combined_summary": combined.get("summary", ""),
            }, ensure_ascii=False, indent=2),
        )

    def _build_final_summary(self, combined: dict, doubao: dict | None, deepseek: dict | None) -> str:
        parts = []
        if doubao:
            parts.append(f"【豆包】{doubao.get('perception_summary', '')}")
        if deepseek:
            parts.append(f"【DeepSeek】{deepseek.get('perception_summary', '')}")
        parts.append(f"\n综合评估: {combined.get('summary', '')}")
        return "\n\n".join(parts)

    @staticmethod
    def _collect_gaps(doubao: dict | None, deepseek: dict | None, combined: dict) -> list[GapItem]:
        gaps = []
        for source in [doubao, deepseek]:
            if source:
                for g in (source.get("gaps") or []):
                    gaps.append(GapItem(
                        category=g.get("category", "general"),
                        severity=g.get("severity", "moderate"),
                        description=g.get("description", ""),
                        evidence=g.get("evidence", ""),
                    ))
        return gaps

    @staticmethod
    def _collect_suggestions(doubao: dict | None, deepseek: dict | None, combined: dict) -> list[ActionItem]:
        suggestions = []
        seen = set()
        for source in [doubao, deepseek]:
            if source:
                for a in (source.get("actions") or []):
                    key = a.get("title", "")
                    if key not in seen:
                        seen.add(key)
                        suggestions.append(ActionItem(
                            priority=a.get("priority", "medium_term"),
                            title=a.get("title", ""),
                            description=a.get("description", ""),
                            effort=a.get("effort", "medium"),
                            impact=a.get("impact", "medium"),
                        ))
        return suggestions

    @staticmethod
    def _build_roadmap(gaps: list[GapItem]) -> list[RoadmapStage]:
        return [
            RoadmapStage(stage=1, title="Foundation 结构化基础", description="让 AI 能识别品牌实体", actions=[
                "实现 Schema.org 结构化数据",
                "确保品牌名称、描述、URL 在 AI 中一致",
                "创建详细的 About 页面",
            ]),
            RoadmapStage(stage=2, title="Clarity 认知清晰", description="消除 AI 对品牌的混淆", actions=[
                "在官网首页用一句话说明「我们为谁做什么」",
                "减少模糊/泛化用词，使用行业特定描述",
                "确保豆包和 DeepSeek 都能正确描述核心业务",
            ]),
            RoadmapStage(stage=3, title="Authority 权威建设", description="增强 AI 对品牌的信任", actions=[
                "在官网展示媒体报道、奖项、客户案例",
                "获取行业权威网站的外部链接",
                "发布原创研究报告或行业洞察",
            ]),
            RoadmapStage(stage=4, title="Rich Presence 丰富存在", description="多维度强化 AI 认知", actions=[
                "同步品牌信息到 Wikipedia、天眼查、企查查等平台",
                "在知乎、小红书等平台建立品牌内容矩阵",
                "创建产品/服务的详细子页面",
            ]),
            RoadmapStage(stage=5, title="AI-native 原生化", description="持续优化 AI 生态中的品牌认知", actions=[
                "每日监控豆包和 DeepSeek 对品牌描述的变化",
                "定期更新品牌内容以反映最新信息",
                "建立 AI 可读的 FAQ/知识库",
            ]),
        ]

    # ── Helpers ────────────────────────────────────────────

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Extract JSON from LLM response (may be wrapped in markdown fences)."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:] if lines[0].startswith("```") else lines
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON block inside
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return {}
