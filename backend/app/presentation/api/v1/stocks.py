"""銘柄詳細API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.presentation.schemas.stock import (
    RecommendationHistoryResponse,
    StockDetailResponse,
    StockPriceHistoryResponse,
    StockSearchResponse,
    TechnicalIndicatorResponse,
)
from app.usecase.stock_detail import GetStockDetailUseCase
from app.usecase.stock_price_history import GetStockPriceHistoryUseCase
from app.usecase.stock_recommendation_history import GetStockRecommendationHistoryUseCase
from app.usecase.stock_search import SearchStocksUseCase
from app.usecase.stock_technical_indicators import GetStockTechnicalIndicatorsUseCase
from app.usecase.stock_technical_indicators_full import GetStockTechnicalIndicatorsFullUseCase

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search", response_model=StockSearchResponse)
async def search_stocks(
    q: str = Query(..., min_length=1, description="検索キーワード（銘柄コードまたは会社名）"),
    limit: int = Query(10, ge=1, le=50, description="取得件数（デフォルト: 10、最大: 50）"),
    db: AsyncSession = Depends(get_db),
):
    """銘柄検索

    銘柄コードまたは会社名の部分一致検索を行います。

    Args:
        q: 検索キーワード（銘柄コードまたは会社名の一部）
        limit: 取得件数（デフォルト: 10、最大: 50）

    Returns:
        検索結果リスト
    """
    usecase = SearchStocksUseCase(db)
    stocks = await usecase.execute(query=q, limit=limit)

    return {"stocks": stocks}


@router.get("/{stock_code}", response_model=StockDetailResponse)
async def get_stock_detail(
    stock_code: str,
    db: AsyncSession = Depends(get_db),
):
    """銘柄詳細取得

    銘柄基本情報 + 最新株価を取得します。

    Args:
        stock_code: 銘柄コード（例: 7203）

    Returns:
        銘柄詳細情報
    """
    usecase = GetStockDetailUseCase(db)
    result = await usecase.execute(stock_code)

    if not result:
        raise HTTPException(status_code=404, detail="Stock not found")

    return result


@router.get("/{stock_code}/prices", response_model=StockPriceHistoryResponse)
async def get_stock_price_history(
    stock_code: str,
    page: int = Query(1, ge=1, description="ページ番号（1始まり）"),
    limit: int = Query(200, ge=1, le=500, description="1ページあたりの件数"),
    db: AsyncSession = Depends(get_db),
):
    """株価履歴取得

    指定銘柄の株価履歴をページング形式で取得します。

    Args:
        stock_code: 銘柄コード
        page: ページ番号（デフォルト: 1）
        limit: 1ページあたりの件数（デフォルト: 200、最大: 500）

    Returns:
        株価履歴データ（ページング情報付き）
    """
    usecase = GetStockPriceHistoryUseCase(db)
    result = await usecase.execute(stock_code, page, limit)
    return result


@router.get("/{stock_code}/technical-indicators", response_model=TechnicalIndicatorResponse)
async def get_stock_technical_indicators(
    stock_code: str,
    page: int = Query(1, ge=1, description="ページ番号（1始まり）"),
    limit: int = Query(200, ge=1, le=500, description="1ページあたりの件数"),
    db: AsyncSession = Depends(get_db),
):
    """テクニカル指標履歴取得

    指定銘柄のテクニカル指標履歴をページング形式で取得します。

    主要指標のみを返します（MA, RSI, MACD, Bollinger Bands等）。

    Args:
        stock_code: 銘柄コード
        page: ページ番号（デフォルト: 1）
        limit: 1ページあたりの件数（デフォルト: 200、最大: 500）

    Returns:
        テクニカル指標履歴データ（ページング情報付き）
    """
    usecase = GetStockTechnicalIndicatorsUseCase(db)
    result = await usecase.execute(stock_code, page, limit)
    return result


@router.get("/{stock_code}/technical-indicators/full")
async def get_stock_technical_indicators_full(
    stock_code: str,
    page: int = Query(1, ge=1, description="ページ番号（1始まり）"),
    limit: int = Query(200, ge=1, le=500, description="1ページあたりの件数"),
    db: AsyncSession = Depends(get_db),
):
    """テクニカル指標完全履歴取得（全125指標）

    指定銘柄のテクニカル指標履歴をページング形式で取得します。

    全125個のテクニカル指標を返します。
    チャート描画や詳細分析に使用できます。

    Args:
        stock_code: 銘柄コード
        page: ページ番号（デフォルト: 1）
        limit: 1ページあたりの件数（デフォルト: 200、最大: 500）

    Returns:
        テクニカル指標完全履歴データ（ページング情報付き、全125指標）
    """
    usecase = GetStockTechnicalIndicatorsFullUseCase(db)
    result = await usecase.execute(stock_code, page, limit)
    return result


@router.get("/{stock_code}/recommendations", response_model=RecommendationHistoryResponse)
async def get_stock_recommendation_history(
    stock_code: str,
    page: int = Query(1, ge=1, description="ページ番号（1始まり）"),
    limit: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),
    db: AsyncSession = Depends(get_db),
):
    """推奨履歴取得

    指定銘柄の過去の推奨履歴をページング形式で取得します。

    Args:
        stock_code: 銘柄コード
        page: ページ番号（デフォルト: 1）
        limit: 1ページあたりの件数（デフォルト: 20、最大: 100）

    Returns:
        推奨履歴データ（ページング情報付き）
    """
    usecase = GetStockRecommendationHistoryUseCase(db)
    result = await usecase.execute(stock_code, page, limit)
    return result
