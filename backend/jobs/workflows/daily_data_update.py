"""日次データ更新ワークフロー

株価取得 → 財務データ取得 → テクニカル指標計算 → ファンダメンタル指標計算を順次実行する統合ワークフロー。
各ステップは冪等なので、何度実行しても同じ結果。

使用例:
    # 通常実行
    $ uv run python backend/jobs/workflows/daily_data_update.py

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - 各ステップは独立しており、エラー時も再実行可能
    - 差分がない場合は自動的にスキップ

所要時間見積もり:
    - 1日分: 約15-30分（株価5-10分 + 財務1-5分 + テクニカル10-20分 + ファンダメンタル0.5-1分）

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

import pandas as pd  # noqa: E402
from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.domain.models.financial_statement import FinancialStatement  # noqa: E402
from app.usecase.calculate_fundamental_indicators_usecase import (  # noqa: E402
    CalculateFundamentalIndicatorsUseCase,
)
from app.usecase.calculate_technical_indicators_usecase import (  # noqa: E402
    CalculateTechnicalIndicatorsUseCase,
)
from app.usecase.fetch_financial_statements_usecase import (  # noqa: E402
    FetchFinancialStatementsUseCase,
)
from app.usecase.fetch_stock_prices_usecase import FetchStockPricesUseCase  # noqa: E402


def load_all_financial_data(database_url: str) -> pd.DataFrame:
    """財務データ全件をメモリにロード（約19万件、500MB）

    Args:
        database_url: データベースURL

    Returns:
        pd.DataFrame: 財務データ全件
    """
    print("  📦 財務データ全件ロード中...")
    engine = create_engine(database_url, echo=False, echo_pool=False, hide_parameters=True)

    try:
        with Session(engine) as session:
            stmt = select(FinancialStatement)
            result = session.execute(stmt)
            all_fins = result.scalars().all()

            # DataFrameに変換
            records = []
            for fin in all_fins:
                # 必要なカラムのみ抽出（メモリ効率化）
                records.append({
                    "stock_code": fin.stock_code,
                    "disc_date": fin.disc_date,
                    "disc_time": fin.disc_time,
                    "type_of_document": fin.type_of_document,
                    "cur_per_type": fin.cur_per_type,
                    "cur_per_st": fin.cur_per_st,
                    "cur_per_en": fin.cur_per_en,
                    # 財務データ
                    "sales": fin.sales,
                    "op": fin.op,
                    "od_p": fin.od_p,
                    "np": fin.np,
                    "eps": fin.eps,
                    "bps": fin.bps,
                    "cfo": fin.cfo,
                    "ta": fin.ta,
                    "eq": fin.eq,
                    "sh_out_fy": fin.sh_out_fy,
                    # 配当
                    "div_ann": fin.div_ann,
                    # 予想データ
                    "f_eps": fin.f_eps,
                    "nx_f_eps": fin.nx_f_eps,
                    "f_div_ann": fin.f_div_ann,
                    "nx_f_div_ann": fin.nx_f_div_ann,
                })

            df = pd.DataFrame(records)
            print(f"  ✅ 財務データロード完了: {len(df):,}件\n")
            return df
    finally:
        engine.dispose()


def main() -> None:
    """日次データ更新ワークフローを実行する。

    ステップ1: 株価データ取得（差分）
    ステップ2: 財務データ取得（差分）
    ステップ3: テクニカル指標計算（差分）
    ステップ4: ファンダメンタル指標計算（差分）
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
            # ステップ4: ファンダメンタル指標計算（差分）
            # ========================================
            print("\n[ステップ4] ファンダメンタル指標計算")
            print("-" * 80)

            # 財務データ全件メモリロード
            financial_df = load_all_financial_data(database_url)

            # ファンダメンタル指標UseCase作成（メモリキャッシュ使用）
            fundamental_usecase = CalculateFundamentalIndicatorsUseCase(
                session, financial_df=financial_df
            )

            # DBの最新日付を取得
            from datetime import date, timedelta

            latest_date = fundamental_usecase.fundamental_repo.get_latest_date()
            if latest_date:
                start_date = latest_date + timedelta(days=1)
                end_date = date.today()

                print(f"  📅 DBの最新日付: {latest_date}")
                print(f"  📅 計算期間: {start_date} 〜 {end_date}")

                fundamental_saved = fundamental_usecase.calculate_and_save(
                    start_date=start_date,
                    end_date=end_date,
                    stock_codes=None,  # 全銘柄
                )
            else:
                print("  ⚠️  DBにファンダメンタル指標データが存在しません")
                print("  💡 全量計算スクリプトを先に実行してください")
                fundamental_saved = 0

            # ========================================
            # 完了
            # ========================================
            print("\n" + "=" * 80)
            print("✅ 全ステップ完了")
            print("=" * 80)
            print(f"📊 株価データ保存: {stock_result['total_saved']:,}件")
            print(f"📊 財務データ保存: {financial_result['total_saved']:,}件")
            print(f"📊 テクニカル指標計算: {tech_result['total_calculated']:,}件")
            print(f"📊 ファンダメンタル指標計算: {fundamental_saved:,}件")
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
