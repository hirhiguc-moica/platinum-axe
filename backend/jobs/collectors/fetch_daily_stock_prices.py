"""株価データ取得スクリプト（差分取得）

J-Quants API から株価日次データの差分を取得してDBに保存する。
DBの最新日付から現在までの差分のみを取得（冪等性担保）。

使用例:
    # 通常実行（DBの最新日付 + 1日 〜 今日）
    $ uv run python backend/jobs/collectors/fetch_daily_stock_prices.py

    # wait時間を調整（デフォルト: 2秒）
    $ uv run python backend/jobs/collectors/fetch_daily_stock_prices.py --wait 5

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - DBの最新日付を自動取得（冪等性担保）
    - progress.json不要（短時間で完了）
    - pod再配置時も安全（DB状態ベース）
    - 週単位分割でrate limit対策

所要時間見積もり:
    - 1日分: 約5-10分
    - 7日分（1週間バックフィル）: 約10-15分

GCP Cloud Scheduler設定例:
    - 実行タイミング: 毎営業日 17:30（市場クローズ後）
    - cron: 30 17 * * 1-5
    - timezone: Asia/Tokyo
"""

import argparse
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

from app.usecase.fetch_stock_prices_usecase import FetchStockPricesUseCase  # noqa: E402


def main() -> None:
    """コマンドライン引数を解析して株価データの差分取得を実行する。

    引数の詳細や使用例はモジュールdocstringを参照。
    """

    parser = argparse.ArgumentParser(description="株価データ取得スクリプト（差分取得）")
    parser.add_argument(
        "--wait",
        type=int,
        default=2,
        help="各週取得後の待機秒数（デフォルト: 2秒、rate limit: 120req/分）",
    )

    args = parser.parse_args()

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
            usecase.execute_incremental(wait_seconds=args.wait)

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
