"""Scoring engine — compute AI Visibility Score (0-100)."""

from app.config import SCORE_WEIGHTS
from app.models.schemas import AIPerceptionProfile, GapItem


async def compute_score(
    perception: AIPerceptionProfile,
    gaps: list[GapItem],
    structured_data: dict | None = None,
) -> tuple[float, dict[str, float]]:
    """
    Compute AI Visibility Score (0-100) across 5 dimensions.

    Dimensions:
    - mention (20%): Is the brand clearly mentioned/identifiable
    - consistency (25%): Semantic consistency in AI perception
    - structure (20%): Structured data presence
    - authority (20%): External validation signals
    - clarity (15%): Value proposition clarity
    """
    scores = {
        "mention": _score_mention(perception),
        "consistency": _score_consistency(perception),
        "structure": _score_structure(structured_data),
        "authority": _score_authority(gaps),
        "clarity": _score_clarity(perception, gaps),
    }

    total = sum(scores[k] * SCORE_WEIGHTS[k] for k in scores)
    return round(total, 1), scores


def _score_mention(profile: AIPerceptionProfile) -> float:
    """Score based on whether brand is clearly identified."""
    detail_level = len(profile.summary) if profile.summary else 0
    if detail_level > 200:
        return 85 + min(15, _bonus(profile))
    elif detail_level > 100:
        return 60 + min(25, _bonus(profile))
    elif detail_level > 50:
        return 40
    return 20


def _score_consistency(profile: AIPerceptionProfile) -> float:
    """Score based on semantic consistency."""
    confusion = len(profile.confusion_areas)
    if confusion == 0:
        return 90
    elif confusion <= 2:
        return 70
    elif confusion <= 4:
        return 50
    return 30


def _score_structure(structured_data: dict | None) -> float:
    """Score based on structured data presence."""
    if not structured_data:
        return 10
    keys = set(structured_data.keys())
    important = {"@type", "name", "description", "url"}
    found = important & keys
    if len(found) >= 3:
        return 85
    elif len(found) >= 1:
        return 50
    return 20


def _score_authority(gaps: list[GapItem]) -> float:
    """Score based on authority gaps."""
    authority_gaps = [g for g in gaps if g.category == "authority"]
    critical = sum(1 for g in authority_gaps if g.severity == "critical")
    total = len(authority_gaps)
    if total == 0:
        return 80
    if critical > 0:
        return max(20, 80 - critical * 25)
    return max(30, 80 - total * 15)


def _score_clarity(profile: AIPerceptionProfile, gaps: list[GapItem]) -> float:
    """Score based on clarity of brand positioning."""
    clarity_gaps = [g for g in gaps if g.category == "clarity"]
    confusion = len(profile.confusion_areas)

    base = 80
    base -= confusion * 10
    base -= len(clarity_gaps) * 15
    return max(10, base)


def _bonus(profile: AIPerceptionProfile) -> float:
    """Small bonus for having well-defined attributes."""
    return len(profile.key_attributes) * 3 + len(profile.known_for) * 3
