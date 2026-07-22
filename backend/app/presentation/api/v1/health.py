"""Health Check API"""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    ヘルスチェックエンドポイント

    システムの稼働状況を確認します。
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "platinum-axe-backend",
    }
