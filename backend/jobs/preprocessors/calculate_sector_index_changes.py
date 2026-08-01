"""セクター指数騰落率計算スクリプト（全量計算）

セクター指数データ（sector_indices_daily）の騰落率を計算してDBに保存する。

計算項目:
    - change_rate_1d: 前営業日比騰落率（%）
    - change_rate_5d: 5営業日前比騰落率（%）
    - change_rate_20d: 20営業日前比騰落率（%）
    - change_rate_60d: 60営業日前比騰落率（%）

使用例:
    # 全量計算
    $ uv run python backend/jobs/preprocessors/calculate_sector_index_changes.py

実装詳細:
    - 全7万レコードをメモリに一括ロード（約10MB）
    - index_codeごとにグループ化して計算
    - 営業日探索: 1日前は最大10日遡る、5日前は最大10日遡る、20日前は最大30日遡る、60日前は最大90日遡る
    - 見つからない場合はNULL
    - PostgreSQL UPDATE で一括保存

所要時間見積もり:
    - 全7万レコード: 約30-60秒

実行タイミング:
    - 初回のみ: 全量計算（このスクリプト）
    - 日次: 差分計算（calculate_daily_sector_index_changes.py）
"""

import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

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

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


def find_previous_business_day(
    df: pd.DataFrame,
    current_date: date,
    target_days: int,
    max_search_days: int,
) -> Optional[date]:
    """指定営業日前の日付を探す

    Args:
        df: 該当指数のDataFrame（date列でソート済み）
        current_date: 基準日
        target_days: 目標営業日数（1, 5, 20, 60）
        max_search_days: 最大遡及日数（10, 10, 30, 90）

    Returns:
        見つかった場合は日付、見つからない場合はNone
    """
    # current_date以前のデータのみ
    past_df = df[df["date"] < current_date].copy()

    if len(past_df) == 0:
        return None

    # 営業日数をカウント
    if len(past_df) >= target_days:
        # target_days営業日前のデータを取得（後ろからtarget_days番目）
        return past_df.iloc[-target_days]["date"]

    # 見つからない場合はNone
    return None


def calculate_change_rate(current_close: float, previous_close: float) -> float:
    """騰落率を計算

    Args:
        current_close: 現在の終値
        previous_close: 過去の終値

    Returns:
        騰落率（%）
    """
    if previous_close == 0 or pd.isna(previous_close):
        return None

    return ((current_close - previous_close) / previous_close) * 100


