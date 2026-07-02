# ZKONER

> **ZKoner is a cognitive identity system that defines how AI understands entities within a domain. It turns brands into structured, AI-readable signals across the web.**
>
> **ZKoner 是一个认知身份系统，将品牌转化为 AI 可理解的结构化信号。**

**ZKoner 帮助品牌理解 AI 如何认识自己，并持续优化这种认知。**

**使命: 让每一个品牌都能建立、监测和优化自己在 AI 世界中的认知。**

**愿景: 未来每家公司管理三件事 — 官网 / 社交媒体 / AI认知。ZKoner 就是第三项。**

AI Brand Intelligence Platform.

## Core Loop

```
Scan ──→ Insight ──→ Action ──→ Verify ──→ Monitor ──→ Loop
```

Observe → Understand → Improve → Monitor (检测 → 理解 → 修正 → 持续监控)

## Product Line

| Product | Capabilities |
|---------|-------------|
| **ZKoner Scan** | AI detection, visibility analysis, AI answer sampling |
| **ZKoner Insight** | AI cognition analysis, Entity analysis, Gap analysis |
| **ZKoner Action** | Fix suggestions, Content suggestions, Schema suggestions |
| **ZKoner Monitor** | Daily monitoring, Trend changes, Email notifications |
| _ZKoner API / ZKoner Agent / ZKoner Studio_ | _Future_ |

## Stack

- **Frontend**: Next.js + Tailwind (`localhost:3000`)
- **Backend**: Python FastAPI + AI Pipeline (`localhost:8000`)
- **Storage**: SQLite (v0.1)

## Quick Start

```bash
cd /home/zxm/zkoner
bash scripts/start.sh
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/analyze` | Submit brand for analysis |
| GET | `/api/analysis/{id}` | Get analysis result |
| GET | `/api/analyses/recent` | Recent analyses |

## Core Modules (Dashboard)

1. **AI Visibility** — Score + breakdown
2. **AI Perception** — How AI "thinks" about your brand
3. **Missing Signals** — Gaps in structure/content/authority/clarity
4. **Recommended Actions** — Prioritized improvement plan
5. **Monitoring Timeline** — Progress tracking

## Mode

- **Mock mode** (default): Runs without API key for dev/demo
- **Live mode**: Set `CLAUDE_API_KEY` in `backend/.env` for real LLM analysis
