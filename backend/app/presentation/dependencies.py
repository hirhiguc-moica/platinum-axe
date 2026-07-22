"""API依存性注入"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.repositories.round_repository import (
    RoundRecommendationRepository,
    RoundRepository,
)


async def get_round_repository(
    session: AsyncSession = Depends(get_db),
) -> RoundRepository:
    """
    RoundRepository取得

    Args:
        session: データベースセッション

    Returns:
        RoundRepository
    """
    return RoundRepository(session)


async def get_round_recommendation_repository(
    session: AsyncSession = Depends(get_db),
) -> RoundRecommendationRepository:
    """
    RoundRecommendationRepository取得

    Args:
        session: データベースセッション

    Returns:
        RoundRecommendationRepository
    """
    return RoundRecommendationRepository(session)
