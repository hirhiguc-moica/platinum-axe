"""株価データ取得スクリプト

J-Quants API から株価日次データ（四本値）を取得してDBに保存する。

コマンドライン引数:
    --start-date: 取得開始日（YYYY-MM-DD形式）
        デフォルト: 2016-07-24（J-Quants Standardプランの開始日）

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

    # wait時間を短縮（1秒で約2時間、rate limit注意）
    $ uv run python backend/jobs/collectors/fetch_stock_prices.py --wait 1

    # 期間指定
    $ uv run python backend/jobs/collectors/fetch_stock_prices.py \
        --start-date 2024-01-01 --end-date 2024-12-31

    # 進捗から再開
    $ uv run python backend/jobs/collectors/fetch_stock_prices.py --resume

実装詳細:
    - 週単位分割（7日ずつ）でrate limit対策
    - 各週取得後10秒待機（--waitで調整可能）
    - 進捗保存（JSON）でエラー時の再開対応
    - PostgreSQL UPSERT で高速保存（重複実行OK）
    - NaN処理完全対応（pandas → PostgreSQL）
    - bool型変換対応（J-Quants APIの '0'/'1' → bool）

所要時間見積もり（全銘柄×10年分）:
    - wait=60秒: 約10.4時間
    - wait=10秒: 約2.5時間（推奨）
    - wait=1秒:  約1.9時間（rate limit注意）
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd
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

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.models.stock_price import StockPriceDaily
from jobs.collectors.jquants_client import JQuantsClient

# 進捗ファイルのパス
PROGRESS_FILE = project_root / "jobs" / "collectors" / "progress_stock_prices.json"


def save_progress(last_completed_date: str) -> None:
    """進捗を保存する。

    Args:
        last_completed_date (str): 最後に完了した日付（YYYY-MM-DD形式）
            例: "2024-12-31"
    """
    # ディレクトリが存在しない場合は作成
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_completed_date": last_completed_date}, f)


def load_progress() -> str | None:
    """進捗ファイルから最後に完了した日付を読み込む。

    Returns:
        str | None: 最後に完了した日付（YYYY-MM-DD形式）。
            ファイルが存在しない場合はNone。
            例: "2024-12-31"
    """
    if not PROGRESS_FILE.exists():
        return None

    with open(PROGRESS_FILE) as f:
        data = json.load(f)
        return data.get("last_completed_date")


def fetch_and_save_stock_prices(
    start_date: datetime,
    end_date: datetime,
    wait_seconds: int = 10,
    resume: bool = False,
) -> None:
    """J-Quants APIから株価データを取得してDBに保存する。

    週単位（7日ずつ）で分割取得し、PostgreSQL UPSERTで保存する。
    進捗はJSONファイルに保存され、エラー時の再開が可能。

    Args:
        start_date (datetime): データ取得の開始日。
            例: datetime(2024, 1, 1)
        end_date (datetime): データ取得の終了日。
            例: datetime(2024, 12, 31)
        wait_seconds (int, optional): 各週取得後の待機秒数。
            デフォルトは10秒。rate limit (120req/分) 対策のため。
            1秒まで短縮可能だが、rate limitに注意。
        resume (bool, optional): 進捗ファイルから再開するかどうか。
            デフォルトはFalse。Trueの場合、進捗ファイルの日付から再開。

    Raises:
        ValueError: APIキーまたはDATABASE_URLが設定されていない場合
        Exception: API取得エラーまたはDB保存エラー

    Note:
        - 進捗は progress_stock_prices.json に自動保存される
        - UPSERT方式のため、重複実行しても問題なし
        - 全銘柄×10年分の場合、約2.5時間（wait=10秒）かかる
    """

    print("=" * 80)
    print("🔄 株価データ取得開始")
    print("=" * 80)

    # 進捗から再開
    if resume:
        last_completed = load_progress()
        if last_completed:
            start_date = datetime.strptime(last_completed, "%Y-%m-%d") + timedelta(days=1)
            print(f"📂 進捗ファイルから再開: {last_completed} の翌日から")

    print(f"📅 取得期間: {start_date.date()} 〜 {end_date.date()}")
    total_days = (end_date - start_date).days
    print(f"📊 取得日数: {total_days}日")

    # 1. APIクライアント初期化
    try:
        client = JQuantsClient()
        print("✅ J-Quants APIクライアント初期化成功")
    except ValueError as e:
        print(f"❌ APIキーが設定されていません: {e}")
        return

    # 2. DB接続
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URLが設定されていません")
        return

    # 非同期版のURL（+asyncpg）を同期版に変換
    database_url = database_url.replace("+asyncpg", "")

    # SQLログを完全に抑制
    engine = create_engine(database_url, echo=False)
    print("✅ DB接続成功")

    # 3. 週単位で分割取得
    current_date = start_date
    week_count = 0
    total_inserted = 0
    total_updated = 0
    total_skipped = 0

    print("\n" + "=" * 80)
    print("📥 データ取得開始")
    print("=" * 80)

    session = Session(engine)

    try:
        while current_date <= end_date:
            week_count += 1
            week_end = min(current_date + timedelta(days=6), end_date)

            print(f"\n📅 Week {week_count}: {current_date.date()} 〜 {week_end.date()}")

            # API取得（応答時間計測）
            request_start = time.time()
            print("  🔄 API取得中...")

            try:
                df = client.get_daily_quotes_range(
                    start_dt=current_date,
                    end_dt=week_end,
                )
                request_elapsed = time.time() - request_start

                print(f"  ✅ API取得成功: {len(df)}件 ({request_elapsed:.2f}秒)")

            except Exception as e:
                print(f"  ❌ API取得エラー: {e}")
                # エラー時は進捗を保存して終了
                save_progress((current_date - timedelta(days=1)).strftime("%Y-%m-%d"))
                raise

            # DB保存
            if len(df) > 0:
                print("  🔄 DB保存中（UPSERT）...")
                save_start = time.time()
                inserted, updated, skipped = save_to_db(session, df)
                save_elapsed = time.time() - save_start
                total_inserted += inserted
                total_updated += updated
                total_skipped += skipped
                print(f"  ✅ DB保存完了: {inserted}件 ({save_elapsed:.2f}秒)")

            # 進捗保存
            save_progress(week_end.strftime("%Y-%m-%d"))

            # 累計表示
            print(f"  📊 累計: {total_inserted}件保存済み")

            # 次の週へ
            current_date = week_end + timedelta(days=1)

            # 最後の週以外は待機
            if current_date < end_date:
                print(f"  ⏳ {wait_seconds}秒待機中... (rate limit対策)")
                time.sleep(wait_seconds)

    except Exception as e:
        session.rollback()
        print(f"\n❌ エラー発生: {e}")
        import traceback

        traceback.print_exc()
        raise

    finally:
        session.close()

    # 最終結果表示
    print("\n" + "=" * 80)
    print("🎉 株価データ取得完了!")
    print("=" * 80)
    print(f"📊 取得週数: {week_count}週")
    print(f"📊 DB保存結果: {total_inserted:,}件（UPSERT: 新規挿入 or 更新）")
    print("=" * 80)


def save_to_db(session: Session, df) -> tuple[int, int, int]:
    """株価DataFrameをPostgreSQL UPSERTでDBに保存する。

    J-Quants APIから取得したDataFrameを、DBモデルに合わせて型変換し、
    ON CONFLICT DO UPDATE (UPSERT) で保存する。

    Args:
        session (Session): SQLAlchemyの同期セッション
        df (pd.DataFrame): J-Quants APIから取得した株価データ。
            カラム: Code, Date, O, H, L, C, Vo, Va, AdjO, AdjH, AdjL, AdjC,
                   AdjVo, AdjFactor, UL, LL

    Returns:
        tuple[int, int, int]: (新規追加件数, 更新件数, スキップ件数)。
            UPSERT方式のため、新規/更新の正確な区別はできない。
            全件を新規追加件数として返す。

    Note:
        - stock_code + date の UNIQUE制約により重複を防止
        - NaN は None に変換される
        - bool型は J-Quants の文字列 '0'/'1' から変換
        - volume/adjusted_volume は BIGINT (21億超の出来高対応)
    """
    if len(df) == 0:
        return 0, 0, 0

    # DataFrameのコピーを作成（元データを変更しない）
    df_copy = df.copy()

    # NaN を None に置換（一括処理）
    df_copy = df_copy.where(pd.notna(df_copy), None)

    # Date列を date 型に変換
    df_copy["Date"] = pd.to_datetime(df_copy["Date"]).dt.date

    # カラム名をDBカラム名にマッピング
    df_copy = df_copy.rename(
        columns={
            "Code": "stock_code",
            "Date": "date",
            "O": "open",
            "H": "high",
            "L": "low",
            "C": "close",
            "Vo": "volume",
            "Va": "turnover_value",
            "AdjO": "adjusted_open",
            "AdjH": "adjusted_high",
            "AdjL": "adjusted_low",
            "AdjC": "adjusted_close",
            "AdjVo": "adjusted_volume",
            "AdjFactor": "adjustment_factor",
            "UL": "is_upper_limit",
            "LL": "is_lower_limit",
        }
    )

    # 数値型をDecimalに変換（NaN対応）
    decimal_columns = [
        "open",
        "high",
        "low",
        "close",
        "turnover_value",
        "adjusted_open",
        "adjusted_high",
        "adjusted_low",
        "adjusted_close",
        "adjustment_factor",
    ]
    for col in decimal_columns:
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].apply(
                lambda x: Decimal(str(x)) if pd.notna(x) and x is not None else None
            )

    # 整数型に変換（NaN対応）
    int_columns = ["volume", "adjusted_volume"]
    for col in int_columns:
        if col in df_copy.columns:
            # NaNをNoneに置換してからintに変換
            df_copy[col] = df_copy[col].apply(
                lambda x: int(x) if pd.notna(x) and x is not None else None
            )

    # bool型に変換（文字列 '0'/'1' → bool）
    bool_columns = ["is_upper_limit", "is_lower_limit"]
    for col in bool_columns:
        if col in df_copy.columns:
            # 文字列 '0'/'1' をまずintに変換してからboolに
            # NaNやNoneはFalseに
            df_copy[col] = df_copy[col].apply(
                lambda x: bool(int(x)) if pd.notna(x) and x is not None and x != "" else False
            )

    # fetched_at を追加
    df_copy["fetched_at"] = datetime.now()

    # 必要なカラムのみ選択
    required_columns = [
        "stock_code",
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover_value",
        "adjusted_open",
        "adjusted_high",
        "adjusted_low",
        "adjusted_close",
        "adjusted_volume",
        "adjustment_factor",
        "is_upper_limit",
        "is_lower_limit",
        "fetched_at",
    ]
    df_copy = df_copy[required_columns]

    # DataFrameをdict形式に変換（一括変換、高速）
    records = df_copy.to_dict("records")

    # fetched_atをdatetimeに変換、volumeを確実にintに変換
    fetched_at_value = datetime.now()
    for record in records:
        # fetched_at変換
        if "fetched_at" in record and hasattr(record["fetched_at"], "to_pydatetime"):
            record["fetched_at"] = record["fetched_at"].to_pydatetime()
        else:
            record["fetched_at"] = fetched_at_value

        # volumeを確実にintに変換（NaN対応）
        if "volume" in record:
            val = record["volume"]
            # NaNまたはNoneの場合はNoneに、それ以外はintに変換
            record["volume"] = int(val) if pd.notna(val) and val is not None else None

        if "adjusted_volume" in record:
            val = record["adjusted_volume"]
            record["adjusted_volume"] = int(val) if pd.notna(val) and val is not None else None

        # TimestampMixinカラムを除外（自動生成されるため）
        record.pop("id", None)
        record.pop("created_at", None)
        record.pop("updated_at", None)

    # PostgreSQL UPSERT (SQLAlchemy ORM)
    stmt = insert(StockPriceDaily).values(records)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_stock_prices_daily_code_date",
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
            "turnover_value": stmt.excluded.turnover_value,
            "adjusted_open": stmt.excluded.adjusted_open,
            "adjusted_high": stmt.excluded.adjusted_high,
            "adjusted_low": stmt.excluded.adjusted_low,
            "adjusted_close": stmt.excluded.adjusted_close,
            "adjusted_volume": stmt.excluded.adjusted_volume,
            "adjustment_factor": stmt.excluded.adjustment_factor,
            "is_upper_limit": stmt.excluded.is_upper_limit,
            "is_lower_limit": stmt.excluded.is_lower_limit,
            "fetched_at": stmt.excluded.fetched_at,
        },
    )

    session.execute(stmt)
    session.commit()

    # UPSERT方式のため、新規/更新の区別はできない
    # 全件を「挿入または更新」として返す
    return len(records), 0, 0


def main() -> None:
    """コマンドライン引数を解析して株価データ取得を実行する。

    引数の詳細や使用例はモジュールdocstringを参照。
    """

    parser = argparse.ArgumentParser(description="株価データ取得スクリプト")
    parser.add_argument(
        "--start-date",
        type=str,
        default="2016-07-24",
        help="取得開始日（YYYY-MM-DD形式、デフォルト: 2016-07-24 ※Standardプランの開始日）",
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

    # 実行
    fetch_and_save_stock_prices(
        start_date=start_date,
        end_date=end_date,
        wait_seconds=args.wait,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
