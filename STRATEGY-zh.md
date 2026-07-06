# ZKONER 核心策略：双模型语义检测

## 为什么是豆包 + DeepSeek

中国市场的 AI 搜索格局：

```
百度系（文心一言） — 传统搜索基因，份额在下滑
字节系（豆包）     — 国内 C 端用户量最大，增长最快
DeepSeek           — 开发者/技术圈影响力最强，开源生态最大
Kimi               — 长文本场景强，但总用户量不及前三
通义千问           — 阿里系，企业用户多
```

**选择豆包 + DeepSeek 的理由：**

| 维度 | 豆包 (Doubao) | DeepSeek |
|------|--------------|----------|
| 用户基数 | 国内最大 C 端 AI 应用 | 开发者/技术决策者 |
| 搜索行为 | 普通消费者「查品牌」的主战场 | B2B/技术品牌的认知来源 |
| API 可用性 | 火山引擎，OpenAI 兼容 | DeepSeek API，OpenAI 兼容 |
| 语义特征 | 偏消费、生活、商业 | 偏技术、深度、逻辑 |

**两个模型覆盖了品牌在 AI 世界中最关键的两种认知：**
- 豆包 → 消费者视角：「这个品牌怎么样？」
- DeepSeek → 专业视角：「这个品牌的技术/实力如何？」

---

## 核心检测逻辑

### 不再模拟 AI，而是真的问 AI

```
旧逻辑（启发式）:
  爬网站 → 看有没有 schema → 打分

新逻辑（双模型语义）:
  爬网站建立 ground truth
        ↓
  对豆包、DeepSeek 分别发问（标准 prompt 模板）
        ↓
  对比 AI 回答 vs ground truth
        ↓
  计算 5 维评分
        ↓
  生成缺口报告 + 优化建议
```

### 标准 Prompt 模板（每个模型问 5 个问题）

```
Q1: 「{brand} 是什么？」                           → 提及度
Q2: 「{brand} 主要做什么？有什么特点？」              → 认知准确性
Q3: 「{brand} 的竞争对手有哪些？它和竞争对手的区别？」 → 竞争格局
Q4: 「{brand} 在行业中的地位如何？」                 → 权威感知
Q5: 「关于 {brand}，有哪些常见的误解或不知道的事？」  → 信息缺口
```

每个问题的回答由 LLM（Claude）分析并打分，而非启发式规则。

---

## 5 维评分体系（升级版）

| 维度 | 权重 | 检测方法 |
|------|------|----------|
| **提及度** | 20% | 两个模型是否都能识别该品牌？回答长度和信息量 |
| **准确性** | 30% | 模型描述是否与 ground truth 一致？是否有事实错误？ |
| **一致性** | 15% | 豆包和 DeepSeek 的描述是否一致？差异在哪？ |
| **深度** | 20% | 模型对品牌的理解深度（笼统 vs 具体） |
| **差异化** | 15% | 模型是否能区分品牌与竞争对手？ |

---

## 技术架构

```
┌──────────────────────────────────────────────────────┐
│                   ZKONER Engine v2                     │
│                                                        │
│  Frontend (Next.js) ─ 显示双模型对比 + 评分 + 建议      │
│       ↓                                                │
│  API Layer (FastAPI)                                   │
│       ↓                                                │
│  ┌─────────────────────────────────────────────┐       │
│  │           Analysis Pipeline                   │       │
│  │                                                │       │
│  │  ① Crawler → 网站 ground truth                 │       │
│  │  ② DoubaoAdapter → 问豆包 5 个问题             │       │
│  │  ③ DeepSeekAdapter → 问 DeepSeek 5 个问题      │       │
│  │  ④ CompareEngine → 对比 + 评分                 │       │
│  │  ⑤ ReportGenerator → 报告 + 建议               │       │
│  └─────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────┘
```

### 适配器接口（已有 `BaseEngineAdapter`）

