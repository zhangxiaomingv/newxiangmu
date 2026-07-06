"""Prompt templates — the core IP of ZKONER.

All prompts are Chinese-first because ZKONER targets Doubao + DeepSeek,
the two dominant AI models in China's market.
"""

# ═══════════════════════════════════════════════════════════════
#  5 standard questions to ask each model about a brand
# ═══════════════════════════════════════════════════════════════

BRAND_QUERIES = [
    {
        "id": "mention",
        "dimension": "提及度",
        "question": "你知道{brand}吗？请详细介绍它是什么。",
        "weight": 0.20,
    },
    {
        "id": "accuracy",
        "dimension": "准确性",
        "question": "{brand}主要做什么业务？它有什么特点和优势？请尽可能具体地描述。",
        "weight": 0.30,
    },
    {
        "id": "differentiation",
        "dimension": "差异化",
        "question": "{brand}的竞争对手有哪些？它与竞争对手的主要区别是什么？{brand}最独特的优势是什么？",
        "weight": 0.15,
    },
    {
        "id": "depth",
        "dimension": "深度",
        "question": "{brand}在行业中的地位如何？它的技术能力、市场份额、影响力怎么样？请给出尽可能详细的分析。",
        "weight": 0.20,
    },
    {
        "id": "blindspot",
        "dimension": "认知盲区",
        "question": "关于{brand}，有哪些普通人不知道但很重要的事实？以及关于{brand}有没有什么常见的误解？如果不了解{brand}，请诚实地说出你不了解的部分。",
        "weight": 0.15,
    },
]

# ═══════════════════════════════════════════════════════════════
#  Ground truth extraction (sent to Claude, or heuristic fallback)
# ═══════════════════════════════════════════════════════════════

GROUND_TRUTH_EXTRACTION = """你是一个品牌分析专家。请根据以下网站信息，提取 {brand} 的「Ground Truth」（真实信息）。

## 网站内容
{website_content}

## About 页面内容
{about_content}

## 结构化数据 (Schema.org)
{structured_data}

## 页面标题: {page_title}
## Meta 描述: {meta_description}

请提取并严格输出以下 JSON（只输出 JSON，不要其他内容）：

{{
  "one_liner": "一句话描述品牌（50字以内）",
  "core_business": "主营业务（2-3句话）",
  "key_features": ["特点1", "特点2", "特点3"],
  "products_services": ["产品/服务1", "产品/服务2"],
  "target_users": "目标用户群",
  "industry": "行业分类",
  "unique_advantages": ["独特优势1", "独特优势2"],
  "known_competitors": ["竞品1", "竞品2"],
  "confidence": "high / medium / low"
}}"""

# ═══════════════════════════════════════════════════════════════
#  Response evaluator (Claude judges Doubao + DeepSeek answers)
# ═══════════════════════════════════════════════════════════════

ANALYZE_MODEL_RESPONSE = """你是一个客观的 AI 品牌认知评估器。以下是某个 AI 模型对「{brand}」的 5 个问题的回答。请根据 Ground Truth 评估每个回答的质量。

## Ground Truth
{ground_truth}

## Q1: 提及度 — 你知道{mention_brand}吗？
{mention_response}

## Q2: 准确性 — 主要做什么？特点和优势？
{accuracy_response}

## Q3: 差异化 — 竞争对手和独特优势？
{differentiation_response}

## Q4: 深度 — 行业地位？
{depth_response}

## Q5: 认知盲区 — 不知道/误解？
{blindspot_response}

---

严格输出以下 JSON（只输出 JSON，不要其他内容）：

{{
  "overall_score": 0-100,
  "dimensions": {{
    "mention": {{ "score": 0-100, "analysis": "评估：AI 是否知道这个品牌？信息量够吗？" }},
    "accuracy": {{ "score": 0-100, "analysis": "评估：描述是否准确？有无事实错误？", "errors": ["错误1"], "hallucinations": ["幻觉1"] }},
    "differentiation": {{ "score": 0-100, "analysis": "评估：能否区分品牌与竞品？", "competitors_mentioned": [], "missed_competitors": [] }},
    "depth": {{ "score": 0-100, "analysis": "评估：理解深度如何？笼统还是具体？", "shallow_areas": [] }},
    "blindspot": {{ "score": 0-100, "analysis": "评估：AI 承认不知道什么？有误解吗？", "confessed_unknowns": [], "misunderstandings": [] }}
  }},
  "perception_summary": "整体认知画像（2-3句话）",
  "key_attributes_from_ai": ["属性1", "属性2", "属性3"],
  "confusion_areas": ["混淆处1"],
  "gaps": [
    {{ "category": "mention|accuracy|depth|differentiation|blindspot", "severity": "critical|moderate|minor", "description": "具体缺口描述" }}
  ],
  "actions": [
    {{ "priority": "immediate|medium_term", "title": "建议标题", "description": "具体行动", "effort": "low|medium|high", "impact": "low|medium|high" }}
  ]
}}"""

# ═══════════════════════════════════════════════════════════════
#  Cross-model comparison
# ═══════════════════════════════════════════════════════════════

