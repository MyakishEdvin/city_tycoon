"""
Mini App API routes.

Every endpoint resolves the caller's identity exclusively from validated
Telegram initData (get_current_telegram_user) — never from a path param,
query param, or request body. All reads/writes go through the existing
UserService / CityService / TransactionService; this router adds no new
economy logic, it only exposes what already exists to the frontend.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import TelegramWebAppUser, get_current_telegram_user
from backend.deps import get_db_session
from backend.schemas import (
    CityOut,
    LanguageUpdateRequest,
    MeResponse,
    TransactionHistoryResponse,
    TransactionOut,
)
from database.models.building_service import BuildingService
from database.models.city_service import CityService
from database.models.transaction_service import TransactionService
from database.models.user import User
from database.models.user_service import UserService
from game.localization import SUPPORTED_LANGUAGES
from game.progression import level_progress_fraction, xp_required_for_level

router = APIRouter(prefix="/api", tags=["mini-app"])


async def _resolve_user(tg_user: TelegramWebAppUser, session: AsyncSession) -> User:
    """
    Every request re-resolves (and, for a first-time caller, registers)
    the user from the validated Telegram identity — the same
    UserService.get_or_create path the bot's /start uses, so there is
    exactly one registration/economy system regardless of entry point.
    """
    service = UserService(session)
    user, _ = await service.get_or_create(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        language_code=tg_user.language_code,
    )
    await service.touch_activity(user)
    return user


async def _build_me_response(user: User, session: AsyncSession) -> MeResponse:
    city = await CityService(session).get_by_user_id(user.id)
    building_count = 0
    if city is not None:
        buildings = await BuildingService(session).get_buildings(city.id)
        building_count = len(buildings)
    return MeResponse(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        level=user.level,
        xp=user.xp,
        xp_for_next_level=xp_required_for_level(user.level),
        level_progress=level_progress_fraction(user.level, user.xp),
        money=user.money,
        reputation=user.reputation,
        energy=user.energy,
        daily_streak=user.daily_streak,
        language=user.language,
        referral_code=user.referral_code,
        city=CityOut(
        unlocked_districts=city.unlocked_districts if city else [],
        population=city.population if city else 0,
        building_count=building_count,
        ),
    )


@router.get("/me", response_model=MeResponse)
async def get_me(
    tg_user: TelegramWebAppUser = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_db_session),
) -> MeResponse:
    user = await _resolve_user(tg_user, session)
    return await _build_me_response(user, session)


@router.get("/transactions", response_model=TransactionHistoryResponse)
async def get_transactions(
    limit: int = 20,
    offset: int = 0,
    tg_user: TelegramWebAppUser = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_db_session),
) -> TransactionHistoryResponse:
    limit = max(1, min(limit, 50))
    offset = max(0, offset)

    user = await _resolve_user(tg_user, session)
    transactions = await TransactionService(session).get_history(
        user.id, limit=limit, offset=offset
    )
    return TransactionHistoryResponse(
        items=[TransactionOut.model_validate(tx) for tx in transactions],
        limit=limit,
        offset=offset,
    )


@router.patch("/me/language", response_model=MeResponse)
async def update_language(
    payload: LanguageUpdateRequest,
    tg_user: TelegramWebAppUser = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_db_session),
) -> MeResponse:
    if payload.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported language. Allowed: {sorted(SUPPORTED_LANGUAGES)}",
        )

    user = await _resolve_user(tg_user, session)
    user = await UserService(session).set_language(user, payload.language)
    return await _build_me_response(user, session)