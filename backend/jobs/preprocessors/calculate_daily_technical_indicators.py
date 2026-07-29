"""テクニカル指標計算スクリプト（差分計算）

株価データからテクニカル指標の差分を計算してDBに保存する。
DBの最新日付から現在までの差分のみを計算（冪等性担保）。

使用例:
    # 通常実行（DBの最新日付 + 1日 〜 今日）
    $ uv run python backend/jobs/preprocessors/calculate_daily_technical_indicators.py

    # バッチサイズを調整（デフォルト: 100）
    $ uv run python backend/jobs/preprocessors/calculate_daily_technical_indicators.py --batch-size 50

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - DBの最新日付を自動取得（冪等性担保）
    - pod再配置時も安全（DB状態ベース）

所要時間見積もり:
    - 1日分: 約10-20分（全銘柄）

GCP Cloud Scheduler設定例:
    - 実行タイミング: 毎営業日 18:00（市場クローズ後、株価取得完了後）
    - cron: 0 18 * * 1-5
    - timezone: Asia/Tokyo
"""

import argparse
import logging
import os
import sys
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
    """コマンドライン引数を解析してテクニカル指標の差分計算を実行する。

    引数の詳細や使用例はモジュールdocstringを参照。
    """

    parser = argparse.ArgumentParser(description="テクニカル指標計算スクリプト（差分計算）")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="バッチサイズ（一度に処理する銘柄数、デフォルト: 100）",
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
    engine = create_engine(database_url, echo=False, echo_pool=False, hide_parameters=True)

    # UseCase実行
    with Session(engine) as session:
        usecase = CalculateTechnicalIndicatorsUseCase(session)

        try:
            usecase.execute_incremental(batch_size=args.batch_size)

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
