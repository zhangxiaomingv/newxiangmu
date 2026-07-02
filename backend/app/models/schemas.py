"""Pydantic schemas for request/response models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Requests ──────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    brand: str = Field(..., description="Brand name or URL")
    url: Optional[str] = Field(None, description="Optional direct URL")


# ── Responses ─────────────────────────────────────────────

class AnalysisStatus(BaseModel):
    id: str
    status: str  # pending | running | completed | failed
    brand: str
    created_at: datetime
    progress: Optional[str] = None


class AIPerceptionProfile(BaseModel):
    summary: str = Field(..., description="How AI perceives this brand")
    key_attributes: list[str] = Field(..., description="Key attributes AI associates")
    known_for: list[str] = Field(..., description="What the brand is known for")
    confusion_areas: list[str] = Field(..., description="Areas of ambiguity/confusion")
    competitor_context: str = Field(..., description="Where brand sits in competitive landscape")


class GapItem(BaseModel):
    category: str  # structure | content | authority | clarity
    severity: str  # critical | moderate | minor
    description: str
    evidence: str = ""


class ActionItem(BaseModel):
    priority: str  # immediate | medium_term
    title: str
    description: str
    effort: str  # low | medium | high
    impact: str  # low | medium | high


class RoadmapStage(BaseModel):
    stage: int
    title: str
    description: str
    actions: list[str]


class AnalysisResult(BaseModel):
    id: str
    brand: str
    status: str = "completed"
    score: float = Field(..., ge=0, le=100, description="AI Visibility Score")
    score_breakdown: dict[str, float]
    perception_profile: AIPerceptionProfile
    gap_map: list[GapItem]
    suggestions: list[ActionItem]
    roadmap: list[RoadmapStage]
    created_at: datetime


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class ScoreSnapshot(BaseModel):
    score: float
    score_breakdown: dict[str, float]
    created_at: datetime