def main() -> None:
    """メイン処理"""
    print("=" * 80)
    print("📊 セクター指数騰落率計算（全量）開始")
    print("=" * 80)

    # データベース接続
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URLが設定されていません。.envファイルを確認してください。")
        sys.exit(1)

    # 非同期版のURL（+asyncpg）を同期版に変換
    database_url = database_url.replace("+asyncpg", "")

    engine = create_engine(database_url, echo=False)

    try:
        with Session(engine) as session:
            # ========================================
            # 1. 全データをメモリにロード
            # ========================================
            print("\n[ステップ1] データロード")
            print("-" * 80)

            query = text("""
                SELECT id, index_code, date, close
                FROM sector_indices_daily
                ORDER BY index_code, date
            """)

            df = pd.read_sql(query, engine)
            print(f"  ✅ ロード完了: {len(df):,}件")

            # ========================================
            # 2. index_codeごとに騰落率計算
            # ========================================
            print("\n[ステップ2] 騰落率計算")
            print("-" * 80)

            # 結果を格納するリスト
            updates = []

            # index_codeごとにグループ化
            grouped = df.groupby("index_code")
            total_indices = len(grouped)
            processed_indices = 0

            for index_code, group_df in grouped:
                processed_indices += 1

                # date列をdatetime.dateに変換
                group_df = group_df.copy()
                group_df["date"] = pd.to_datetime(group_df["date"]).dt.date

                # 日付順にソート
                group_df = group_df.sort_values("date").reset_index(drop=True)

                # 各レコードについて騰落率計算
                for idx, row in group_df.iterrows():
                    current_date = row["date"]
                    current_close = row["close"]
                    record_id = row["id"]

                    # 1営業日前
                    prev_1d = find_previous_business_day(
                        group_df, current_date, target_days=1, max_search_days=10
                    )
                    change_rate_1d = None
                    if prev_1d:
                        prev_close = group_df[group_df["date"] == prev_1d]["close"].iloc[0]
                        change_rate_1d = calculate_change_rate(current_close, prev_close)

                    # 5営業日前
                    prev_5d = find_previous_business_day(
                        group_df, current_date, target_days=5, max_search_days=10
                    )
                    change_rate_5d = None
                    if prev_5d:
                        prev_close = group_df[group_df["date"] == prev_5d]["close"].iloc[0]
                        change_rate_5d = calculate_change_rate(current_close, prev_close)

                    # 20営業日前
                    prev_20d = find_previous_business_day(
                        group_df, current_date, target_days=20, max_search_days=30
                    )
                    change_rate_20d = None
                    if prev_20d:
                        prev_close = group_df[group_df["date"] == prev_20d]["close"].iloc[0]
                        change_rate_20d = calculate_change_rate(current_close, prev_close)

                    # 60営業日前
                    prev_60d = find_previous_business_day(
                        group_df, current_date, target_days=60, max_search_days=90
                    )
                    change_rate_60d = None
                    if prev_60d:
                        prev_close = group_df[group_df["date"] == prev_60d]["close"].iloc[0]
                        change_rate_60d = calculate_change_rate(current_close, prev_close)

                    # 更新データを追加
                    updates.append(
                        {
                            "id": record_id,
                            "change_rate_1d": change_rate_1d,
                            "change_rate_5d": change_rate_5d,
                            "change_rate_20d": change_rate_20d,
                            "change_rate_60d": change_rate_60d,
                        }
                    )

                # 進捗表示（上書き）
                print(f"  進捗: {processed_indices}/{total_indices} 指数完了", end="\r")

            print(f"\n  ✅ 計算完了: {len(updates):,}件")

            # ========================================
            # 3. DBに一括UPDATE
            # ========================================
            print("\n[ステップ3] DB更新")
            print("-" * 80)

            # バッチサイズ（1000件ずつ更新）
            batch_size = 1000
            total_updated = 0

            for i in range(0, len(updates), batch_size):
                batch = updates[i : i + batch_size]

                # UPDATE文を生成（CASE文で一括更新）
                # NULLの場合は'NULL'、数値の場合はそのまま
                when_clauses_1d = []
                when_clauses_5d = []
                when_clauses_20d = []
                when_clauses_60d = []

                for item in batch:
                    id_str = f"'{item['id']}'"

                    # change_rate_1d
                    if item["change_rate_1d"] is not None:
                        when_clauses_1d.append(f"WHEN {id_str} THEN {item['change_rate_1d']}")
                    else:
                        when_clauses_1d.append(f"WHEN {id_str} THEN NULL")

                    # change_rate_5d
                    if item["change_rate_5d"] is not None:
                        when_clauses_5d.append(f"WHEN {id_str} THEN {item['change_rate_5d']}")
                    else:
                        when_clauses_5d.append(f"WHEN {id_str} THEN NULL")

                    # change_rate_20d
                    if item["change_rate_20d"] is not None:
                        when_clauses_20d.append(f"WHEN {id_str} THEN {item['change_rate_20d']}")
                    else:
                        when_clauses_20d.append(f"WHEN {id_str} THEN NULL")

                    # change_rate_60d
                    if item["change_rate_60d"] is not None:
                        when_clauses_60d.append(f"WHEN {id_str} THEN {item['change_rate_60d']}")
                    else:
                        when_clauses_60d.append(f"WHEN {id_str} THEN NULL")

                # ID一覧
                ids = [f"'{item['id']}'" for item in batch]

                update_query = f"""
                    UPDATE sector_indices_daily
                    SET
                        change_rate_1d = CASE id
                            {' '.join(when_clauses_1d)}
                        END,
                        change_rate_5d = CASE id
                            {' '.join(when_clauses_5d)}
                        END,
                        change_rate_20d = CASE id
                            {' '.join(when_clauses_20d)}
                        END,
                        change_rate_60d = CASE id
                            {' '.join(when_clauses_60d)}
                        END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id IN ({', '.join(ids)})
                """

                session.execute(text(update_query))
                session.commit()

                total_updated += len(batch)
                print(f"  進捗: {total_updated:,} / {len(updates):,}件", end="\r")

            print(f"\n  ✅ 更新完了: {total_updated:,}件")

            # ========================================
            # 完了
            # ========================================
            print("\n" + "=" * 80)
            print("✅ 全量計算完了")
            print("=" * 80)
            print(f"📊 計算件数: {len(updates):,}件")
            print(f"📊 更新件数: {total_updated:,}件")
            print("=" * 80)

    except KeyboardInterrupt:
        print("\n⚠️  ユーザーによって中断されました")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
