"""Analysis API endpoints."""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.models.schemas import (
    AnalyzeRequest, AnalysisResult, AnalysisStatus, HealthResponse, ScoreSnapshot,
)
from app.crawler import crawl_brand
from app.ai_engine import registry as engine_registry
from app.ai_engine import EngineInput
from app.scoring import compute_score
from app.storage import (
    init_db, save_pending, save_analysis, update_status,
    get_analysis, get_analysis_status, list_recent,
    get_latest_result, get_score_history, list_tracked_brands,
)
from app.config import AI_ENGINE

router = APIRouter()

LOCALE_TO_LANG = {"en": "English", "zh": "Chinese"}


# ── Shared analysis pipeline ─────────────────────────────

async def _run_analysis_pipeline(
    analysis_id: str, brand: str, url: str | None = None,
    locale: str = "en",
) -> AnalysisResult:
    """Execute the full analysis pipeline using the configured AI engine."""
    output_language = LOCALE_TO_LANG.get(locale, "English")

    update_status(analysis_id, "running", "Crawling website...")
    crawled = await crawl_brand(brand, url)

    update_status(analysis_id, "running", "Analyzing AI perception...")

    # ── Resolve which engine to use ──────────────────────────
    preferred = None if AI_ENGINE == "auto" else AI_ENGINE

    inp = EngineInput(
        brand=brand,
        url=crawled["url"],
        website_content=crawled["raw_text"],
        about_content=crawled.get("about_text", ""),
        structured_data=crawled.get("structured_data", {}),
        output_language=output_language,
        page_title=crawled.get("title", ""),
        meta_description=crawled.get("meta_description", ""),
        headings=crawled.get("headings", []),
    )

    engine_result = await engine_registry.analyze(inp, preferred=preferred)

    # ── Compute score ─────────────────────────────────────────

    # For dual-model engine, use the cross-model comparison score
    if engine_result.engine_name == "dual" and engine_result.source_raw:
        try:
            raw_data = json.loads(engine_result.source_raw)
            doubao_score = raw_data.get("doubao_overall")
            deepseek_score = raw_data.get("deepseek_overall")
            # Derive score from available model evaluations
            scores = [s for s in [doubao_score, deepseek_score] if s is not None]
            if scores:
                score = round(sum(scores) / len(scores), 1)
                score_breakdown = {
                    "doubao": doubao_score or 0,
                    "deepseek": deepseek_score or 0,
                    "combined": score,
                }
            else:
                score, score_breakdown = await compute_score(
                    engine_result.perception, engine_result.gaps,
                    crawled.get("structured_data"),
                )
        except (json.JSONDecodeError, TypeError, KeyError):
            score, score_breakdown = await compute_score(
                engine_result.perception, engine_result.gaps,
                crawled.get("structured_data"),
            )
    else:
        score, score_breakdown = await compute_score(
            engine_result.perception, engine_result.gaps,
            crawled.get("structured_data"),
        )

    # ── Parse model data for frontend ──────────────────────────
    model_data = None
    doubao_score = None
    deepseek_score = None
    if engine_result.source_raw:
        try:
            raw = json.loads(engine_result.source_raw)
            if raw.get("engine") == "dual_model":
                doubao_score = raw.get("doubao_overall")
                deepseek_score = raw.get("deepseek_overall")
                model_data = raw
        except (json.JSONDecodeError, TypeError):
            pass

    return AnalysisResult(
        id=analysis_id,
        brand=brand,
        locale=locale,
        engine=engine_result.engine_name,
        score=score,
        score_breakdown=score_breakdown,
        perception_profile=engine_result.perception,
        gap_map=engine_result.gaps,
        suggestions=engine_result.suggestions,
        roadmap=engine_result.roadmap,
        created_at=datetime.now(timezone.utc),
        doubao_score=doubao_score,
        deepseek_score=deepseek_score,
        model_data=model_data,
    )


# ── Health ───────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


# ── Analyze ──────────────────────────────────────────────

@router.post("/analyze", response_model=AnalysisStatus)
async def start_analysis(req: AnalyzeRequest):
    """Start a brand analysis (runs in background)."""
    analysis_id = str(uuid.uuid4())[:8]
    save_pending(analysis_id, req.brand)

    # Run pipeline in background so POST returns immediately
    import asyncio
    asyncio.create_task(_run_and_save(analysis_id, req.brand, req.url, req.locale))

    return AnalysisStatus(
        id=analysis_id, brand=req.brand, status="pending",
        locale=req.locale,
        created_at=datetime.now(timezone.utc),
    )


async def _run_and_save(analysis_id: str, brand: str, url: str | None = None,
                        locale: str = "en") -> None:
    """Run analysis pipeline and save result (for background tasks)."""
    try:
        result = await _run_analysis_pipeline(analysis_id, brand, url, locale=locale)
        save_analysis(result)
    except HTTPException:
        raise
    except Exception as e:
        update_status(analysis_id, "failed", str(e))


# ── Re-analyze (Monitor loop) ───────────────────────────

@router.post("/analyze/{analysis_id}/reanalyze", response_model=AnalysisStatus)
async def reanalyze_brand(analysis_id: str, locale: str = "en"):
    """Re-analyze a previously analyzed brand (creates a new analysis)."""
    # Get original analysis to find brand
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

    import asyncio
    asyncio.create_task(_run_and_save(new_id, brand, locale=locale))

    return AnalysisStatus(
        id=new_id, brand=brand, status="pending",
        locale=locale,
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


# ── Recent analyses ─────────────────────────────────────

@router.get("/analyses/recent", response_model=list[AnalysisStatus])
async def recent_analyses(limit: int = 10):
    """List recent analyses."""
    return list_recent(limit)


# ── Tracked brands ─────────────────────────────────────

@router.get("/brands", response_model=list[str])
async def tracked_brands():
    """List all tracked brands."""
    return list_tracked_brands()
