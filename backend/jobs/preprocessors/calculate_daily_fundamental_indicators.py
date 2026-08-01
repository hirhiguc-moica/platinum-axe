"""ファンダメンタル指標計算スクリプト（差分計算）

株価データと財務データからファンダメンタル指標（20項目）の差分を計算してDBに保存する。
DBの最新日付から現在までの差分のみを計算（冪等性担保）。

使用例:
    # 通常実行（DBの最新日付 + 1日 〜 今日）
    $ uv run python backend/jobs/preprocessors/calculate_daily_fundamental_indicators.py

    # 特定の開始日から計算
    $ uv run python backend/jobs/preprocessors/calculate_daily_fundamental_indicators.py --start-date 2024-07-01

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - DBの最新日付を自動取得（冪等性担保）
    - 財務データ全件メモリキャッシュ（約500MB）
    - Point-in-Time設計（未来情報混入を防止）
    - pod再配置時も安全（DB状態ベース）

所要時間見積もり:
    - 1日分: 約30-60秒（全銘柄）

GCP Cloud Scheduler設定例:
    - 実行タイミング: 毎営業日 18:00（市場クローズ後、株価・財務取得完了後）
    - cron: 0 18 * * 1-5
    - timezone: Asia/Tokyo
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

import pandas as pd  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.infrastructure.persistence.financial_statement_repository import (  # noqa: E402
    FinancialStatementRepository,
)
from app.usecase.calculate_fundamental_indicators_usecase import (  # noqa: E402
    CalculateFundamentalIndicatorsUseCase,
)


def load_all_financial_data(database_url: str) -> pd.DataFrame:
    """財務データ全件をメモリにロード（約19万件、列選択により約300MB）

    Args:
        database_url: データベースURL

    Returns:
        pd.DataFrame: 財務データ全件

    Note:
        - ORM生成を回避し、列選択で直接DataFrameに変換
        - ファンダメンタル指標計算に必要な24列のみ抽出
        - メモリ使用量: 約300MB（ORM経由の約500MBから削減）
    """
    print("  📦 財務データ全件ロード中...")
    engine = create_engine(database_url, echo=False, echo_pool=False, hide_parameters=True)

    try:
        with Session(engine) as session:
            repo = FinancialStatementRepository(session)
            df = repo.load_all_as_dataframe()
            print(f"  ✅ 財務データロード完了: {len(df):,}件")
            return df
    finally:
        engine.dispose()


def main() -> None:
    """コマンドライン引数を解析してファンダメンタル指標の差分計算を実行する。

    引数の詳細や使用例はモジュールdocstringを参照。
    """
    parser = argparse.ArgumentParser(description="ファンダメンタル指標計算スクリプト（差分計算）")
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="計算開始日（YYYY-MM-DD形式、デフォルト: DBの最新日付 + 1日）",
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
    print("=" * 80)
    print("🚀 ファンダメンタル指標計算スクリプト（差分計算）")
    print("=" * 80)
    print()

    start_time = datetime.now()

    try:
        # 財務データ全件ロード（メモリキャッシュ、約500MB）
        financial_df = load_all_financial_data(database_url)
        print()

        with Session(engine) as session:
            usecase = CalculateFundamentalIndicatorsUseCase(session, financial_df=financial_df)

            # 開始日の決定
            if args.start_date:
                start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
                print(f"  📅 計算開始日（指定）: {start_date}")
            else:
                # DBの最新日付を取得
                latest_date = usecase.fundamental_repo.get_latest_date()
                if latest_date:
                    # 最新日付の翌日から計算
                    from datetime import timedelta

                    start_date = latest_date + timedelta(days=1)
                    print(f"  📅 DBの最新日付: {latest_date}")
                    print(f"  📅 計算開始日（最新日+1日）: {start_date}")
                else:
                    # データが1件もない場合はエラー
                    print("  ⚠️  DBにファンダメンタル指標データが存在しません")
                    print("  💡 全量計算スクリプトを先に実行してください:")
                    print("     uv run python backend/jobs/preprocessors/calculate_fundamental_indicators.py")
                    sys.exit(1)

            # 終了日は今日
            end_date = date.today()
            print(f"  📅 計算終了日: {end_date}")
            print()

            # 差分計算実行
            saved = usecase.calculate_and_save(
                start_date=start_date,
                end_date=end_date,
                stock_codes=None,  # 全銘柄
            )

        end_time = datetime.now()
        elapsed = end_time - start_time

        print()
        print("=" * 80)
        print("✅ ファンダメンタル指標差分計算完了")
        print("=" * 80)
        print(f"  📊 保存件数: {saved:,}件")
        print(f"  ⏱️  所要時間: {elapsed}")
        print()

        # 正常終了
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️  ユーザーによる中断")
        sys.exit(1)

    except Exception as e:
        end_time = datetime.now()
        elapsed = end_time - start_time

        print()
        print("=" * 80)
        print("❌ エラー発生")
        print("=" * 80)
        print(f"  エラー内容: {e}")
        print(f"  ⏱️  所要時間: {elapsed}")
        print()

        # エラー終了
        sys.exit(1)


if __name__ == "__main__":
    main()
