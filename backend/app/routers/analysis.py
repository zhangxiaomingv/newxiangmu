"""Analysis API endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import AnalyzeRequest, AnalysisResult, AnalysisStatus, HealthResponse
from app.crawler import crawl_brand
from app.ai_engine import analyze_perception, detect_gaps, generate_optimizations
from app.scoring import compute_score
from app.storage import (
    init_db, save_pending, save_analysis, update_status,
    get_analysis, get_analysis_status, list_recent,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


@router.post("/analyze", response_model=AnalysisStatus)
async def start_analysis(req: AnalyzeRequest):
    """Start a brand analysis (async — returns immediately)."""
    analysis_id = str(uuid.uuid4())[:8]
    save_pending(analysis_id, req.brand)

    # Run analysis synchronously for v0.1 simplicity
    # In production, this would be a background task
    update_status(analysis_id, "running", "Crawling website...")
    try:
        # Step 1: Crawl
        crawled = await crawl_brand(req.brand, req.url)
        update_status(analysis_id, "running", "Analyzing AI perception...")

        # Step 2: AI Perception Analysis
        perception = await analyze_perception(
            brand=req.brand,
            url=crawled["url"],
            website_content=crawled["raw_text"],
            about_content=crawled.get("about_text", ""),
            structured_data=crawled.get("structured_data", {}),
        )

        update_status(analysis_id, "running", "Detecting gaps...")

        # Step 3: Gap Detection
        gaps = await detect_gaps(
            brand=req.brand,
            url=crawled["url"],
            perception=perception,
            website_content=crawled["raw_text"],
        )

        update_status(analysis_id, "running", "Generating recommendations...")

        # Step 4: Scoring
        score, score_breakdown = await compute_score(perception, gaps, crawled.get("structured_data"))

        # Step 5: Optimizations
        suggestions, roadmap = await generate_optimizations(req.brand, perception, gaps)

        # Step 6: Save result
        result = AnalysisResult(
            id=analysis_id,
            brand=req.brand,
            score=score,
            score_breakdown=score_breakdown,
            perception_profile=perception,
            gap_map=gaps,
            suggestions=suggestions,
            roadmap=roadmap,
            created_at=datetime.now(timezone.utc),
        )
        save_analysis(result)

    except HTTPException:
        raise
    except Exception as e:
        update_status(analysis_id, "failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

    return AnalysisStatus(
        id=analysis_id,
        brand=req.brand,
        status="completed",
        created_at=datetime.now(timezone.utc),
    )


@router.get("/analysis/{analysis_id}", response_model=AnalysisResult | AnalysisStatus)
async def get_analysis_result(analysis_id: str):
    """Get analysis result or status."""
    # Try full result first
    result = get_analysis(analysis_id)
    if result:
        return result

    # Fall back to status
    status = get_analysis_status(analysis_id)
    if status:
        return status

    raise HTTPException(status_code=404, detail="Analysis not found")


@router.get("/analyses/recent", response_model=list[AnalysisStatus])
async def recent_analyses(limit: int = 10):
    """List recent analyses."""
    return list_recent(limit)
