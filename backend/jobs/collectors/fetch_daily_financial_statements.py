"""財務データ差分取得バッチ（日次ジョブ）

DBの最新開示日から現在までの差分データを取得してDBに保存する。

使用例:
    # 差分取得（DBの最新日から自動取得）
    $ uv run python backend/jobs/collectors/fetch_daily_financial_statements.py

実行タイミング:
    - 手動実行: 上記コマンド
    - 自動実行: GCP Cloud Scheduler（毎営業日17:30、株価データ取得後）

所要時間:
    - 通常（1日分）: 約5-10秒
    - バックフィル（複数日）: 日数に応じて増加（月単位分割で自動対応）

注意:
    - このスクリプトは冪等性あり（何度実行しても同じ結果）
    - DBに既存データがある場合はUPSERTされる
    - バッチ停止期間の補完（バックフィル）も自動で行われる
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# SQLAlchemyのログを完全に抑制
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# .envファイルを読み込み
env_path = project_root / ".env"
load_dotenv(env_path)

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.usecase.fetch_financial_statements_usecase import (  # noqa: E402
    FetchFinancialStatementsUseCase,  # noqa: E402
)


def main():
    """財務データ差分取得バッチのエントリーポイント"""
    print("=" * 80)
    print("📅 財務データ差分取得バッチ")
    print("=" * 80)

    # DB接続
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URLが設定されていません")
        sys.exit(1)

    # 非同期版のURL（+asyncpg）を同期版に変換
    database_url = database_url.replace("+asyncpg", "")

    # SQLログを完全に抑制
    engine = create_engine(database_url, echo=False)

    # UseCase実行
    with Session(engine) as session:
        usecase = FetchFinancialStatementsUseCase(session)
        result = usecase.execute_incremental(wait_seconds=2)

        if result["total_saved"] > 0:
            print(f"\n✅ 差分取得完了: {result['total_saved']}件")
            print(f"📅 取得期間: {result['start_date']} 〜 {result['end_date']}")
            print(f"⏱️  所要時間: {result['elapsed_seconds']:.1f}秒")
        else:
            print("\n✅ 差分なし（最新です）")


if __name__ == "__main__":
    main()
