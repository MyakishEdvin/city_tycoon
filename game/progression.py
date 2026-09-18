"""
Player progression: XP thresholds and level-up math.

Pure functions only (no DB access) — ProgressionService in
database/models/progression_service.py is the stateful counterpart that
actually mutates a User. Keeping the curve here means tuning progression
later is a one-line change here, not a hunt through every XP source.
"""

from __future__ import annotations

# XP required to advance from `level` to `level + 1`. Linear growth is
# intentionally simple for the first pass — buildings/quests (later
# phases) are what should drive interesting pacing, not the curve itself.
BASE_XP_PER_LEVEL = 100
XP_GROWTH_PER_LEVEL = 50


def xp_required_for_level(level: int) -> int:
    """XP needed to advance from `level` to `level + 1`."""
    if level < 1:
        raise ValueError("level must be >= 1")
    return BASE_XP_PER_LEVEL + (level - 1) * XP_GROWTH_PER_LEVEL


def level_progress_fraction(level: int, xp: int) -> float:
    """Fraction (0.0-1.0) of the way through the current level's XP bar."""
    required = xp_required_for_level(level)
    if required <= 0:
        return 0.0
    return max(0.0, min(1.0, xp / required))