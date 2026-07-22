from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.shared.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """アプリケーションライフサイクル管理"""
    # Startup: データベース接続プール初期化など
    print("Starting up...")

    yield

    # Shutdown: リソースクリーンアップ
    print("Shutting down...")


def create_app() -> FastAPI:
    """FastAPIアプリケーションファクトリ"""

    # 本番環境ではドキュメントを無効化
    docs_url = None if settings.is_production else "/docs"
    redoc_url = None if settings.is_production else "/redoc"

    app = FastAPI(
        title="Platinum Axe API",
        description="株式投資推奨システム - Backend API",
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan,
    )

    # CORS設定（開発環境のみ）
    if settings.is_development:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

    # ルーター登録
    from app.presentation.api.v1 import health, rounds

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(rounds.router, prefix="/api/v1", tags=["rounds"])

    @app.get("/")
    async def root() -> dict[str, str]:
        """ルートエンドポイント"""
        return {"message": "Platinum Axe API", "environment": settings.ENVIRONMENT}

    return app


app = create_app()
