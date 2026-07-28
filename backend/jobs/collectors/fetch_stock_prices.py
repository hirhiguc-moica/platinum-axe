"""株価データ取得スクリプト（全件取得）

J-Quants API から株価日次データ（四本値）を全件取得してDBに保存する。

コマンドライン引数:
    --start-date: 取得開始日（YYYY-MM-DD形式）
        デフォルト: 2016-07-28（J-Quants Standardプランの開始日）

    --end-date: 取得終了日（YYYY-MM-DD形式）
        デフォルト: 今日

    --test: テストモード（1週間のみ取得）
        デフォルト: False

    --resume: 進捗ファイルから再開
        デフォルト: False
        進捗ファイル（progress_stock_prices.json）の日付から再開

    --wait: 各週取得後の待機秒数
        デフォルト: 10秒
        rate limit: 120req/分（2req/秒）を考慮
        1秒まで短縮可能だが、rate limitに注意

使用例:
    # テストモード（1週間のみ取得）
    $ uv run python backend/jobs/collectors/fetch_stock_prices.py --test

    # 過去10年分取得（デフォルトwait=10秒で約2.5時間）
    $ uv run python backend/jobs/collectors/fetch_stock_prices.py

    # wait時間を短縮（2秒で約2時間、rate limit注意）
    $ uv run python backend/jobs/collectors/fetch_stock_prices.py --wait 2

    # 期間指定
    $ uv run python backend/jobs/collectors/fetch_stock_prices.py \
        --start-date 2024-01-01 --end-date 2024-12-31

    # 進捗から再開
    $ uv run python backend/jobs/collectors/fetch_stock_prices.py --resume

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - 週単位分割（7日ずつ）でrate limit対策
    - 各週取得後10秒待機（--waitで調整可能）
    - 進捗保存（JSON）でエラー時の再開対応
    - PostgreSQL UPSERT で高速保存（重複実行OK）

所要時間見積もり（全銘柄×10年分）:
    - wait=10秒: 約2.5時間（推奨）
    - wait=2秒:  約2時間（実績値）
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

from app.usecase.fetch_stock_prices_usecase import FetchStockPricesUseCase  # noqa: E402


def main() -> None:
    """コマンドライン引数を解析して株価データ取得を実行する。

    引数の詳細や使用例はモジュールdocstringを参照。
    """

    parser = argparse.ArgumentParser(description="株価データ取得スクリプト（全件取得）")
    parser.add_argument(
        "--start-date",
        type=str,
        default="2016-07-28",
        help="取得開始日（YYYY-MM-DD形式、デフォルト: 2016-07-28 ※Standardプランの開始日）",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="取得終了日（YYYY-MM-DD形式、デフォルト: 今日）",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモード（1週間のみ取得）",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="進捗ファイルから再開",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=10,
        help="各週取得後の待機秒数（デフォルト: 10秒、rate limit: 120req/分）",
    )

    args = parser.parse_args()

    # 日付パース
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    # テストモード
    if args.test:
        print("⚠️  テストモード: 1週間のみ取得")
        end_date = start_date + timedelta(days=6)

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
        usecase = FetchStockPricesUseCase(session)

        try:
            usecase.execute_full(
                start_date=start_date,
                end_date=end_date,
                wait_seconds=args.wait,
                resume=args.resume,
            )

            # 正常終了
            sys.exit(0)

        except KeyboardInterrupt:
            print("\n⚠️  ユーザーによる中断")
            sys.exit(1)

        except Exception as e:
            print(f"\n❌ エラー: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
