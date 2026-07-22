"""ラウンド履歴API"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.usecase.history import (
    GetLatestRoundResultsUseCase,
    GetOverallPerformanceUseCase,
    GetRoundDetailWithResultsUseCase,
    GetRoundHistoryUseCase,
)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/latest")
async def get_latest_results(
    index_filter: Literal["all", "nikkei225", "topix"] = Query(
        "all", description="指数フィルター"
    ),
    db: AsyncSession = Depends(get_db),
):
    """直近のラウンド結果を取得（BUY/SELL）

    Args:
        index_filter: all（全銘柄） | nikkei225（日経225のみ） | topix（TOPIXのみ）
        db: DBセッション

    Returns:
        直近のBUY/SELLラウンド結果
    """
    usecase = GetLatestRoundResultsUseCase()
    result = await usecase.execute(db, index_filter)
    return result


@router.get("/summary")
async def get_performance_summary(
    index_filter: Literal["all", "nikkei225", "topix"] = Query(
        "all", description="指数フィルター"
    ),
    db: AsyncSession = Depends(get_db),
):
    """全体のパフォーマンスサマリーを取得

    Args:
        index_filter: all（全銘柄） | nikkei225（日経225のみ） | topix（TOPIXのみ）
        db: DBセッション

    Returns:
        BUY/SELLの全体パフォーマンス統計
    """
    usecase = GetOverallPerformanceUseCase()
    result = await usecase.execute(db, index_filter)
    return result


@router.get("")
async def get_round_history(
    round_type: Literal["BUY", "SELL"] | None = Query(
        None, description="ラウンドタイプ（未指定で全て）"
    ),
    index_filter: Literal["all", "nikkei225", "topix"] = Query(
        "all", description="指数フィルター"
    ),
    page: int = Query(1, ge=1, description="ページ番号（1始まり）"),
    limit: int = Query(10, ge=1, le=100, description="1ページあたりの件数"),
    db: AsyncSession = Depends(get_db),
):
    """ラウンド履歴を取得（ページネーション付き）

    Args:
        round_type: BUY | SELL | None（全て）
        index_filter: all（全銘柄） | nikkei225（日経225のみ） | topix（TOPIXのみ）
        page: ページ番号（1始まり）
        limit: 1ページあたりの件数（1-100）
        db: DBセッション

    Returns:
        ラウンド履歴とページネーション情報
    """
    usecase = GetRoundHistoryUseCase()
    result = await usecase.execute(db, round_type, index_filter, page, limit)
    return result


@router.get("/{round_id}")
async def get_round_detail(
    round_id: str,
    db: AsyncSession = Depends(get_db),
):
    """特定ラウンドの詳細を取得（推奨銘柄 + 結果データ付き）

    Args:
        round_id: ラウンドID（例: 2026-W29-BUY）
        db: DBセッション

    Returns:
        ラウンド詳細 + 推奨銘柄 + 結果データ

    Raises:
        HTTPException: ラウンドが見つからない場合（404）
    """
    usecase = GetRoundDetailWithResultsUseCase()
    result = await usecase.execute(db, round_id)

    if result is None:
        raise HTTPException(status_code=404, detail=f"Round not found: {round_id}")

    return result
