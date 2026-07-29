"""テクニカル指標計算スクリプト（全量計算）

株価データからテクニカル指標（125項目）を全件計算してDBに保存する。

コマンドライン引数:
    --start-date: 計算開始日（YYYY-MM-DD形式）
        デフォルト: 2016-07-28（J-Quants Standardプランの開始日）

    --end-date: 計算終了日（YYYY-MM-DD形式）
        デフォルト: 今日

    --test: テストモード（1銘柄のみ計算）
        デフォルト: False

    --batch-size: バッチサイズ（一度に処理する銘柄数）
        デフォルト: 100銘柄

使用例:
    # テストモード（1銘柄のみ）
    $ uv run python backend/jobs/preprocessors/calculate_technical_indicators.py --test

    # 全銘柄計算（デフォルト: 全期間）
    $ uv run python backend/jobs/preprocessors/calculate_technical_indicators.py

    # 期間指定
    $ uv run python backend/jobs/preprocessors/calculate_technical_indicators.py \
        --start-date 2024-01-01 --end-date 2024-12-31

    # バッチサイズ調整
    $ uv run python backend/jobs/preprocessors/calculate_technical_indicators.py \
        --batch-size 50

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - 銘柄単位でテクニカル指標を計算
    - PostgreSQL UPSERT で高速保存（重複実行OK）

所要時間見積もり（全銘柄×10年分）:
    - batch_size=100: 約2-3時間（推奨）
    - batch_size=50:  約3-4時間
"""

import argparse
import logging
import os
import sys
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

# SQLAlchemyとPostgreSQLドライバのログを完全に抑制
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.pool").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.orm").setLevel(logging.ERROR)

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# .envファイルを読み込み
env_path = project_root / ".env"
load_dotenv(env_path)

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.usecase.calculate_technical_indicators_usecase import (  # noqa: E402
    CalculateTechnicalIndicatorsUseCase,
)


def main() -> None:
    """コマンドライン引数を解析してテクニカル指標計算を実行する。

    引数の詳細や使用例はモジュールdocstringを参照。
    """

    parser = argparse.ArgumentParser(description="テクニカル指標計算スクリプト（全量計算）")
    parser.add_argument(
        "--start-date",
        type=str,
        default="2016-07-28",
        help="計算開始日（YYYY-MM-DD形式、デフォルト: 2016-07-28 ※Standardプランの開始日）",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=date.today().strftime("%Y-%m-%d"),
        help="計算終了日（YYYY-MM-DD形式、デフォルト: 今日）",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモード（1銘柄のみ計算）",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="バッチサイズ（一度に処理する銘柄数、デフォルト: 100）",
    )

    args = parser.parse_args()

    # 日付パース
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()

    # 日付の妥当性検証
    if start_date > end_date:
        print(f"❌ エラー: --start-date ({start_date}) が --end-date ({end_date}) より後の日付です")
        sys.exit(1)

    # テストモード
    batch_size = args.batch_size
    limit_stocks = None
    if args.test:
        print("⚠️  テストモード: 1銘柄のみ計算")
        limit_stocks = 1

    # DB接続
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URLが設定されていません")
        sys.exit(1)

    # 非同期版のURL（+asyncpg）を同期版に変換
    database_url = database_url.replace("+asyncpg", "")

    # SQLログを完全に抑制
    engine = create_engine(database_url, echo=False, echo_pool=False, hide_parameters=True)

    # UseCase実行
    with Session(engine) as session:
        usecase = CalculateTechnicalIndicatorsUseCase(session)

        try:
            usecase.execute_full(
                start_date=start_date,
                end_date=end_date,
                batch_size=batch_size,
                limit_stocks=limit_stocks,
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
