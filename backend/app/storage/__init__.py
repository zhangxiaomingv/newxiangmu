"""SQLite-based storage for analysis results (v0.1)."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import DATA_DIR
from app.models.schemas import AnalysisResult, AnalysisStatus

DB_PATH = DATA_DIR / "zkoner.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
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
        CREATE INDEX IF NOT EXISTS idx_analyses_brand ON analyses(brand)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status)
    """)
    conn.commit()
    conn.close()


def save_analysis(analysis: AnalysisResult):
    """Save completed analysis result."""
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
