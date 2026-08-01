"""セクター指数騰落率計算UseCase

セクター指数データの騰落率を計算する業務ロジックを提供する。

計算項目:
    - change_rate_1d: 前営業日比騰落率（%）
    - change_rate_5d: 5営業日前比騰落率（%）
    - change_rate_20d: 20営業日前比騰落率（%）
    - change_rate_60d: 60営業日前比騰落率（%）

使用例:
    from app.usecase.calculate_sector_index_changes_usecase import CalculateSectorIndexChangesUseCase

    with Session(engine) as session:
        usecase = CalculateSectorIndexChangesUseCase(session)

        # 差分計算
        result = usecase.execute_incremental()

        # 全量計算
        result = usecase.execute_full()
"""

from datetime import date, timedelta
from typing import Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


class CalculateSectorIndexChangesUseCase:
    """セクター指数騰落率計算UseCase"""

    def __init__(self, session: Session):
        """初期化

        Args:
            session: SQLAlchemyセッション
        """
        self.session = session

    def execute_incremental(self) -> dict:
        """差分計算を実行する

        最新計算日の翌日から現在までの騰落率を計算する。

        Returns:
            実行結果の辞書
            {
                'total_calculated': 計算件数,
                'total_updated': 更新件数,
            }
        """
        # change_rate_1dの最新計算日を取得
        latest_calculated_query = text("""
            SELECT MAX(date) as latest_calculated_date
            FROM sector_indices_daily
            WHERE change_rate_1d IS NOT NULL
        """)

        calc_result = self.session.execute(latest_calculated_query).fetchone()
        latest_calculated_date = calc_result[0] if calc_result and calc_result[0] else None

        if latest_calculated_date is None:
            print("  ⚠️  全量計算が未実施です。先に全量計算を実行してください。")
            return {"total_calculated": 0, "total_updated": 0}

        # セクター指数データの最新日を取得
        latest_date_query = text("""
            SELECT MAX(date) as latest_date
            FROM sector_indices_daily
        """)

        result = self.session.execute(latest_date_query).fetchone()
        latest_date = result[0] if result and result[0] else None

        if not latest_date:
            print("  ⚠️  データが存在しません")
            return {"total_calculated": 0, "total_updated": 0}

        # 最新計算日の翌日から現在までを対象
        target_start_date = latest_calculated_date + timedelta(days=1)

        print(f"  📅 最新計算日: {latest_calculated_date}")
        print(f"  📅 差分対象: {target_start_date} 〜 {latest_date}")

        if target_start_date > latest_date:
            print("  ⚠️  更新対象なし（すべて計算済み）")
            return {"total_calculated": 0, "total_updated": 0}

        # 90日前から取得（60営業日前までカバー）
        data_start_date = latest_date - timedelta(days=90)

        # 計算実行
        return self._calculate_and_update(
            data_start_date=data_start_date,
            target_start_date=target_start_date,
            latest_date=latest_date,
        )

    def execute_full(self) -> dict:
        """全量計算を実行する

        全レコードの騰落率を計算する。

        Returns:
            実行結果の辞書
            {
                'total_calculated': 計算件数,
                'total_updated': 更新件数,
            }
        """
        # 全データの日付範囲を取得
        date_range_query = text("""
            SELECT MIN(date) as min_date, MAX(date) as max_date
            FROM sector_indices_daily
        """)

        result = self.session.execute(date_range_query).fetchone()
        if not result or not result[0] or not result[1]:
            print("  ⚠️  データが存在しません")
            return {"total_calculated": 0, "total_updated": 0}

        min_date = result[0]
        max_date = result[1]

        print(f"  📅 計算期間: {min_date} 〜 {max_date}")

        # 計算実行（全期間）
        return self._calculate_and_update(
            data_start_date=min_date,
            target_start_date=min_date,
            latest_date=max_date,
        )

    def _calculate_and_update(
        self,
        data_start_date: date,
        target_start_date: date,
        latest_date: date,
    ) -> dict:
        """騰落率を計算してDBを更新する

        Args:
            data_start_date: データロード開始日
            target_start_date: 計算対象開始日
            latest_date: 最新日付

        Returns:
            実行結果の辞書
        """
        # データロード
        query = text("""
            SELECT id, index_code, date, close
            FROM sector_indices_daily
            WHERE date >= :start_date
            ORDER BY index_code, date
        """)

        df = pd.read_sql(query, self.session.bind, params={"start_date": data_start_date})
        print(f"  ✅ データロード完了: {len(df):,}件")

        # 計算対象レコードを取得
        target_query = text("""
            SELECT id, index_code, date, close
            FROM sector_indices_daily
            WHERE date >= :target_start_date
            ORDER BY index_code, date
        """)

        target_df = pd.read_sql(
            target_query, self.session.bind, params={"target_start_date": target_start_date}
        )

        if len(target_df) == 0:
            print("  ⚠️  計算対象なし")
            return {"total_calculated": 0, "total_updated": 0}

        print(f"  ✅ 計算対象: {len(target_df):,}件")

        # 騰落率計算
        updates = self._calculate_changes(df, target_df)

        print(f"  ✅ 計算完了: {len(updates):,}件")

        # DB更新
        total_updated = self._update_database(updates)

        print(f"  ✅ 更新完了: {total_updated:,}件")

        return {
            "total_calculated": len(updates),
            "total_updated": total_updated,
        }

    def _calculate_changes(self, all_df: pd.DataFrame, target_df: pd.DataFrame) -> list:
        """騰落率を計算する

        Args:
            all_df: 全データ（過去データ参照用）
            target_df: 計算対象データ

        Returns:
            更新データのリスト
        """
        updates = []

        # 全データをindex_codeでグループ化（過去データ参照用）
        all_data_grouped = all_df.groupby("index_code")

        # 計算対象をindex_codeでグループ化
        target_grouped = target_df.groupby("index_code")

        total_indices = len(target_grouped)
        processed_indices = 0

        for index_code, target_group in target_grouped:
            processed_indices += 1

            # 該当指数の全データを取得（過去データ参照用）
            all_group = all_data_grouped.get_group(index_code).copy()

            # date列をdatetime.dateに変換
            all_group["date"] = pd.to_datetime(all_group["date"]).dt.date
            all_group = all_group.sort_values("date").reset_index(drop=True)

            # 計算対象の各レコードについて騰落率計算
            for idx, row in target_group.iterrows():
                current_date = pd.to_datetime(row["date"]).date()
                current_close = row["close"]
                record_id = row["id"]

                # 1営業日前
                prev_1d = self._find_previous_business_day(all_group, current_date, 1, 10)
                change_rate_1d = None
                if prev_1d:
                    prev_close = all_group[all_group["date"] == prev_1d]["close"].iloc[0]
                    change_rate_1d = self._calculate_change_rate(current_close, prev_close)

                # 5営業日前
                prev_5d = self._find_previous_business_day(all_group, current_date, 5, 10)
                change_rate_5d = None
                if prev_5d:
                    prev_close = all_group[all_group["date"] == prev_5d]["close"].iloc[0]
                    change_rate_5d = self._calculate_change_rate(current_close, prev_close)

                # 20営業日前
                prev_20d = self._find_previous_business_day(all_group, current_date, 20, 30)
                change_rate_20d = None
                if prev_20d:
                    prev_close = all_group[all_group["date"] == prev_20d]["close"].iloc[0]
                    change_rate_20d = self._calculate_change_rate(current_close, prev_close)

                # 60営業日前
                prev_60d = self._find_previous_business_day(all_group, current_date, 60, 90)
                change_rate_60d = None
                if prev_60d:
                    prev_close = all_group[all_group["date"] == prev_60d]["close"].iloc[0]
                    change_rate_60d = self._calculate_change_rate(current_close, prev_close)

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

        print()  # 改行

        return updates

    def _find_previous_business_day(
        self,
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

    def _calculate_change_rate(self, current_close: float, previous_close: float) -> Optional[float]:
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

    def _update_database(self, updates: list) -> int:
        """DBを一括更新する

        Args:
            updates: 更新データのリスト

        Returns:
            更新件数
        """
        if len(updates) == 0:
            return 0

        # バッチサイズ（1000件ずつ更新）
        batch_size = 1000
        total_updated = 0

        for i in range(0, len(updates), batch_size):
            batch = updates[i : i + batch_size]

            # UPDATE文を生成（CASE文で一括更新）
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

            self.session.execute(text(update_query))
            self.session.commit()

            total_updated += len(batch)
            print(f"  DB更新進捗: {total_updated:,} / {len(updates):,}件", end="\r")

        print()  # 改行

        return total_updated
