"""データベースを完全にリセットするスクリプト"""

import asyncio

from sqlalchemy import text

from app.domain.models import Base
from app.infrastructure.database import engine


async def reset_db():
    """全テーブルとマイグレーション履歴を削除"""
    async with engine.begin() as conn:
        # 全テーブル削除
        await conn.run_sync(Base.metadata.drop_all)
        print("✅ All tables dropped")

        # alembic_version テーブル削除
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        print("✅ alembic_version table dropped")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_db())
