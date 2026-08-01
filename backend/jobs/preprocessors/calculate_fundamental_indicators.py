"""ファンダメンタル指標計算スクリプト（全量計算）

株価データと財務データからファンダメンタル指標（20項目）を全件計算してDBに保存する。

コマンドライン引数:
    --start-date: 計算開始日（YYYY-MM-DD形式）
        デフォルト: 10年前 または 2016-07-28（Standardプラン開始日）の遅い方

    --end-date: 計算終了日（YYYY-MM-DD形式）
        デフォルト: 今日

    --test: テストモード（1銘柄のみ計算）
        デフォルト: False

使用例:
    # テストモード（1銘柄×1日のみ）
    $ uv run python backend/jobs/preprocessors/calculate_fundamental_indicators.py --test

    # 全銘柄計算（デフォルト: 全期間）
    $ uv run python backend/jobs/preprocessors/calculate_fundamental_indicators.py

    # 期間指定
    $ uv run python backend/jobs/preprocessors/calculate_fundamental_indicators.py \
        --start-date 2024-01-01 --end-date 2024-12-31

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - Point-in-Time設計（未来情報混入を防止）
    - 株式分割の自動検出・調整
    - 会計基準変更対応（YoY計算可能）
    - 予想データ活用（実績PER + 予想PER 2種類）
    - PostgreSQL UPSERT で高速保存（重複実行OK）

所要時間見積もり（全銘柄×10年分）:
    - 全銘柄（約4,444銘柄）× 約2,500営業日 = 約1,100万件
    - 所要時間: 約2-3時間（推定）

詳細設計: docs/ml/fundamental-indicators-design.md
"""

import argparse
import logging
import os
import sys
from datetime import date, datetime, timedelta
from multiprocessing import Pool
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
from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.domain.models.financial_statement import FinancialStatement  # noqa: E402
from app.usecase.calculate_fundamental_indicators_usecase import (  # noqa: E402
    CalculateFundamentalIndicatorsUseCase,
)


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
            print(f"  ✅ 財務データロード完了: {len(df):,}件")
            return df
    finally:
        engine.dispose()


def process_date_range(args_tuple: tuple) -> int:
    """日付範囲を処理するワーカー関数（並列処理用）

    Args:
        args_tuple: (start_date, end_date, stock_codes, database_url, worker_id, financial_df)

    Returns:
        int: 保存件数
    """
    start_date, end_date, stock_codes, database_url, worker_id, financial_df = args_tuple

    # 各ワーカーで独立したDB接続を作成
    engine = create_engine(database_url, echo=False, echo_pool=False, hide_parameters=True)

    print(f"  🔨 Worker {worker_id}: {start_date} 〜 {end_date} 開始")

    try:
        with Session(engine) as session:
            usecase = CalculateFundamentalIndicatorsUseCase(session, financial_df=financial_df)
            saved = usecase.calculate_and_save(
                start_date=start_date,
                end_date=end_date,
                stock_codes=stock_codes,
            )
            print(f"  ✅ Worker {worker_id}: {saved:,}件 完了")
            return saved
    except Exception as e:
        print(f"  ❌ Worker {worker_id}: エラー - {e}")
        raise
    finally:
        engine.dispose()


def main() -> None:
    """コマンドライン引数を解析してファンダメンタル指標計算を実行する。

    引数の詳細や使用例はモジュールdocstringを参照。
    """
    # デフォルト開始日: 10年前 または J-Quants Standardプラン開始日の遅い方
    standardplan_start = date(2016, 7, 28)
    ten_years_ago = date.today() - timedelta(days=365 * 10)
    default_start_date = max(standardplan_start, ten_years_ago).strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(description="ファンダメンタル指標計算スクリプト（全量計算）")
    parser.add_argument(
        "--start-date",
        type=str,
        default=default_start_date,
        help=f"計算開始日（YYYY-MM-DD形式、デフォルト: {default_start_date} ※10年前またはStandardプラン開始日）",
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
        help="テストモード（1銘柄×1日のみ計算）",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="並列処理のワーカー数（デフォルト: 1 = 非並列、推奨: 4-8）",
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
    stock_codes = None
    if args.test:
        print("⚠️  テストモード: 1銘柄×1日のみ計算")
        stock_codes = ["72030"]  # トヨタ自動車
        end_date = start_date + timedelta(days=1)  # 1日のみ

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
    print("🚀 ファンダメンタル指標計算スクリプト（全量計算）")
    print("=" * 80)
    print()

    start_time = datetime.now()

    try:
        # 財務データ全件ロード（メモリキャッシュ、約500MB）
        financial_df = load_all_financial_data(database_url)
        print()

        if args.workers > 1:
            # 並列処理モード
            print(f"  🚀 並列処理モード: {args.workers}ワーカー")

            # 営業日リストを取得（一時的にSessionを作成）
            with Session(engine) as session:
                usecase = CalculateFundamentalIndicatorsUseCase(session, financial_df=financial_df)
                trading_dates = usecase._get_trading_dates(start_date, end_date)

            if not trading_dates:
                print("  ⚠️  指定期間に営業日が見つかりません")
                sys.exit(0)

            # 営業日リストをワーカー数で分割
            chunk_size = len(trading_dates) // args.workers
            date_chunks = []
            for i in range(args.workers):
                chunk_start_idx = i * chunk_size
                if i == args.workers - 1:
                    # 最後のワーカーは残り全部
                    chunk_end_idx = len(trading_dates)
                else:
                    chunk_end_idx = (i + 1) * chunk_size

                chunk_start_date = trading_dates[chunk_start_idx]
                chunk_end_date = trading_dates[chunk_end_idx - 1]
                date_chunks.append(
                    (chunk_start_date, chunk_end_date, stock_codes, database_url, i + 1, financial_df)
                )

            # 並列実行
            with Pool(processes=args.workers) as pool:
                results = pool.map(process_date_range, date_chunks)

            saved = sum(results)

        else:
            # 非並列処理モード（既存のロジック）
            with Session(engine) as session:
                usecase = CalculateFundamentalIndicatorsUseCase(session, financial_df=financial_df)
                saved = usecase.calculate_and_save(
                    start_date=start_date,
                    end_date=end_date,
                    stock_codes=stock_codes,
                )

        end_time = datetime.now()
        elapsed = end_time - start_time

        print()
        print("=" * 80)
        print("✅ ファンダメンタル指標計算完了")
        print("=" * 80)
        print(f"  📊 保存件数: {saved:,}件")
        print(f"  ⏱️  所要時間: {elapsed}")
        print()

        # 正常終了
        sys.exit(0)

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