```python
class DoubaoAdapter(BaseEngineAdapter):
    """调用豆包 API（火山引擎），OpenAI 兼容"""
    model = "doubao-pro-32k"  # 或其他豆包模型
    endpoint = "https://ark.cn-beijing.volces.com/api/v3"

class DeepSeekAdapter(BaseEngineAdapter):
    """调用 DeepSeek API，OpenAI 兼容"""
    model = "deepseek-chat"
    endpoint = "https://api.deepseek.com"
```

两个适配器使用相同的 OpenAI 兼容 API，通过 `openai` Python SDK 调用。

---

## Prompt 工程（核心资产）

### Ground Truth 提取 Prompt

```
根据以下网站信息，提取 {brand} 的 ground truth：

网站内容: {crawl_data}
结构化数据: {structured_data}

请提取：
1. 一句话描述（品牌是什么）
2. 核心特点（3-5个）
3. 主要产品/服务
4. 目标用户
5. 行业分类
6. 关键差异化因素
```

### AI 认知分析 Prompt（Claude 分析豆包/DeepSeek 的回复）

```
以下是 AI 模型对「{brand}」的回答：

{model_response}

Ground truth（来自品牌官网）：
{ground_truth}

请分析：
1. 提及度评分 (0-100)：回答是否包含品牌关键信息？
2. 准确性评分 (0-100)：是否有事实错误？
3. 深度评分 (0-100)：回答是否具体还是笼统？
4. 差异化评分 (0-100)：是否区分了品牌与竞争对手？
5. 信息缺口：AI 遗漏了什么？品牌在 AI 认知中有哪些盲区？
6. 优化建议：品牌应该做什么来提高 AI 对该维度的认知？
```

---

## Dashboard 升级

当前 5 模块升级为双模型对比视图：

| 模块 | 升级前 | 升级后 |
|------|--------|--------|
| AI Visibility | 单一评分 | 豆包 + DeepSeek 双评分对比 |
| AI Perception | 启发式画像 | 两个模型的真实回答分析 |
| Missing Signals | 网站层面的缺口 | 基于 AI 回答的语义缺口 |
| Recommended Actions | 通用建议 | 针对具体 AI 模型的优化建议 |
| Timeline | 评分历史 | 双模型趋势对比 |

---

## 实现路径

### Phase 1：双模型适配器（当前）
- [ ] `DoubaoAdapter` — 火山引擎 API 接入
- [ ] `DeepSeekAdapter` — DeepSeek API 接入
- [ ] Ground truth extractor — Claude 提取品牌 ground truth
- [ ] 标准 Prompt 模板 — 5 个问题的中英文版

### Phase 2：对比引擎
- [ ] `CompareEngine` — 对比两个模型的回答
- [ ] 5 维评分升级为双模型版本
- [ ] Claude 作为分析器，评估豆包/DeepSeek 的回答质量

### Phase 3：Dashboard 升级
- [ ] 双模型评分卡片
- [ ] 回答对比视图（豆包怎么说 vs DeepSeek 怎么说）
- [ ] 语义缺口可视化
- [ ] 针对性优化建议

### Phase 4：持续监控
- [ ] 定时任务每日采样
- [ ] 评分趋势追踪
- [ ] 变化告警（模型对你的认知变了）

---

## API Keys 需求

| 服务 | 用途 | 获取方式 |
|------|------|----------|
| 火山引擎 API | 调用豆包 | console.volcengine.com → 开通豆包 → 获取 API Key |
| DeepSeek API | 调用 DeepSeek | platform.deepseek.com → API Keys |
| Claude API | 分析 AI 回答（可选，可用启发式替代） | console.anthropic.com |

---

## 护城河

1. **Prompt 模板库** — 5 个标准问题的调优是最核心的资产，直接影响分析质量
2. **双模型对比方法** — 不是看单一模型，而是对比两个模型的认知差异
3. **Ground truth 对齐** — 知道「真实的品牌信息」才能判断 AI 是否准确
4. **中国市场专精** — 豆包 + DeepSeek 的组合是中文 AI 搜索的最佳覆盖
