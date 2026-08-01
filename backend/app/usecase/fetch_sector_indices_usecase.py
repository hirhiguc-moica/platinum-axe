"""セクター指数データ取得UseCase

J-Quants APIからセクター指数データ（TOPIX、TOPIX-17等）を取得してDBに保存するビジネスロジック。
"""

import time
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.infrastructure.jquants import JQuantsIndexRepository
from app.infrastructure.persistence.sector_index_daily_repository import (
    SectorIndexDailyRepository,
)


# 全38指数の定義
ALL_INDICES = [
    # TOPIX関連（9指数）
    ("0000", "TOPIX"),
    ("0028", "TOPIX Core30"),
    ("0029", "TOPIX Large 70"),
    ("002A", "TOPIX 100"),
    ("002B", "TOPIX Mid400"),
    ("002C", "TOPIX 500"),
    ("002D", "TOPIX Small"),
    ("002E", "TOPIX 1000"),
    ("002F", "TOPIX Small500"),
    # 市場別（4指数）
    ("0500", "東証プライム市場指数"),
    ("0501", "東証スタンダード市場指数"),
    ("0502", "東証グロース市場指数"),
    ("0070", "東証グロース市場250指数"),
    # TOPIX-17（17業種別指数）
    ("0080", "食品"),
    ("0081", "エネルギー資源"),
    ("0082", "建設・資材"),
    ("0083", "素材・化学"),
    ("0084", "医薬品"),
    ("0085", "自動車・輸送機"),
    ("0086", "鉄鋼・非鉄"),
    ("0087", "機械"),
    ("0088", "電機・精密"),
    ("0089", "情報通信・サービスその他"),
    ("008A", "電力・ガス"),
    ("008B", "運輸・物流"),
    ("008C", "商社・卸売"),
    ("008D", "小売"),
    ("008E", "銀行"),
    ("008F", "金融（除く銀行）"),
    ("0090", "不動産"),
    # その他（1指数）
    ("0075", "REIT"),
]


