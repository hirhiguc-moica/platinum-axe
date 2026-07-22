"""Alembicマイグレーション履歴をクリーンアップ"""

import asyncio

from sqlalchemy import text

from app.infrastructure.database import engine


async def clean_alembic():
    """alembic_versionテーブルを確実に削除"""
    async with engine.begin() as conn:
        # alembic_versionテーブルの内容を確認
        try:
            result = await conn.execute(text("SELECT * FROM alembic_version"))
            rows = result.fetchall()
            print(f"📋 Current alembic_version: {rows}")
        except Exception as e:
            print(f"⚠️ alembic_version table doesn't exist or error: {e}")

        # alembic_versionテーブルを削除
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        print("✅ alembic_version table dropped")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(clean_alembic())
