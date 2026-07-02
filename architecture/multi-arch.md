# ZKONER 多语言 · 多模型 · 多区域 · 同一代码库架构

> **One Codebase. Any Language. Any Engine. Any Region.**

---

## 目录

1. [设计原则](#1-设计原则)
2. [总体架构](#2-总体架构)
3. [多语言架构 (Multi-language)](#3-多语言架构)
4. [多模型架构 (Multi-model)](#4-多模型架构)
5. [多区域架构 (Multi-region)](#5-多区域架构)
6. [统一配置模型](#6-统一配置模型)
7. [数据流详解](#7-数据流详解)
8. [目录结构](#8-目录结构)
9. [开发指南](#9-开发指南)
10. [路线图](#10-路线图)

---

## 1. 设计原则

### 1.1 分层隔离，核心不变

```
┌─────────────────────────────────────────────┐
│          Engine Layer    (可变)              │
├─────────────────────────────────────────────┤
│          Localization Layer (可变)           │
├─────────────────────────────────────────────┤
│          Region Layer     (可变)             │
├─────────────────────────────────────────────┤
│          Core Layer       (不变)             │
│   Scoring / Storage / Schemas / API Router  │
└─────────────────────────────────────────────┘
```

**Core Layer** 必须对 language / engine / region 完全无感知。它是纯数学模型和数据模型。

### 1.2 Engine 是插件，不是内置功能

每个 AI 引擎（ChatGPT、DeepSeek、Kimi、秘塔、元宝、Google AI、Perplexity…）是一个 adapter，实现统一接口。新增引擎 = 新增一个文件，不改已有代码。

### 1.3 Region 是配置集，不是代码分支

没有 "国内版" 和 "海外版" 两个项目。Region 只是一组 `{available_engines, default_language, proxy_config, compliance_rules}` 的配置。

### 1.4 语言是运行时参数，不是构建时参数

UI 和报告的语言在请求时决定（Accept-Language header 或用户设置）。不是编译时静态生成。

---

## 2. 总体架构

```
                          ┌─────────────────────┐
                          │     Frontend UI      │
                          │  (Next.js + i18n)   │
                          │  中 / EN / auto      │
                          └─────────┬───────────┘
                                    │
                          ┌─────────▼───────────┐
                          │   API Gateway        │
                          │  lang / region 路由  │
                          └─────────┬───────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
          ┌─────────▼──────┐ ┌──────▼────────┐ ┌───▼──────────┐
          │ Engine Router  │ │   Locale      │ │  Region      │
          │ (model选择器)  │ │   Service     │ │  Config      │
          └─────────┬──────┘ └──────┬────────┘ └───┬──────────┘
                    │               │               │
          ┌─────────▼───────────────▼───────────────▼──────────┐
          │                Analysis Pipeline                    │
          │  Crawl → Perceive → Gap Detect → Score → Optimize │
          │  (每个步骤感知 language / region 上下文)            │
          └─────────────────────┬──────────────────────────────┘
                                │
          ┌─────────────────────▼──────────────────────────────┐
          │                 Storage Layer                       │
          │   SQLite (dev) / PostgreSQL (prod)                  │
          │   Multi-region sharding (future)                    │
          └────────────────────────────────────────────────────┘
```

### 核心概念

| 概念 | 定义 | 示例 |
|------|------|------|
| **Engine** | 一个 AI 对话/搜索服务 | ChatGPT, DeepSeek, Kimi, 秘塔 |
| **Region** | 一个地理/法规区域 | `cn` (中国大陆), `global` (海外) |
| **Locale** | 一个语言-地区组合 | `en-US`, `zh-CN`, `zh-TW`, `ja-JP` |
| **Analysis** | 一次完整的品牌分析 | 对一个品牌在指定引擎上的可见度评估 |

---

## 3. 多语言架构

### 3.1 架构一览

```
┌───────────────────────────────────────────────────┐
│  UI Layer (i18n) — 用户可见部分                    │
│  ┌─────────────────────────────────────────────┐  │
│  │  zkoner.com/  → English UI                  │  │
│  │  zkoner.com/zh/ → 中文 UI                   │  │
│  │  只翻译框架文案，AI内容保持英文              │  │
│  └─────────────────────────────────────────────┘  │
├───────────────────────────────────────────────────┤
│  API Layer (Always English)                       │
│  ┌─────────────────────────────────────────────┐  │
│  │  所有字段、错误、日志 = English              │  │
│  │  locale 仅前端使用，API 不感知              │  │
│  └─────────────────────────────────────────────┘  │
├───────────────────────────────────────────────────┤
│  AI Pipeline (Always English Prompts)             │
│  ┌─────────────────────────────────────────────┐  │
│  │  LLM 阅读中文/日文内容 → 输出英文分析       │  │
│  │  不需要多语言 Prompt 模板                   │  │
│  └─────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────┘
```

### 3.2 路由策略

```
zkoner.com/        → English (默认)
zkoner.com/zh/     → 中文

未来扩展:
zkoner.com/ja/     → 日本語
```

- English 无前缀（SEO 友好）
- 中文 `/zh/` 前缀
- `next-intl` 的 path-based routing 天然支持

### 3.3 UI i18n

使用 `next-intl`，只翻译用户可见的 UI 控件文案：

```
frontend/messages/
├── en/
│   ├── common.json        # 全局: 按钮、错误、状态
│   ├── home.json           # 首页: 标题、副标题、提示
│   ├── dashboard.json      # 仪表盘: 模块标题、标签
│   └── report.json         # 报告: 分类名、说明
└── zh/
    ├── common.json
    ├── home.json
    ├── dashboard.json
    └── report.json
```

**关键原则**：翻译文件只包含 UI 框架文案。AI 生成的动态内容（perception summary、gap descriptions、action titles）**保持英文**，不翻译。

```
UI 框架文案 → 翻译文件 (next-intl)
AI 生成内容 → 保留英文（如摘要、描述、建议）
动态数据 → 保留英文（品牌名、URL、评分标签）
```

### 3.4 API 层（Always English）

API 所有字段保持英文，不引入 `LocalizedString` 类型：

```python
# ❌ 错误: 之前的设计
class ActionItem(BaseModel):
    title: LocalizedString    # {en: "...", zh: "..."}  太复杂

# ✅ 正确: 所有字段英文
class ActionItem(BaseModel):
    title: str                # "Add Organization Schema to homepage"
    description: str          # "Add schema.org/Organization JSON-LD markup..."
```

`locale` 参数只用于：
1. 前端选择 UI 语言
2. 未来可选的运行时翻译（调用 LLM 翻译文本）

### 3.5 AI Pipeline（Always English）

Prompt 模板**只有英文**，不维护中英双语：

```python
# backend/app/[locale]/  # 语言路由ai_engine/prompts/perception.py
PERCEPTION_PROMPT = """You are an AI brand perception analyst.
Analyze how AI systems would perceive this brand...

Brand: {brand}
Website Content (may be in Chinese):
{website_content}

Return your analysis in English only."""
```

LLM 的能力决定了它可以：
- 读中文网站内容 → 理解品牌 → **输出英文分析**
- 读中文搜索结果 → 理解上下文 → **输出英文缺口检测**
- 不需要我们做中英 Prompt 两套

```python
# ❌ 错误: 之前的设计（双语 Prompt）
PROMPT_REGISTRY = {
    "perception": {"en": PERCEPTION_EN, "zh": PERCEPTION_ZH},
}

# ✅ 正确: 纯英文 Prompt
PERCEPTION_PROMPT = """...Return in English only."""
```


### 3.3 语言总结

| 层面 | 语言 | 说明 |
|------|------|------|
| UI 框架文案 | 中/EN (可切换) | next-intl 翻译文件控制 |
| AI 生成内容 | English | 始终英文，不翻译 |
| API 字段 | English | 始终英文 |
| AI Prompts | English | 始终英文 |
| 数据库 | English | 字段名、存储值 |

```
zkoner.com/        → UI: English
zkoner.com/zh/     → UI: 中文
                      AI内容: 保留英文
```

---

## 4. 多模型架构

### 4.1 Engine Adapter 接口

每个 AI 搜索引擎实现统一接口：

```python
# backend/app/[locale]/  # 语言路由engines/base.py
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class EngineCapability(Enum):
    WEB_SEARCH = "web_search"            # 传统网页搜索
    AI_CHAT = "ai_chat"                   # AI 对话回答
    NEWS = "news"                         # 新闻搜索
    VIDEO = "video"                       # 视频搜索
    IMAGE = "image"                       # 图片搜索


class EngineRegion(Enum):
    GLOBAL = "global"                     # 全球可用
    CN_ONLY = "cn_only"                   # 仅中国大陆
    CN_PREFERRED = "cn_preferred"         # 中国为主，海外可用


@dataclass
class EngineInfo:
    """每个引擎的元信息"""
    id: str                               # chatgpt, deepseek, kimi, etc.
    name: str                             # 显示名
    name_zh: str                          # 中文显示名
    capabilities: list[EngineCapability]
    region: EngineRegion
    auth_required: bool                   # 需要登录/API Key？
    rate_limit: int                       # 每分钟请求上限
    base_url: str                         # API 或 Web URL


@dataclass
class EngineSearchResult:
    """统一搜索结果结构"""
    title: str
    url: str
    snippet: str
    position: int                         # 排名位置
    source: str                           # engine id
    published_date: Optional[str] = None
    is_featured: bool = False             # AI 精选/摘要结果


@dataclass
class EngineQueryResult:
    """一次查询的完整结果"""
    query: str
    engine_id: str
    results: list[EngineSearchResult]
    ai_answer: Optional[str] = None       # AI 直接回答内容
    total_results: Optional[int] = None
    error: Optional[str] = None
    response_time_ms: Optional[int] = None


class BaseEngineAdapter(ABC):
    """所有 AI 引擎适配器的基类"""

    @property
    @abstractmethod
    def info(self) -> EngineInfo:
        ...

    @abstractmethod
    async def search(self, query: str, **kwargs) -> EngineQueryResult:
        """执行一次搜索/查询"""
        ...

    @abstractmethod
    async def health(self) -> bool:
        """检查引擎是否可用"""
        ...
```

### 4.2 引擎实现示例

```python
# backend/app/[locale]/  # 语言路由engines/chatgpt.py
from app.engines.base import BaseEngineAdapter, EngineInfo, EngineSearchResult, ...


class ChatGPTAdapter(BaseEngineAdapter):
    """ChatGPT (chatgpt.com) 引擎适配器"""

    @property
    def info(self) -> EngineInfo:
        return EngineInfo(
            id="chatgpt",
            name="ChatGPT",
            name_zh="ChatGPT",
            capabilities=[EngineCapability.AI_CHAT, EngineCapability.WEB_SEARCH],
            region=EngineRegion.GLOBAL,
            auth_required=True,          # 需要 OpenAI 账号
            rate_limit=30,
            base_url="https://chatgpt.com",
        )

    async def search(self, query: str, **kwargs) -> EngineQueryResult:
        """通过 Playwright/Scrapling 模拟浏览器访问 ChatGPT"""
        # 1. 初始化浏览器 session
        # 2. 导航到 chatgpt.com
        # 3. 输入 query
        # 4. 等待 AI 回答
        # 5. 提取搜索结果 + AI answer
        # 6. 返回规范化结果
        ...

    async def health(self) -> bool:
        # 检查 chatgpt.com 可达性
        ...
```

```python
# backend/app/[locale]/  # 语言路由engines/deepseek.py

class DeepSeekAdapter(BaseEngineAdapter):
    """DeepSeek (chat.deepseek.com) — 国内主流 AI 搜索引擎"""

    @property
    def info(self) -> EngineInfo:
        return EngineInfo(
            id="deepseek",
            name="DeepSeek",
            name_zh="DeepSeek",
            capabilities=[EngineCapability.AI_CHAT, EngineCapability.WEB_SEARCH],
            region=EngineRegion.CN_PREFERRED,
            auth_required=False,         # 无需登录也可使用
            rate_limit=20,
            base_url="https://chat.deepseek.com",
        )

    async def search(self, query: str, **kwargs) -> EngineQueryResult:
        # DeepSeek 的搜索实现
        ...
```

```python
# backend/app/[locale]/  # 语言路由engines/kimi.py

class KimiAdapter(BaseEngineAdapter):
    """Kimi (kimi.moonshot.cn) — 月之暗面"""

    @property
    def info(self) -> EngineInfo:
        return EngineInfo(
            id="kimi",
            name="Kimi",
            name_zh="Kimi",
            capabilities=[EngineCapability.AI_CHAT, EngineCapability.WEB_SEARCH],
            region=EngineRegion.CN_ONLY,
            auth_required=False,
            rate_limit=20,
            base_url="https://kimi.moonshot.cn",
        )
```

```python
# backend/app/[locale]/  # 语言路由engines/mita.py

class MitaAdapter(BaseEngineAdapter):
    """秘塔 AI (metaso.cn) — 中国 AI 搜索引擎"""

    @property
    def info(self) -> EngineInfo:
        return EngineInfo(
            id="mita",
            name="Mita AI",
            name_zh="秘塔AI",
            capabilities=[EngineCapability.AI_CHAT, EngineCapability.WEB_SEARCH],
            region=EngineRegion.CN_ONLY,
            auth_required=False,        # 无需登录
            rate_limit=30,
            base_url="https://metaso.cn",
        )

    async def search(self, query: str, **kwargs) -> EngineQueryResult:
        # 秘塔无需登录，可以直接 HTTP 请求
        ...
```

```python
# backend/app/[locale]/  # 语言路由engines/perplexity.py

class PerplexityAdapter(BaseEngineAdapter):
    """Perplexity AI — 海外 AI 搜索引擎"""

    @property
    def info(self) -> EngineInfo:
        return EngineInfo(
            id="perplexity",
            name="Perplexity",
            name_zh="Perplexity",
            capabilities=[EngineCapability.AI_CHAT, EngineCapability.WEB_SEARCH],
            region=EngineRegion.GLOBAL,
            auth_required=False,         # 无需登录也可使用
            rate_limit=30,
            base_url="https://www.perplexity.ai",
        )

    async def search(self, query: str, **kwargs) -> EngineQueryResult:
        # Perplexity 无需登录，可直接 HTTP 请求
        ...
```

### 4.3 Engine Registry

```python
# backend/app/[locale]/  # 语言路由engines/registry.py
from typing import Optional
from app.engines.base import BaseEngineAdapter, EngineRegion


class EngineRegistry:
    """所有引擎适配器的注册中心"""

    _adapters: dict[str, type[BaseEngineAdapter]] = {}

    @classmethod
    def register(cls, adapter_cls: type[BaseEngineAdapter]):
        instance = adapter_cls()
        cls._adapters[instance.info.id] = adapter_cls
        return adapter_cls

    @classmethod
    def get(cls, engine_id: str) -> Optional[BaseEngineAdapter]:
        cls._ensure_loaded()
        adapter_cls = cls._adapters.get(engine_id)
        return adapter_cls() if adapter_cls else None

    @classmethod
    def list_for_region(cls, region: str) -> list[BaseEngineAdapter]:
        """获取某区域可用的所有引擎"""
        cls._ensure_loaded()
        region_map = {
            "cn":    [EngineRegion.CN_ONLY, EngineRegion.CN_PREFERRED, EngineRegion.GLOBAL],
            "global": [EngineRegion.GLOBAL, EngineRegion.CN_PREFERRED],
        }
        allowed = region_map.get(region, [EngineRegion.GLOBAL])
        return [
            cls.get(eid)
            for eid, cls_ in cls._adapters.items()
            if cls_().info.region in allowed
        ]

    @classmethod
    def _ensure_loaded(cls):
        """Lazy-load all engine modules so imports don't slow startup."""
        import importlib, pkgutil
        import app.engines
        for importer, modname, ispkg in pkgutil.iter_modules(app.engines.__path__):
            if modname not in ("base", "registry"):
                importlib.import_module(f"app.engines.{modname}")

    @classmethod
    def list_all(cls) -> list[dict]:
        """列出所有引擎信息（用于前端选择器）"""
        return [
            {"id": eid, **cls_().info.__dict__}
            for eid, cls_ in cls._adapters.items()
        ]
```

### 4.4 Engine Router（多引擎调度器）

```python
# backend/app/[locale]/  # 语言路由engines/router.py
from app.engines.registry import EngineRegistry
from app.engines.base import EngineQueryResult


class EngineRouter:
    """
    多引擎查询调度器。
    根据 region 和 selected_engines 决定查询哪些引擎。
    """

    def __init__(self, region: str, engines: list[str] | None = None):
        self.region = region
        self.engines = engines or []  # 空列表 = 使用 region 默认

    def resolve(self) -> list:
        """解析出最终要查询的引擎列表"""
        if self.engines:
            return [e for eid in self.engines if (e := EngineRegistry.get(eid))]
        return EngineRegistry.list_for_region(self.region)

    async def query_all(self, query: str) -> dict[str, EngineQueryResult]:
        """并行查询所有选定引擎"""
        adapters = self.resolve()
        import asyncio
        tasks = {a.info.id: a.search(query) for a in adapters}
        results = {}
        for eid, task in tasks.items():
            try:
                results[eid] = await task
            except Exception as ex:
                results[eid] = EngineQueryResult(
                    query=query, engine_id=eid,
                    results=[], error=str(ex),
                )
        return results
```

### 4.5 引擎接入方式分类

| 方式 | 适用引擎 | 复杂度 | 稳定性 |
|------|---------|--------|--------|
| **HTTP API**（官方 API） | Perplexity API, OpenAI API | ★☆☆ | ★★★ |
| **HTTP 无头（无登录）** | 秘塔, Perplexity Web | ★★☆ | ★★☆ |
| **Playwright 浏览器（有登录）** | ChatGPT, DeepSeek(高级) | ★★★ | ★☆☆ |
| **Playwright 浏览器（无登录）** | Kimi, 豆包 | ★★☆ | ★★☆ |
| **移动端 API 逆向** | — (不推荐，法律风险) | ★★★★ | — |

**策略**：优先用最简单稳定的方式（HTTP API > HTTP 无头 > Playwright 无登录 > Playwright 有登录）

---

## 5. 多区域架构

### 5.1 Region 配置模型

每个 region 是一组命名的配置：

```python
# backend/app/[locale]/  # 语言路由region/config.py
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CrawlerConfig:
    """爬虫的区域配置"""
    user_agent: str
    timeout_ms: int = 15000
    proxy: Optional[str] = None          # 代理地址
    use_proxy_pool: bool = False         # 是否使用代理池
    respect_robots_txt: bool = True


@dataclass
class ComplianceConfig:
    """合规配置"""
    data_retention_days: int = 90        # 数据保留天数
    require_consent: bool = True         # 是否需要用户同意
    gdpr_mode: bool = False              # GDPR 模式
    cn_regulation_mode: bool = False     # 中国法规模式
    export_restricted: bool = False      # 数据是否限制导出


@dataclass
class RegionConfig:
    """完整的区域配置"""
    id: str                              # "cn", "global"
    label: str                           # "中国大陆", "Global"
    default_locale: str                  # "zh-CN", "en-US"
    supported_locales: list[str]         # 支持的语言
    available_engines: list[str]         # 可用引擎 ID 列表
    default_engines: list[str]           # 默认引擎列表
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    compliance: ComplianceConfig = field(default_factory=ComplianceConfig)
    host: str = "localhost"              # API Host


# ── 预定义 Region ──

REGIONS: dict[str, RegionConfig] = {
    "global": RegionConfig(
        id="global",
        label="Global",
        default_locale="en-US",
        supported_locales=["en-US", "zh-CN", "ja-JP"],
        available_engines=["chatgpt", "perplexity", "google_ai", "gemini"],
        default_engines=["chatgpt", "perplexity"],
        crawler=CrawlerConfig(
            user_agent="Mozilla/5.0 (compatible; ZKONER/1.0; +https://zkoner.com)",
            timeout_ms=15000,
        ),
        compliance=ComplianceConfig(
            data_retention_days=90,
            gdpr_mode=True,
        ),
    ),
    "cn": RegionConfig(
        id="cn",
        label="中国大陆",
        default_locale="zh-CN",
        supported_locales=["zh-CN", "en-US"],
        available_engines=["deepseek", "kimi", "mita", "doubao", "yuanbao"],
        default_engines=["deepseek", "kimi", "mita"],
        crawler=CrawlerConfig(
            user_agent="Mozilla/5.0 (Linux; Android 13; ...)",
            timeout_ms=20000,
            use_proxy_pool=True,
        ),
        compliance=ComplianceConfig(
            data_retention_days=180,
            cn_regulation_mode=True,
        ),
    ),
}


def get_region(region_id: str) -> RegionConfig:
    return REGIONS.get(region_id, REGIONS["global"])
```

### 5.2 Region 路由与部署

```
                    ┌──────────────────┐
                    │   zkoner.com     │ ← 全球 CDN
                    │   (Cloudflare)   │
                    └────────┬─────────┘
                             │
               ┌─────────────┴─────────────┐
               │                           │
    ┌──────────▼──────────┐    ┌───────────▼──────────┐
    │   global cluster    │    │     cn cluster        │
    │   (AWS/Azure EU/US) │    │   (阿里云 / 腾讯云)   │
    │   Region: global    │    │   Region: cn          │
    │   Engines: chatgpt  │    │   Engines: deepseek   │
    │            perplexity│    │            kimi       │
    │            gemini    │    │            mita       │
    └─────────────────────┘    └──────────────────────┘
               │                           │
               └─────────────┬─────────────┘
                             │
                    ┌────────▼────────┐
                    │   Shared DB     │
                    │  (读写分离)     │
                    │  Multi-region   │
                    │  sharding (未来)│
                    └─────────────────┘
```

**部署策略**：
- 同一套 Docker 镜像部署到两个集群
- 环境变量 `ZKONER_REGION=global` 或 `ZKONER_REGION=cn`
- 中国集群通过域名/IP 自动路由到国内引擎
- 全球集群自动路由到海外引擎
- 数据层按 region 标签分表（未来按需分库）

### 5.3 Region 检测与自动选择

```python
# backend/app/[locale]/  # 语言路由region/detect.py
import ipaddress
from typing import Optional


# 中国 IP 范围（简化版）
CN_IP_RANGES = [
    ipaddress.ip_network("1.0.0.0/8"),
    ipaddress.ip_network("14.0.0.0/8"),
    ipaddress.ip_network("36.0.0.0/8"),
    ipaddress.ip_network("39.0.0.0/8"),
    # ... 完整的中国 IP 列表
]


def detect_region_from_ip(client_ip: str) -> str:
    """根据客户端 IP 自动检测区域"""
    try:
        ip = ipaddress.ip_address(client_ip)
        for r in CN_IP_RANGES:
            if ip in r:
                return "cn"
        return "global"
    except ValueError:
        return "global"


def detect_region_from_headers(headers: dict) -> str:
    """从请求 headers 检测区域（Cloudflare/阿里云 CDN 注入）"""
    # Cloudflare: cf-ipcountry
    country = headers.get("cf-ipcountry", "").upper()
    if country == "CN":
        return "cn"
    # 阿里云 CDN: ali-cf-country
    country = headers.get("ali-cf-country", "")
    if country == "CN":
        return "cn"
    return "unknown"
```

### 5.4 合规管理

```python
# backend/app/[locale]/  # 语言路由compliance/manager.py
from app.region.config import ComplianceConfig


class ComplianceManager:
    """多区域合规管理器"""

    def __init__(self, config: ComplianceConfig):
        self.config = config

    def check_data_retention(self, created_at) -> bool:
        """检查数据是否超期"""
        from datetime import datetime, timezone, timedelta
        age = datetime.now(timezone.utc) - created_at
        return age.days <= self.config.data_retention_days

    def sanitize_output(self, data: dict, locale: str) -> dict:
        """根据区域法规清理输出数据"""
        if self.config.gdpr_mode:
            data = self._apply_gdpr(data)
        if self.config.cn_regulation_mode:
            data = self._apply_cn_regulations(data)
        return data

    def _apply_gdpr(self, data: dict) -> dict:
        """GDPR: 移除个人信息，添加数据来源说明"""
        ...

    def _apply_cn_regulations(self, data: dict) -> dict:
        """中国法规：内容合规检查"""
        ...
```

---

## 6. 统一配置模型

### 6.1 环境变量

```bash
# ── 核心 ──
ZKONER_REGION=global               # global | cn
ZKONER_ENV=development              # development | staging | production

# ── 语言 ──
ZKONER_DEFAULT_LOCALE=en-US        # 默认语言
ZKONER_SUPPORTED_LOCALES=en-US,zh-CN

# ── 引擎 ──
ZKONER_ENGINES=chatgpt,perplexity   # 启用的引擎（逗号分隔）
ZKONER_ENGINE_TIMEOUT=30000         # 引擎查询超时 (ms)

# ── 爬虫 ──
ZKONER_CRAWL_TIMEOUT=15000
ZKONER_CRAWL_PROXY=                # 代理地址（可选）
ZKONER_CRAWL_USE_PROXY_POOL=false

# ── AI 分析 ──
CLAUDE_API_KEY=                     # 分析 LLM 的 API Key
CLAUDE_MODEL=claude-sonnet-5-20251001

# ── 合规 ──
ZKONER_DATA_RETENTION_DAYS=90
ZKONER_GDPR_MODE=false
```

### 6.2 请求级参数

```json
POST /api/analyze
{
  "brand": "Anthropic",
  "url": "https://anthropic.com",
  "locale": "zh-CN",
  "region": "global",
  "engines": ["chatgpt", "perplexity"],
  "reanalysis_id": "a284d544"
}
```

| 参数 | 说明 | 默认 |
|------|------|------|
| `locale` | 报告语言 | 从 Accept-Language 检测 |
| `region` | 区域 | 从 IP/header 检测 |
| `engines` | 指定引擎数组 | 使用 region 默认引擎 |
| `reanalysis_id` | 重新分析（复用已有品牌信息） | null |

### 6.3 配置优先级

```
环境变量 (highest)
  → 请求参数
    → Region 预定义配置
      → 代码默认值 (lowest)
```

---

## 7. 数据流详解

### 7.1 完整分析流程（多语言/多模型/多区域）

```
用户请求
  │ locale=zh-CN, region=cn, engines=[deepseek, kimi]
  │ brand="深圳迈瑞医疗"
  ▼
┌─────────────────────────────────────────────────────────┐
│  1. 路由层                                               │
│     - 检测 region → cn                                  │
│     - 解析 locale → zh-CN                               │
│     - 解析引擎 → deepseek + kimi                        │
│     - 检测品牌语言 → zh (含中文)                         │
└─────────────────────────┬───────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  2. Engine Scan（并行）                                  │
│     ┌──────────┐    ┌──────────┐                         │
│     │ DeepSeek │    │  Kimi    │                         │
│     │ 搜:      │    │ 搜:      │                         │
│     │ "迈瑞医  │    │ "迈瑞医  │                         │
│     │  疗 AI"  │    │  疗 AI"  │                         │
│     └────┬─────┘    └────┬─────┘                         │
│          ▼               ▼                                │
│     [搜索结果]       [搜索结果]                           │
│     (规范化)         (规范化)                              │
└─────────────────────────┬───────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  3. 爬虫                                                 │
│     - 爬官网 (zh-CN 适配)                                │
│     - 爬 About 页面                                      │
│     - 提取结构化数据                                     │
│     - 语言检测 zh → 存储内容                             │
└─────────────────────────┬───────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
                          ▼
┌─────────────────────────────────────────────────────────┐
│  4. AI 感知分析（English Prompts）                       │
│     - LLM 读任何语言网站内容 → 英文分析                  │
│     - 输出英文 AIPerceptionProfile                       │
└─────────────────────────┬───────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  5. 缺口检测（English Prompts）                          │
│     - 英文 Prompt 检测结构/内容/权威性缺口               │
│     - GapItem 描述为英文                                 │
└─────────────────────────┬───────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  6. 评分（Language-agnostic）                            │
│     - 评分引擎不关心语言，只关心数据                     │
│     - 5 维度评分保持一致                                │
└─────────────────────────┬───────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  7. 优化建议生成（English Prompts）                      │
│     - 生成英文 ActionItem + Roadmap                     │
└─────────────────────────┬───────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  8. 返回                                                 │
│     - 所有字段英文                                       │
│     - Compliance 检查通过                                │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  8. 返回（根据 locale 展平）                             │
│     - 去除 LocalizedString 包装                          │
│     - 返回纯 zh-CN 文本                                │
│     - Compliance 检查通过                               │
└─────────────────────────────────────────────────────────┘
```

### 7.2 多引擎并行查询 vs 串行

```
场景 A: 所有引擎都可以直接 HTTP 请求
  ─────────────────────────────────────────
  DeepSeek ──→ HTTP GET ──→ 结果
  Kimi     ──→ HTTP GET ──→ 结果      ← 并行
  秘塔     ──→ HTTP GET ──→ 结果
  
  总时间 ≈ max(单个引擎时间)

场景 B: 部分引擎需要 Playwright 浏览器
  ─────────────────────────────────────────
  ChatGPT  ──→ Playwright session ──→ 结果
  Perplexity ──→ HTTP GET ──→ 结果       ← 浏览器与HTTP可并行
  Gemini   ──→ API call ──→ 结果
  
  总时间 ≈ max(浏览器时间, HTTP时间, API时间)
```

### 7.3 结果合并策略

多引擎扫描后，需要合并结果以形成统一的 AI 认知画像：

```python
# backend/app/[locale]/  # 语言路由engines/merger.py
from app.engines.base import EngineQueryResult


def merge_engine_results(results: dict[str, EngineQueryResult]) -> dict:
    """
    合并多个引擎的查询结果为一个统一的品牌可见度报告。

    合并维度：
    - 覆盖率：多少引擎提到了该品牌
    - 一致性：各引擎的描述是否一致
    - 排名：品牌在各引擎的平均排名
    - AI 回答：各引擎 AI 回答的内容（用于 perception 分析）
    """
    total = len(results)
    mentioned = sum(1 for r in results.values() if _is_mentioned(r))
    avg_position = _avg_position(results)

    return {
        "engine_coverage": mentioned / total if total > 0 else 0,
        "average_position": avg_position,
        "ai_answers": {eid: r.ai_answer for eid, r in results.items() if r.ai_answer},
        "by_engine": results,
    }
```

---

## 8. 目录结构

```
zkoner/
├── backend/
│   ├── app/[locale]/  # 语言路由
│   │   ├── main.py
│   │   ├── config.py                    # 全局配置
│   │   │
│   │   ├── models/
│   │   │   ├── schemas.py              # Pydantic schemas
│   │   │   └── enums.py                # Region, Locale, Engine 枚举
│   │   │
│   │   │
│   │   ├── engines/                    # ★ 多模型层
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # BaseEngineAdapter 接口
│   │   │   ├── registry.py             # 引擎注册中心
│   │   │   ├── router.py               # 多引擎调度器
│   │   │   ├── merger.py               # 结果合并
│   │   │   ├── chatgpt.py              # ChatGPT adapter
│   │   │   ├── deepseek.py             # DeepSeek adapter
│   │   │   ├── kimi.py                 # Kimi adapter
│   │   │   ├── mita.py                 # 秘塔 adapter
│   │   │   ├── doubao.py               # 豆包 adapter
│   │   │   ├── yuanbao.py              # 腾讯元宝 adapter
│   │   │   ├── perplexity.py           # Perplexity adapter
│   │   │   ├── gemini.py               # Google Gemini adapter
│   │   │   └── google_ai.py            # Google AI 搜索 adapter
│   │   │
│   │   ├── region/                     # ★ 多区域层
│   │   │   ├── config.py               # RegionConfig 定义
│   │   │   ├── detect.py               # IP/Header 区域检测
│   │   │   └── middleware.py           # FastAPI middleware
│   │   │
│   │   ├── compliance/                 # 合规管理
│   │   │   ├── manager.py              # 多区域合规
│   │   │   └── rules/                  # 各区域具体规则
│   │   │       ├── gdpr.py
│   │   │       └── cn_regulations.py
│   │   │
│   │   ├── ai_engine/                  # AI 分析引擎（不变）
│   │   │   ├── __init__.py
│   │   │   ├── prompts/               # English Prompts
│   │   │   │   ├── __init__.py         # PromptRegistry
│   │   │   └── service.py             # 核心分析逻辑
│   │   │
│   │   ├── crawler/                    # 爬虫层
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # 基础爬虫
│   │   │   ├── scrapling.py            # Scrapling 集成 (未来)
│   │   │   └── playwright.py           # Playwright 浏览器 (未来)
│   │   │
│   │   ├── scoring/                    # 评分引擎（完全语言无关）
│   │   │   └── __init__.py
│   │   │
│   │   ├── storage/                    # 存储层
│   │   │   ├── __init__.py
│   │   │   └── models/                 # ORM models
│   │   │
│   │   └── routers/                    # API 路由
│   │       └── analysis.py
│   │
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── messages/                       # ★ 翻译文件
│   │   ├── en/
│   │   │   ├── common.json
│   │   │   ├── home.json
│   │   │   ├── dashboard.json
│   │   │   └── report.json
│   │   └── zh/
│   │       ├── common.json
│   │       ├── home.json
│   │       ├── dashboard.json
│   │       └── report.json
│   │
│   ├── src/
│   │   │
│   │   ├── app/[locale]/  # 语言路由
│   │   │   ├── [locale]/              # ★ 语言路由
│   │   │   │   ├── page.js
│   │   │   │   ├── layout.js
│   │   │   │   └── analysis/[id]/page.js
│   │   │   └── ...
│   │   │
│   │   └── lib/
│   │       ├── api.js
│   │       └── locale.js              # 客户端 locale 工具
│   │
│   └── package.json
│
├── architecture/                       # 架构文档
│   └── multi-arch.md                   # ← 本文
│
├── scripts/
│   └── start.sh
│
├── README.md
├── CLAUDE.md
└── AGENTS.md
```

---

## 9. 开发指南

### 9.1 新增一个引擎

```python
# 1. 在 backend/app/[locale]/  # 语言路由engines/ 下新建文件
# 2. 继承 BaseEngineAdapter
# 3. 实现 info / search / health
# 4. 用 @EngineRegistry.register 装饰
# 5. 完成！

@app/[locale]/  # 语言路由engines/doubao.py
@EngineRegistry.register
class DoubaoAdapter(BaseEngineAdapter):
    ...
```

无需修改任何已有代码。EngineRegistry 的 `_ensure_loaded()` 会自动发现新模块。

### 9.2 新增一个语言

```
1. frontend/messages/{lang}/ 下新建翻译文件
2. backend/app/[locale]/  # 语言路由ai_engine/prompts/ 下新建 Prompt 模板
4. region config 的 supported_locales 添加语言
```

### 9.3 新增一个区域

```python
# 在 backend/app/[locale]/  # 语言路由region/config.py 的 REGIONS 字典添加
REGIONS["jp"] = RegionConfig(
    id="jp",
    label="日本",
    default_locale="ja-JP",
    supported_locales=["ja-JP", "en-US"],
    available_engines=["chatgpt", "perplexity", "gemini"],
    default_engines=["chatgpt", "perplexity"],
    ...
)
```

### 9.4 代码约定

| 原则 | 说明 |
|------|------|
| **Core 层禁止 import locale/engine/region** | Core 层不知道外面有什么语言和引擎 |
| **Adapter 只做一件事** | ChatGPTAdapter 只管和 ChatGPT 通信，不做分析 |
| **结果规范化在最外层做** | Engine 返回原始结果，由 registry 或 router 做归一 |
| **Locale 只向后传递** | 请求进入后确定 locale，下游全部使用同一 locale |
| **配置覆盖而非修改** | 不要改 RegionConfig 的默认值，用环境变量叠加 |

### 9.5 开发和生产环境

| 环境 | Region | 引擎 |
|------|--------|------|
| `development` | `global` | mock（无真实 API 调用） |
| `staging` | `global` | 真实引擎，但降频 |
| `production (global)` | `global` | ChatGPT + Perplexity + Gemini |
| `production (cn)` | `cn` | DeepSeek + Kimi + 秘塔 |

---

## 10. 路线图

### Phase 1: 架构落地 (当前 → 2周)
- [ ] 前端接入 next-intl，实现中英文路由切换
- [ ] 实现 BaseEngineAdapter + EngineRegistry
- [ ] 实现 RegionConfig + region 检测
- [ ] 纯英文 Prompt 确认 + 增加 Return in English only 指令
- [ ] 不需要（见上一项）
- [ ] 不需要（API 始终英文）

### Phase 2: 引擎实现 (2周 → 4周)
- [ ] 秘塔 adapter（HTTP 无头，无需登录）
- [ ] Perplexity adapter（HTTP 无头，无需登录）
- [ ] DeepSeek adapter（Playwright 无登录）
- [ ] Kimi adapter（Playwright 无登录）
- [ ] 多引擎并行查询 + 结果合并

### Phase 3: 区域化 (4周 → 6周)
- [ ] 中国区部署配置（阿里云 + 代理池）
- [ ] 合规管理（GDPR + 中国法规）
- [ ] IP/Header 自动区域检测
- [ ] 中国区前端 CDN 部署

### Phase 4: 高级引擎 (6周+)
- [ ] ChatGPT adapter（Playwright + 登录态维护）
- [ ] 豆包 / 元宝 adapter
- [ ] Google Gemini adapter
- [ ] Scrapling 集成替代手动浏览器操作

---

> **ZKONER: See Your Brand Through AI — 在任何语言，任何引擎，任何区域。**
