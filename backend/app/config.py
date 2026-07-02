"""Application configuration."""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# LLM API
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-20251001")

# Crawler
CRAWL_TIMEOUT = int(os.getenv("CRAWL_TIMEOUT", "15000"))  # ms
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Scoring defaults
SCORE_WEIGHTS = {
    "mention": 0.20,       # Is the brand mentioned clearly
    "consistency": 0.25,   # Semantic consistency across sources
    "structure": 0.20,     # Structured data (schema.org, etc.)
    "authority": 0.20,     # External signals (backlinks, citations)
    "clarity": 0.15,       # Is brand purpose/value proposition clear
}
