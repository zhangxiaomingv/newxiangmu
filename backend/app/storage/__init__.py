"""SQLite-based storage for analysis results (v0.1 → v0.2 with monitoring)."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import DATA_DIR
from app.models.schemas import AnalysisResult, AnalysisStatus, ScoreSnapshot

DB_PATH = DATA_DIR / "zkoner.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if not exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            brand TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            url TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            result_json TEXT,
            progress TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS score_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            score REAL NOT NULL,
            score_breakdown TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_analyses_brand ON analyses(brand)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_score_history_brand ON score_history(brand)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_score_history_created ON score_history(created_at)
    """)
    conn.commit()
    conn.close()


def save_analysis(analysis: AnalysisResult):
    """Save completed analysis result and record a score snapshot."""
    conn = _get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO analyses
           (id, brand, status, url, created_at, completed_at, result_json)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            analysis.id,
            analysis.brand,
            analysis.status,
            None,
            analysis.created_at.isoformat(),
            datetime.now(timezone.utc).isoformat(),
            analysis.model_dump_json(),
        ),
    )
    # Record score history
    conn.execute(
        "INSERT INTO score_history (brand, score, score_breakdown, created_at) VALUES (?, ?, ?, ?)",
        (analysis.brand, analysis.score, json.dumps(analysis.score_breakdown), analysis.created_at.isoformat()),
    )
    conn.commit()
    conn.close()


def save_pending(analysis_id: str, brand: str):
    """Create a pending analysis entry."""
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO analyses (id, brand, status, created_at) VALUES (?, ?, 'pending', ?)",
        (analysis_id, brand, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def update_status(analysis_id: str, status: str, progress: str = ""):
    """Update analysis status."""
    conn = _get_conn()
    conn.execute(
        "UPDATE analyses SET status = ?, progress = ? WHERE id = ?",
        (status, progress, analysis_id),
    )
    conn.commit()
    conn.close()


def get_analysis(analysis_id: str) -> Optional[AnalysisResult]:
    """Retrieve analysis by ID."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT result_json FROM analyses WHERE id = ?", (analysis_id,)
    ).fetchone()
    conn.close()
    if row and row["result_json"]:
        return AnalysisResult.model_validate_json(row["result_json"])
    return None


def get_analysis_status(analysis_id: str) -> Optional[AnalysisStatus]:
    """Retrieve analysis status."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, brand, status, created_at, progress FROM analyses WHERE id = ?",
        (analysis_id,),
    ).fetchone()
    conn.close()
    if row:
        return AnalysisStatus(
            id=row["id"],
            brand=row["brand"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            progress=row.get("progress"),
        )
    return None


def get_latest_result(brand: str) -> Optional[AnalysisResult]:
    """Get the most recent completed analysis for a brand."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT result_json FROM analyses WHERE brand = ? AND status = 'completed' ORDER BY created_at DESC LIMIT 1",
        (brand,),
    ).fetchone()
    conn.close()
    if row and row["result_json"]:
        return AnalysisResult.model_validate_json(row["result_json"])
    return None


def get_score_history(brand: str, limit: int = 30) -> list[ScoreSnapshot]:
    """Get score history for a brand, most recent first."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT score, score_breakdown, created_at FROM score_history WHERE brand = ? ORDER BY created_at DESC LIMIT ?",
        (brand, limit),
    ).fetchall()
    conn.close()
    return [
        ScoreSnapshot(
            score=row["score"],
            score_breakdown=json.loads(row["score_breakdown"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


def list_recent(limit: int = 10) -> list[AnalysisStatus]:
    """List recent analyses."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, brand, status, created_at FROM analyses ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        AnalysisStatus(
            id=r["id"],
            brand=r["brand"],
            status=r["status"],
            created_at=datetime.fromisoformat(r["created_at"]),
        )
        for r in rows
    ]


def list_tracked_brands() -> list[str]:
    """List distinct brands that have been analyzed."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT DISTINCT brand FROM analyses WHERE status = 'completed' ORDER BY brand"
    ).fetchall()
    conn.close()
    return [r["brand"] for r in rows]
