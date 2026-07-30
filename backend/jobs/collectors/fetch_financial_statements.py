"""財務データ全量取得バッチ

J-Quants APIから財務サマリーデータ（決算短信・業績予想・配当予想）を全量取得してDBに保存する。

使用例:
    # テストモード（直近1ヶ月のみ取得）
    $ uv run python backend/jobs/collectors/fetch_financial_statements.py --test

    # 過去10年分全量取得（Standardプラン: 現在から10年前〜、wait=1秒で約1時間）
    $ uv run python backend/jobs/collectors/fetch_financial_statements.py

    # 期間指定取得
    $ uv run python backend/jobs/collectors/fetch_financial_statements.py \\
        --start-date 2024-01-01 --end-date 2024-12-31

    # 進捗から再開
    $ uv run python backend/jobs/collectors/fetch_financial_statements.py --resume
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
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

from app.usecase.fetch_financial_statements_usecase import FetchFinancialStatementsUseCase  # noqa: E402


def main():
    """財務データ全量取得バッチのエントリーポイント"""
    parser = argparse.ArgumentParser(description="財務データ全量取得バッチ")
    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモード（直近1ヶ月のみ取得）",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="取得開始日（YYYY-MM-DD形式、デフォルト: 現在から10年前 ※Standardプラン利用可能範囲）",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="取得終了日（YYYY-MM-DD形式、デフォルト: 今日）",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=1,
        help="各日取得後の待機秒数（デフォルト: 1秒、レート制限60件/分対策）",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="進捗ファイルから再開",
    )

    args = parser.parse_args()

    # テストモードの場合は直近1ヶ月のみ取得 + 待機時間0秒
    if args.test:
        print("🧪 テストモード: 直近1ヶ月のみ取得（待機時間: 0秒）")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        # テストモードでは待機しない（明示的に--waitを指定した場合を除く）
        if args.wait == 1:  # デフォルト値の場合のみ上書き
            args.wait = 0
    else:
        # 開始日・終了日の設定
        if args.start_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        else:
            # デフォルト: J-Quants Standardプラン（現在から10年前）
            ten_years_ago = datetime.now() - timedelta(days=365 * 10)
            start_date = ten_years_ago

        if args.end_date:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        else:
            # デフォルト: 今日
            end_date = datetime.now()

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
        result = usecase.execute_full(
            start_date=start_date,
            end_date=end_date,
            wait_seconds=args.wait,
            resume=args.resume,
        )

        print(f"\n✅ 全件取得完了: {result['total_saved']}件")
        print(f"⏱️  所要時間: {result['elapsed_seconds']:.1f}秒 ({result['elapsed_seconds'] / 60:.1f}分)")


if __name__ == "__main__":
    main()
