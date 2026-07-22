"""ラウンド関連リポジトリ"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Round, RoundRecommendation


class RoundRepository:
    """ラウンドリポジトリ"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_all(self, limit: int = 50, offset: int = 0) -> list[Round]:
        """
        全ラウンド取得

        Args:
            limit: 取得件数
            offset: オフセット

        Returns:
            ラウンドリスト
        """
        stmt = (
            select(Round)
            .order_by(Round.start_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_id(self, round_id: str) -> Round | None:
        """
        ラウンドID検索

        Args:
            round_id: ラウンドID

        Returns:
            ラウンド（存在しない場合はNone）
        """
        stmt = select(Round).where(Round.round_id == round_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id_with_recommendations(self, round_id: str) -> Round | None:
        """
        ラウンドID検索（推奨銘柄付き）

        Args:
            round_id: ラウンドID

        Returns:
            ラウンド（推奨銘柄含む）
        """
        stmt = (
            select(Round)
            .where(Round.round_id == round_id)
            .options(selectinload(Round.recommendations))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class RoundRecommendationRepository:
    """ラウンド推奨銘柄リポジトリ"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_round_uuid(self, round_uuid: UUID) -> list[RoundRecommendation]:
        """
        ラウンドUUIDで推奨銘柄取得（銘柄情報付き）

        Args:
            round_uuid: ラウンドのUUID（主キー）

        Returns:
            推奨銘柄リスト（ランク順、銘柄情報含む）
        """
        stmt = (
            select(RoundRecommendation)
            .where(RoundRecommendation.round_id == round_uuid)
            .options(selectinload(RoundRecommendation.stock))
            .order_by(RoundRecommendation.rank)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