CROSS_MODEL_COMPARISON = """你是 AI 品牌认知评估器。对比两个 AI 模型对「{brand}」的认知差异。

## Ground Truth
{ground_truth}

## 豆包 (Doubao) 评估
{doubao_eval}

## DeepSeek 评估
{deepseek_eval}

---

输出 JSON：

{{
  "overall_score": 0-100,
  "consistency": 0-100,
  "model_winner": "doubao|deepseek|tie",
  "consensus_strengths": ["两个模型都正确认知的优点"],
  "consensus_gaps": ["两个模型都缺失的信息"],
  "divergence_areas": ["认知分歧的地方"],
  "summary": "品牌在中文 AI 生态中的整体认知画像（3-4句话）",
  "key_attributes_from_ai": ["属性1", "属性2"],
  "known_for": ["AI熟知的方面1", "方面2"],
  "confusion_areas": ["混淆处1"],
  "competitor_context": "竞争格局分析"
}}"""

# ═══════════════════════════════════════════════════════════════
#  Helper: build filled-in prompts
# ═══════════════════════════════════════════════════════════════

DOUBAO_SYSTEM_PROMPT = "你是一个信息全面、客观准确的 AI 助手。请用中文回答。回答应具体、详实、有据可查。"

DEEPSEEK_SYSTEM_PROMPT = "你是一个专业的研究助手，擅长提供深度、结构化、有逻辑的回答。请用中文回答。"

# ═══════════════════════════════════════════════════════════════
#  Backward-compatible aliases for old adapters (claude, metaso)
# ═══════════════════════════════════════════════════════════════

PERCEPTION_PROMPT = GROUND_TRUTH_EXTRACTION.replace("Ground Truth", "perception")
PERCEPTION_PROMPT = """You are an AI brand perception analyst. Analyze how AI systems would perceive {brand} based on its public web presence.

Brand: {brand}
Website URL: {url}

Website Content:
{website_content}

About Page Content:
{about_content}

Structured Data Found:
{structured_data}

Return your analysis as a JSON object with these fields:
- summary (str): One-paragraph summary of AI's perception
- key_attributes (list[str]): 3-5 key attributes
- known_for (list[str]): 2-4 things the brand is known for
- confusion_areas (list[str]): 2-4 areas of ambiguity
- competitor_context (str): competitive landscape position

IMPORTANT: Write your response in {output_language}."""

GAP_PROMPT = """You are an AI visibility auditor. Based on the brand analysis below, identify what information is missing for AI systems.

Brand: {brand}
Website URL: {url}

AI Perception Analysis:
{perception_analysis}

Website Content:
{website_content}

Identify gaps in: structure, content, authority, clarity.

Return JSON array of gap items: category, severity (critical|moderate|minor), description, evidence.

IMPORTANT: Write your response in {output_language}."""

OPTIMIZATION_PROMPT = """You are an AI visibility strategist. Generate concrete steps to improve AI visibility.

Brand: {brand}

Current AI Perception:
{perception_analysis}

Identified Gaps:
{gap_analysis}

Return JSON:
{{
  "immediate_actions": [{{"title": "...", "description": "...", "effort": "low|medium|high", "impact": "low|medium|high"}}],
  "medium_term_actions": [{{"title": "...", "description": "...", "effort": "low|medium|high", "impact": "low|medium|high"}}],
  "roadmap": [{{"stage": 1, "title": "...", "description": "...", "actions": ["..."]}}]
}}

Stage progression: Foundation → Clarity → Authority → Rich Presence → AI-native

IMPORTANT: Write your response in {output_language}."""


def get_brand_queries(brand: str) -> list[dict]:
    """Return the 5 standard questions with brand name filled in."""
    return [
        {**q, "question": q["question"].format(brand=brand)}
        for q in BRAND_QUERIES
    ]


def get_ground_truth_prompt(brand: str, crawl_data: dict) -> str:
    return GROUND_TRUTH_EXTRACTION.format(
        brand=brand,
        website_content=crawl_data.get("raw_text", "")[:3000],
        about_content=crawl_data.get("about_text", "")[:2000],
        structured_data=str(crawl_data.get("structured_data", {}))[:2000],
        page_title=crawl_data.get("title", ""),
        meta_description=crawl_data.get("meta_description", ""),
    )


def get_analysis_prompt(brand: str, ground_truth: str, responses: dict) -> str:
    return ANALYZE_MODEL_RESPONSE.format(
        brand=brand,
        ground_truth=ground_truth,
        mention_brand=brand,
        mention_response=responses.get("mention", ""),
        accuracy_response=responses.get("accuracy", ""),
        differentiation_response=responses.get("differentiation", ""),
        depth_response=responses.get("depth", ""),
        blindspot_response=responses.get("blindspot", ""),
    )


def get_comparison_prompt(brand: str, ground_truth: str, doubao_eval: str, deepseek_eval: str) -> str:
    return CROSS_MODEL_COMPARISON.format(
        brand=brand,
        ground_truth=ground_truth,
        doubao_eval=doubao_eval,
        deepseek_eval=deepseek_eval,
    )
