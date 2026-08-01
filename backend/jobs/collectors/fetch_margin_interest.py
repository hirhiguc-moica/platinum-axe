"""信用取引週末残高データ取得スクリプト（全件取得）

J-Quants API から信用取引週末残高データ（全銘柄）を全件取得してDBに保存する。

コマンドライン引数:
    --start-date: 取得開始日（YYYY-MM-DD形式）
        デフォルト: 実行日から10年前（J-Quants Standardプランの取得可能期間）

    --end-date: 取得終了日（YYYY-MM-DD形式）
        デフォルト: 今日

    --test: テストモード（1ヶ月のみ取得）
        デフォルト: False

    --wait: 各週取得後の待機秒数
        デフォルト: 1秒
        rate limit: 60req/分（1req/秒）を考慮

使用例:
    # テストモード（1ヶ月のみ取得）
    $ uv run python backend/jobs/collectors/fetch_margin_interest.py --test

    # 過去10年分取得（デフォルトwait=1秒で約10分）
    $ uv run python backend/jobs/collectors/fetch_margin_interest.py

    # wait時間なし（約5分、rate limit注意）
    $ uv run python backend/jobs/collectors/fetch_margin_interest.py --wait 0

    # 期間指定
    $ uv run python backend/jobs/collectors/fetch_margin_interest.py \
        --start-date 2024-01-01 --end-date 2024-12-31

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - 日単位で取得（APIの仕様上、全銘柄取得はdateパラメータのみ対応）
    - 週末（金曜日）のみデータが存在（他の日はデータなし）
    - 各日取得後1秒待機（--waitで調整可能）
    - PostgreSQL UPSERT で高速保存（重複実行OK）
    - 進捗保存なし（エラー時は最初から再実行）

所要時間見積もり（過去10年=約3650日、うち週末データ約520日）:
    - wait=1秒: 約3650秒（約1時間、推奨）
    - wait=0秒: 約30分（rate limit注意）
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

from app.usecase.fetch_margin_interest_usecase import FetchMarginInterestUseCase  # noqa: E402


def main() -> None:
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="信用取引週末残高データ取得（全件取得モード）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="取得開始日（YYYY-MM-DD形式）。デフォルト: 実行日から10年前",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="取得終了日（YYYY-MM-DD形式）。デフォルト: 今日",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモード（1ヶ月のみ取得）",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=1.0,
        help="各週取得後の待機秒数（デフォルト: 1秒）",
    )

    args = parser.parse_args()

    # 開始日・終了日の決定
    if args.test:
        # テストモード: 直近1ヶ月
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        print("🧪 テストモード: 直近1ヶ月のみ取得")
    else:
        # 開始日
        if args.start_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        else:
            # デフォルト: 10年前
            start_date = datetime.now() - timedelta(days=365 * 10)

        # 終了日
        if args.end_date:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        else:
            end_date = datetime.now()

    # データベース接続
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is not set in .env file")

    # 非同期版のURL（+asyncpg）を同期版に変換
    database_url = database_url.replace("+asyncpg", "")

    engine = create_engine(database_url)

    # UseCase実行
    with Session(engine) as session:
        usecase = FetchMarginInterestUseCase(session)

        result = usecase.execute_full(
            start_date=start_date,
            end_date=end_date,
            wait_seconds=args.wait,
        )

    # 終了
    print("\n✅ 全件取得完了!")
    print(f"📊 取得週数: {result['total_weeks']}週")
    print(f"📊 保存件数: {result['total_saved']:,}件")
    print(f"⏱️  所要時間: {result['elapsed_seconds']:.1f}秒")


if __name__ == "__main__":
    main()
