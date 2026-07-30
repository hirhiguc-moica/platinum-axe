"""日次データ更新ワークフロー

株価取得 → 財務データ取得 → テクニカル指標計算を順次実行する統合ワークフロー。
各ステップは冪等なので、何度実行しても同じ結果。

使用例:
    # 通常実行
    $ uv run python backend/jobs/workflows/daily_data_update.py

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - 各ステップは独立しており、エラー時も再実行可能
    - 差分がない場合は自動的にスキップ

所要時間見積もり:
    - 1日分: 約15-30分（株価取得5-10分 + 財務取得1-5分 + テクニカル計算10-20分）

GCP Cloud Scheduler設定例:
    - 実行タイミング: 毎営業日 17:30（市場クローズ後）
    - cron: 30 17 * * 1-5
    - timezone: Asia/Tokyo
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

from app.usecase.calculate_technical_indicators_usecase import (  # noqa: E402
    CalculateTechnicalIndicatorsUseCase,
)
from app.usecase.fetch_financial_statements_usecase import (  # noqa: E402
    FetchFinancialStatementsUseCase,
)
from app.usecase.fetch_stock_prices_usecase import FetchStockPricesUseCase  # noqa: E402


def main() -> None:
    """日次データ更新ワークフローを実行する。

    ステップ1: 株価データ取得（差分）
    ステップ2: 財務データ取得（差分）
    ステップ3: テクニカル指標計算（差分）
    """

    print("=" * 80)
    print("📅 日次データ更新ワークフロー開始")
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

    try:
        with Session(engine) as session:
            # ========================================
            # ステップ1: 株価データ取得
            # ========================================
            print("\n[ステップ1] 株価データ取得")
            print("-" * 80)

            stock_usecase = FetchStockPricesUseCase(session)
            stock_result = stock_usecase.execute_incremental(wait_seconds=2)

            if stock_result["total_saved"] == 0:
                print("\n⚠️  新規株価データなし。未計算の指標がないかステップ3で確認します。")

            # ========================================
            # ステップ2: 財務データ取得
            # ========================================
            print("\n[ステップ2] 財務データ取得")
            print("-" * 80)

            financial_usecase = FetchFinancialStatementsUseCase(session)
            financial_result = financial_usecase.execute_incremental(wait_seconds=1)

            if financial_result["total_saved"] == 0:
                print("\n⚠️  新規財務データなし（最新です）")

            # ========================================
            # ステップ3: テクニカル指標計算（常に実行、UseCase側で差分判定）
            # ========================================
            print("\n[ステップ3] テクニカル指標計算")
            print("-" * 80)

            tech_usecase = CalculateTechnicalIndicatorsUseCase(session)
            tech_result = tech_usecase.execute_incremental(batch_size=100)

            # ========================================
            # 完了
            # ========================================
            print("\n" + "=" * 80)
            print("✅ 全ステップ完了")
            print("=" * 80)
            print(f"📊 株価データ保存: {stock_result['total_saved']:,}件")
            print(f"📊 財務データ保存: {financial_result['total_saved']:,}件")
            print(f"📊 テクニカル指標計算: {tech_result['total_calculated']:,}件")
            print("=" * 80)

            sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️  ユーザーによる中断")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ ワークフローエラー: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
