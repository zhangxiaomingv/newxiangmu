"""Analysis API endpoints."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import (
    AnalyzeRequest, AnalysisResult, AnalysisStatus, HealthResponse, ScoreSnapshot,
)
from app.crawler import crawl_brand
from app.ai_engine import analyze_perception, detect_gaps, generate_optimizations
from app.scoring import compute_score
from app.storage import (
    init_db, save_pending, save_analysis, update_status,
    get_analysis, get_analysis_status, list_recent,
    get_latest_result, get_score_history, list_tracked_brands,
)

router = APIRouter()


# ── Shared analysis pipeline ─────────────────────────────

async def _run_analysis_pipeline(analysis_id: str, brand: str, url: str | None = None) -> AnalysisResult:
    """Execute the full analysis pipeline (crawl → perceive → gap → score → optimize)."""
    update_status(analysis_id, "running", "Crawling website...")
    crawled = await crawl_brand(brand, url)

    update_status(analysis_id, "running", "Analyzing AI perception...")
    perception = await analyze_perception(
        brand=brand,
        url=crawled["url"],
        website_content=crawled["raw_text"],
        about_content=crawled.get("about_text", ""),
        structured_data=crawled.get("structured_data", {}),
    )

    update_status(analysis_id, "running", "Detecting gaps...")
    gaps = await detect_gaps(
        brand=brand,
        url=crawled["url"],
        perception=perception,
        website_content=crawled["raw_text"],
    )

    update_status(analysis_id, "running", "Generating recommendations...")
    score, score_breakdown = await compute_score(perception, gaps, crawled.get("structured_data"))

    suggestions, roadmap = await generate_optimizations(brand, perception, gaps)

    return AnalysisResult(
        id=analysis_id,
        brand=brand,
        score=score,
        score_breakdown=score_breakdown,
        perception_profile=perception,
        gap_map=gaps,
        suggestions=suggestions,
        roadmap=roadmap,
        created_at=datetime.now(timezone.utc),
    )


# ── Health ───────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


# ── Analyze ──────────────────────────────────────────────

@router.post("/analyze", response_model=AnalysisStatus)
async def start_analysis(req: AnalyzeRequest):
    """Start a brand analysis."""
    analysis_id = str(uuid.uuid4())[:8]
    save_pending(analysis_id, req.brand)

    try:
        result = await _run_analysis_pipeline(analysis_id, req.brand, req.url)
        save_analysis(result)
    except HTTPException:
        raise
    except Exception as e:
        update_status(analysis_id, "failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

    return AnalysisStatus(
        id=analysis_id, brand=req.brand, status="completed",
        created_at=datetime.now(timezone.utc),
    )


# ── Re-analyze (Monitor loop) ───────────────────────────

@router.post("/analyze/{analysis_id}/reanalyze", response_model=AnalysisStatus)
async def reanalyze_brand(analysis_id: str):
    """Re-analyze a previously analyzed brand (creates a new analysis)."""
    # First, get the original to find the brand
    original = get_analysis(analysis_id)
    if not original:
        original_status = get_analysis_status(analysis_id)
        if not original_status:
            raise HTTPException(status_code=404, detail="Original analysis not found")
        brand = original_status.brand
    else:
        brand = original.brand

    new_id = str(uuid.uuid4())[:8]
    save_pending(new_id, brand)

    try:
        result = await _run_analysis_pipeline(new_id, brand)
        save_analysis(result)
    except HTTPException:
        raise
    except Exception as e:
        update_status(new_id, "failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

    return AnalysisStatus(
        id=new_id, brand=brand, status="completed",
        created_at=datetime.now(timezone.utc),
    )


# ── Get result ──────────────────────────────────────────

@router.get("/analysis/{analysis_id}", response_model=AnalysisResult | AnalysisStatus)
async def get_analysis_result(analysis_id: str):
    """Get analysis result or status."""
    result = get_analysis(analysis_id)
    if result:
        return result
    status = get_analysis_status(analysis_id)
    if status:
        return status
    raise HTTPException(status_code=404, detail="Analysis not found")


# ── Score history (timeline data) ────────────────────────

@router.get("/analysis/{analysis_id}/history", response_model=list[ScoreSnapshot])
async def get_analysis_history(analysis_id: str):
    """Get score history for the brand associated with an analysis."""
    original = get_analysis(analysis_id)
    if not original:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return get_score_history(original.brand, limit=30)


# ── Recent analyses ──────────────────────────────────────

@router.get("/analyses/recent", response_model=list[AnalysisStatus])
async def recent_analyses(limit: int = 10):
    """List recent analyses."""
    return list_recent(limit)


# ── Tracked brands ──────────────────────────────────────

@router.get("/brands", response_model=list[str])
async def tracked_brands():
    """List all tracked brands."""
    return list_tracked_brands()
