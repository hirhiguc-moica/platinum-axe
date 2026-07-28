"""株価データ取得UseCase

J-Quants APIから株価データを取得してDBに保存するビジネスロジック。
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.infrastructure.jquants import JQuantsStockPriceRepository
from app.infrastructure.persistence import StockPriceDailyRepository


class FetchStockPricesUseCase:
    """株価データ取得UseCase

    J-Quants APIから株価データを取得してDBに保存する。
    週単位分割、進捗保存、差分取得に対応。

    使用例:
        >>> usecase = FetchStockPricesUseCase(session)
        >>> # 全件取得
        >>> usecase.execute_full(
        ...     start_date=datetime(2016, 7, 24),
        ...     end_date=datetime.now(),
        ...     wait_seconds=10
        ... )
        >>> # 差分取得
        >>> usecase.execute_incremental(wait_seconds=2)
    """

    # 進捗ファイルのパス（プロジェクトルート/jobs/collectors/）
    PROGRESS_FILE_NAME = "progress_stock_prices.json"

    def __init__(
        self,
        session: Session,
        api_repository: JQuantsStockPriceRepository | None = None,
        db_repository: StockPriceDailyRepository | None = None,
        progress_file_path: Path | None = None,
    ):
        """初期化

        Args:
            session: SQLAlchemyの同期セッション
            api_repository: J-Quants API リポジトリ（省略時は自動生成）
            db_repository: DB永続化リポジトリ（省略時は自動生成）
            progress_file_path: 進捗ファイルのパス（省略時はデフォルト）
        """
        self.session = session
        self.api_repo = api_repository or JQuantsStockPriceRepository()
        self.db_repo = db_repository or StockPriceDailyRepository(session)

        # 進捗ファイルのパス
        if progress_file_path:
            self.progress_file = progress_file_path
        else:
            # デフォルト: プロジェクトルート/jobs/collectors/progress_stock_prices.json
            # このファイルの場所から推測
            project_root = Path(__file__).parent.parent.parent.parent
            self.progress_file = project_root / "jobs" / "collectors" / self.PROGRESS_FILE_NAME

    def execute_full(
        self,
        start_date: datetime,
        end_date: datetime,
        wait_seconds: int = 10,
        resume: bool = False,
    ) -> dict:
        """全件取得モード（期間指定）

        指定期間の株価データを全件取得してDBに保存。
        週単位分割、進捗保存、エラー時再開に対応。

        Args:
            start_date: 取得開始日
            end_date: 取得終了日
            wait_seconds: 各週取得後の待機秒数（デフォルト: 10秒）
            resume: 進捗ファイルから再開するか（デフォルト: False）

        Returns:
            dict: 実行結果
                - total_weeks: 取得週数
                - total_saved: 保存件数
                - elapsed_seconds: 所要時間（秒）

        Example:
            >>> usecase = FetchStockPricesUseCase(session)
            >>> result = usecase.execute_full(
            ...     start_date=datetime(2024, 1, 1),
            ...     end_date=datetime(2024, 12, 31),
            ...     wait_seconds=10
            ... )
            >>> print(result['total_saved'])
            1000000
        """
        print("=" * 80)
        print("🔄 株価データ取得開始（全件取得モード）")
        print("=" * 80)

        # 進捗から再開
        if resume:
            last_completed = self._load_progress()
            if last_completed:
                start_date = datetime.strptime(last_completed, "%Y-%m-%d") + timedelta(days=1)
                print(f"📂 進捗ファイルから再開: {last_completed} の翌日から")

        print(f"📅 取得期間: {start_date.date()} 〜 {end_date.date()}")
        total_days = (end_date - start_date).days
        print(f"📊 取得日数: {total_days}日")

        # 実行
        start_time = time.time()
        result = self._fetch_and_save_loop(
            start_date=start_date,
            end_date=end_date,
            wait_seconds=wait_seconds,
            save_progress=True,  # 全件取得モードでは進捗保存ON
        )
        elapsed_seconds = time.time() - start_time

        # 最終結果表示
        print("\n" + "=" * 80)
        print("🎉 株価データ取得完了!")
        print("=" * 80)
        print(f"📊 取得週数: {result['total_weeks']}週")
        print(f"📊 DB保存件数: {result['total_saved']:,}件")
        print(f"⏱️  所要時間: {elapsed_seconds:.1f}秒")
        print("=" * 80)

        return {
            "total_weeks": result["total_weeks"],
            "total_saved": result["total_saved"],
            "elapsed_seconds": elapsed_seconds,
        }

    def execute_incremental(self, wait_seconds: int = 2) -> dict:
        """差分取得モード

        DBの最新日付から現在までの差分データを取得。
        進捗保存は不要（短時間で完了するため）。

        Args:
            wait_seconds: 各週取得後の待機秒数（デフォルト: 2秒）

        Returns:
            dict: 実行結果
                - total_weeks: 取得週数
                - total_saved: 保存件数
                - elapsed_seconds: 所要時間（秒）
                - start_date: 取得開始日
                - end_date: 取得終了日

        Example:
            >>> usecase = FetchStockPricesUseCase(session)
            >>> result = usecase.execute_incremental()
            >>> print(result['total_saved'])
            19119
        """
        print("=" * 80)
        print("🔄 株価データ取得開始（差分取得モード）")
        print("=" * 80)

        # DBから最新日付を取得
        latest_date = self.db_repo.get_latest_date()

        if latest_date:
            # 最新日付の翌日から取得
            start_date = datetime.combine(latest_date, datetime.min.time()) + timedelta(days=1)
            print(f"📂 DB最新日付: {latest_date}")
            print(f"📅 取得開始日: {start_date.date()}")
        else:
            # DBが空の場合はデフォルト開始日（Standardプランの開始日）
            start_date = datetime(2016, 7, 28)
            print("⚠️  DBにデータが存在しません。初回取得を開始します。")
            print(f"📅 取得開始日: {start_date.date()}")

        # 終了日は今日
        end_date = datetime.now()
        print(f"📅 取得終了日: {end_date.date()}")

        # 差分がない場合
        if start_date.date() > end_date.date():
            print("\n✅ 差分データはありません（最新です）")
            return {
                "total_weeks": 0,
                "total_saved": 0,
                "elapsed_seconds": 0,
                "start_date": start_date.date(),
                "end_date": end_date.date(),
            }

        total_days = (end_date - start_date).days
        print(f"📊 取得日数: {total_days}日")

        # 実行
        start_time = time.time()
        result = self._fetch_and_save_loop(
            start_date=start_date,
            end_date=end_date,
            wait_seconds=wait_seconds,
            save_progress=False,  # 差分取得モードでは進捗保存OFF
        )
        elapsed_seconds = time.time() - start_time

        # 最終結果表示
        print("\n" + "=" * 80)
        print("🎉 差分データ取得完了!")
        print("=" * 80)
        print(f"📊 取得週数: {result['total_weeks']}週")
        print(f"📊 DB保存件数: {result['total_saved']:,}件")
        print(f"⏱️  所要時間: {elapsed_seconds:.1f}秒")
        print("=" * 80)

        return {
            "total_weeks": result["total_weeks"],
            "total_saved": result["total_saved"],
            "elapsed_seconds": elapsed_seconds,
            "start_date": start_date.date(),
            "end_date": end_date.date(),
        }

    def _fetch_and_save_loop(
        self,
        start_date: datetime,
        end_date: datetime,
        wait_seconds: int,
        save_progress: bool,
    ) -> dict:
        """週単位で分割取得してDBに保存（内部メソッド）

        Args:
            start_date: 取得開始日
            end_date: 取得終了日
            wait_seconds: 各週取得後の待機秒数
            save_progress: 進捗保存するか

        Returns:
            dict: 実行結果
                - total_weeks: 取得週数
                - total_saved: 保存件数

        Raises:
            Exception: API取得エラーまたはDB保存エラー
        """
        current_date = start_date
        week_count = 0
        total_saved = 0

        print("\n" + "=" * 80)
        print("📥 データ取得開始")
        print("=" * 80)

        try:
            while current_date <= end_date:
                week_count += 1
                week_end = min(current_date + timedelta(days=6), end_date)

                print(f"\n📅 Week {week_count}: {current_date.date()} 〜 {week_end.date()}")

                # API取得（応答時間計測）
                request_start = time.time()
                print("  🔄 API取得中...")

                try:
                    df = self.api_repo.fetch_daily_quotes_range(
                        start_date=current_date,
                        end_date=week_end,
                    )
                    request_elapsed = time.time() - request_start
                    print(f"  ✅ API取得成功: {len(df)}件 ({request_elapsed:.2f}秒)")

                except Exception as e:
                    print(f"  ❌ API取得エラー: {e}")
                    # エラー時は進捗を保存して終了
                    if save_progress:
                        self._save_progress((current_date - timedelta(days=1)).strftime("%Y-%m-%d"))
                    raise

                # DB保存
                if len(df) > 0:
                    print("  🔄 DB保存中（UPSERT）...")
                    save_start = time.time()
                    saved = self.db_repo.bulk_upsert(df)
                    save_elapsed = time.time() - save_start
                    total_saved += saved
                    print(f"  ✅ DB保存完了: {saved}件 ({save_elapsed:.2f}秒)")

                # 進捗保存
                if save_progress:
                    self._save_progress(week_end.strftime("%Y-%m-%d"))

                # 累計表示
                print(f"  📊 累計: {total_saved}件保存済み")

                # 次の週へ
                current_date = week_end + timedelta(days=1)

                # 最後の週以外は待機
                if current_date <= end_date:
                    print(f"  ⏳ {wait_seconds}秒待機中... (rate limit対策)")
                    time.sleep(wait_seconds)

        except Exception as e:
            self.session.rollback()
            print(f"\n❌ エラー発生: {e}")
            import traceback

            traceback.print_exc()
            raise

        return {
            "total_weeks": week_count,
            "total_saved": total_saved,
        }

    def _save_progress(self, last_completed_date: str) -> None:
        """進捗を保存する

        Args:
            last_completed_date: 最後に完了した日付（YYYY-MM-DD形式）
        """
        # ディレクトリが存在しない場合は作成
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.progress_file, "w") as f:
            json.dump({"last_completed_date": last_completed_date}, f)

    def _load_progress(self) -> str | None:
        """進捗ファイルから最後に完了した日付を読み込む

        Returns:
            str | None: 最後に完了した日付（YYYY-MM-DD形式）。
                ファイルが存在しない場合はNone。
        """
        if not self.progress_file.exists():
            return None

        with open(self.progress_file) as f:
            data = json.load(f)
            return data.get("last_completed_date")
