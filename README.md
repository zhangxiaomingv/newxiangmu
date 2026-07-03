# ZKONER — AI Brand Intelligence Platform

> **Measure how AI understands your brand — and continuously improve it.**
>
> **ZKoner 帮助品牌理解 AI 如何认识自己，并持续优化这种认知。**

未来每家公司管理三件事：**官网 / 社交媒体 / AI 认知。ZKoner 就是第三项。**

---

## Product Loop

```
Scan → Insight → Action → Verify → Monitor → Loop
```

## Quick Start

```bash
# Clone & run — no API key needed
cd zkoner
bash scripts/start.sh

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

Enter any brand name or URL → instant AI visibility analysis.

## Product Line

| Product | Capabilities |
|---------|-------------|
| **ZKoner Scan** | AI detection, visibility analysis, AI answer sampling |
| **ZKoner Insight** | AI cognition analysis, Entity analysis, Gap analysis |
| **ZKoner Action** | Fix suggestions, Content suggestions, Schema suggestions |
| **ZKoner Monitor** | Daily monitoring, Trend changes, Email notifications |

## Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16 + Tailwind CSS (dark theme) |
| **Backend** | Python FastAPI |
| **AI Engine** | Pluggable engine registry (EngineRegistry) |
| **Engine: Claude** | Anthropic Claude API (requires `CLAUDE_API_KEY`) |
| **Engine: Heuristic** | Built-in heuristic analysis — works out of the box |
| **Engine: Mock** | Canned data for demo |
| **Crawler** | httpx + BeautifulSoup |
| **Storage** | SQLite |

No API key is required to run — the heuristic engine provides real analysis purely from web crawl data.

## Dashboard (5 Modules)

1. **AI Visibility** — Score (0–100) across 5 dimensions
2. **AI Perception** — How AI "thinks" about your brand
3. **Missing Signals** — Gaps in structure / content / authority / clarity
4. **Recommended Actions** — Prioritised immediate + medium-term improvements
5. **Monitoring Timeline** — Re-analysis history & 5-stage roadmap

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analyze` | Submit brand for analysis |
| `GET` | `/api/analysis/{id}` | Get analysis result |
| `POST` | `/api/analyze/{id}/reanalyze` | Re-analyse a brand |
| `GET` | `/api/analysis/{id}/history` | Score history (timeline) |
| `GET` | `/api/analyses/recent` | Recent analyses |
| `GET` | `/api/brands` | Tracked brands |

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `AI_ENGINE` | `auto` | Engine selection: `auto`, `claude`, `metaso`, `mock` |
| `CLAUDE_API_KEY` | — | Set for Claude-powered analysis |
| `CLAUDE_MODEL` | `claude-sonnet-5-20251001` | Claude model ID |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api` | Backend URL (frontend) |

## Multi-language

- `/` — English (auto-detect browser language)
- `/zh` — Chinese
- Locale drives AI output language

## License

MIT