class FetchSectorIndicesUseCase:
    """セクター指数データ取得UseCase

    J-Quants APIからセクター指数データを取得してDBに保存する。
    全38指数を個別に取得、レート制限対策として1指数ごとに待機。

    使用例:
        >>> usecase = FetchSectorIndicesUseCase(session)
        >>> # 全件取得
        >>> usecase.execute_full(
        ...     start_date=datetime(2009, 2, 2),
        ...     end_date=datetime.now(),
        ...     wait_seconds=1
        ... )
        >>> # 差分取得
        >>> usecase.execute_incremental(wait_seconds=1)
    """

    def __init__(
        self,
        session: Session,
        api_repository: JQuantsIndexRepository | None = None,
        db_repository: SectorIndexDailyRepository | None = None,
    ):
        """初期化

        Args:
            session: SQLAlchemyの同期セッション
            api_repository: J-Quants API リポジトリ（省略時は自動生成）
            db_repository: DB永続化リポジトリ（省略時は自動生成）
        """
        self.session = session
        self.api_repo = api_repository or JQuantsIndexRepository()
        self.db_repo = db_repository or SectorIndexDailyRepository(session)

    def execute_full(
        self,
        start_date: datetime,
        end_date: datetime,
        wait_seconds: float = 1.0,
    ) -> dict:
        """全件取得モード（期間指定）

        指定期間の全38指数データを取得してDBに保存。
        レート制限対策として1指数ごとに待機。

        Args:
            start_date: 取得開始日
            end_date: 取得終了日
            wait_seconds: 各指数取得後の待機秒数（デフォルト: 1.0秒）

        Returns:
            dict: 実行結果
                - total_indices: 取得指数数
                - total_saved: 保存件数
                - elapsed_seconds: 所要時間（秒）

        Example:
            >>> usecase = FetchSectorIndicesUseCase(session)
            >>> result = usecase.execute_full(
            ...     start_date=datetime(2009, 2, 2),
            ...     end_date=datetime.now(),
            ...     wait_seconds=1
            ... )
            >>> print(result['total_saved'])
            140000
        """
        print("=" * 80)
        print("🔄 セクター指数データ取得開始（全件取得モード）")
        print("=" * 80)

        # 開始時刻を記録・表示
        start_time = time.time()
        start_datetime = datetime.now()
        print(f"🕐 開始時刻: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"📅 取得期間: {start_date.date()} 〜 {end_date.date()}")
        total_days = (end_date - start_date).days
        print(f"📊 取得日数: {total_days}日")
        print(f"📊 取得指数数: {len(ALL_INDICES)}指数")
        print(f"⏳ 待機時間: {wait_seconds}秒/指数")
        result = self._fetch_and_save_loop(
            start_date=start_date,
            end_date=end_date,
            wait_seconds=wait_seconds,
        )
        elapsed_seconds = time.time() - start_time

        # 終了時刻を記録・表示
        end_datetime = datetime.now()

        # 最終結果表示
        print("\n" + "=" * 80)
        print("🎉 セクター指数データ取得完了!")
        print("=" * 80)
        print(f"🕐 開始時刻: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕐 終了時刻: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 取得日数: {result['total_days']}日")
        print(f"📊 DB保存件数: {result['total_saved']:,}件")
        print(f"⏱️  所要時間: {elapsed_seconds:.1f}秒")
        print("=" * 80)

        return {
            "total_days": result["total_days"],
            "total_saved": result["total_saved"],
            "elapsed_seconds": elapsed_seconds,
        }

    def execute_incremental(self, wait_seconds: float = 1.0) -> dict:
        """差分取得モード

        DBの最新日付から現在までの差分データを取得。

        Args:
            wait_seconds: 各指数取得後の待機秒数（デフォルト: 1.0秒）

        Returns:
            dict: 実行結果
                - total_indices: 取得指数数
                - total_saved: 保存件数
                - elapsed_seconds: 所要時間（秒）
                - start_date: 取得開始日
                - end_date: 取得終了日

        Example:
            >>> usecase = FetchSectorIndicesUseCase(session)
            >>> result = usecase.execute_incremental()
            >>> print(result['total_saved'])
            38
        """
        print("=" * 80)
        print("🔄 セクター指数データ取得開始（差分取得モード）")
        print("=" * 80)

        # 開始時刻を記録・表示
        start_time = time.time()
        start_datetime = datetime.now()
        print(f"🕐 開始時刻: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

        # DBから最新日付を取得
        latest_date = self.db_repo.get_latest_date()

        if latest_date:
            # 最新日付の翌日から取得
            start_date = datetime.combine(latest_date, datetime.min.time()) + timedelta(days=1)
            print(f"📂 DB最新日付: {latest_date}")
            print(f"📅 取得開始日: {start_date.date()}")
        else:
            # DBが空の場合はデフォルト開始日（2009年2月2日）
            start_date = datetime(2009, 2, 2)
            print("⚠️  DBにデータが存在しません。初回取得を開始します。")
            print(f"📅 取得開始日: {start_date.date()} （J-Quants API取得可能開始日）")

        # 終了日は今日
        end_date = datetime.now()
        print(f"📅 取得終了日: {end_date.date()}")

        # 差分がない場合
        if start_date.date() > end_date.date():
            print("\n✅ 差分データはありません（最新です）")
            return {
                "total_indices": 0,
                "total_saved": 0,
                "elapsed_seconds": 0,
                "start_date": start_date.date(),
                "end_date": end_date.date(),
            }

        total_days = (end_date - start_date).days
        print(f"📊 取得日数: {total_days}日")
        print(f"📊 取得指数数: {len(ALL_INDICES)}指数")
        print(f"⏳ 待機時間: {wait_seconds}秒/指数")
        result = self._fetch_and_save_loop(
            start_date=start_date,
            end_date=end_date,
            wait_seconds=wait_seconds,
        )
        elapsed_seconds = time.time() - start_time

        # 終了時刻を記録・表示
        end_datetime = datetime.now()

        # 最終結果表示
        print("\n" + "=" * 80)
        print("🎉 差分データ取得完了!")
        print("=" * 80)
        print(f"🕐 開始時刻: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕐 終了時刻: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 取得日数: {result['total_days']}日")
        print(f"📊 DB保存件数: {result['total_saved']:,}件")
        print(f"⏱️  所要時間: {elapsed_seconds:.1f}秒")
        print("=" * 80)

        return {
            "total_days": result["total_days"],
            "total_saved": result["total_saved"],
            "elapsed_seconds": elapsed_seconds,
            "start_date": start_date.date(),
            "end_date": end_date.date(),
        }

    def _fetch_and_save_loop(
        self,
        start_date: datetime,
        end_date: datetime,
        wait_seconds: float,
    ) -> dict:
        """日単位で38指数を取得してDBに保存（内部メソッド）

        レート制限対策として、各指数取得後に待機する。

        Args:
            start_date: 取得開始日
            end_date: 取得終了日
            wait_seconds: 各指数取得後の待機秒数（レート制限60件/分対策）

        Returns:
            dict: 実行結果
                - total_days: 取得日数
                - total_saved: 保存件数

        Raises:
            Exception: API取得エラーまたはDB保存エラー
        """
        current_date = start_date
        day_count = 0
        total_saved = 0

        print("\n" + "=" * 80)
        print("📥 データ取得開始（日単位で38指数を取得）")
        print("=" * 80)

        try:
            while current_date <= end_date:
                day_count += 1
                day_start_time = time.time()

                print(f"\n📅 Day {day_count}: {current_date.date()}")

                day_saved = 0

                # 全指数を1日分まとめて取得
                try:
                    df = self.api_repo.fetch_index_daily_range(
                        index_code=None,  # 全指数取得
                        start_date=current_date,
                        end_date=current_date,  # 1日のみ
                    )

                    # 指数ごとに分割してDB保存
                    if len(df) > 0 and "Code" in df.columns:
                        for index_code, index_name in ALL_INDICES:
                            # 該当指数のデータのみ抽出
                            df_index = df[df["Code"] == index_code]
                            if len(df_index) > 0:
                                saved = self.db_repo.bulk_upsert(
                                    df=df_index, index_code=index_code, index_name=index_name
                                )
                                day_saved += saved

                except Exception as e:
                    print(f"  ⚠️  {current_date.date()} 取得エラー: {e}")
                    # デバッグ用: 詳細なトレースバック
                    import traceback
                    traceback.print_exc()
                    # エラー時はスキップして次の日へ

                # 1日分をコミット
                self.session.commit()
                total_saved += day_saved

                # 1日分の所要時間を計算
                day_elapsed = time.time() - day_start_time

                print(f"  ✅ DB保存完了: {day_saved}件（全指数）")
                print(f"  ⏱️  所要時間: {day_elapsed:.1f}秒")
                print(f"  📊 累計: {total_saved}件保存済み")

                # 次の日へ
                current_date = current_date + timedelta(days=1)

                # 最後の日以外は待機
                if current_date <= end_date:
                    time.sleep(wait_seconds)

        except Exception as e:
            self.session.rollback()
            print(f"\n❌ エラー発生: {e}")
            import traceback

            traceback.print_exc()
            raise

        return {
            "total_days": day_count,
            "total_saved": total_saved,
        }
