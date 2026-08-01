"""信用取引週末残高データ取得UseCase

J-Quants APIから信用取引週末残高データを取得してDBに保存するビジネスロジック。
"""

import time
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.infrastructure.jquants.margin_repository import JQuantsMarginRepository
from app.infrastructure.persistence.margin_trading_balance_repository import (
    MarginTradingBalanceRepository,
)


class FetchMarginInterestUseCase:
    """信用取引週末残高データ取得UseCase

    J-Quants APIから信用取引週末残高データを取得してDBに保存する。
    日単位分割、差分取得に対応。

    使用例:
        >>> usecase = FetchMarginInterestUseCase(session)
        >>> # 全件取得
        >>> usecase.execute_full(
        ...     start_date=datetime(2016, 7, 24),
        ...     end_date=datetime.now(),
        ...     wait_seconds=1
        ... )
        >>> # 差分取得
        >>> usecase.execute_incremental(wait_seconds=1)
    """

    def __init__(
        self,
        session: Session,
        api_repository: JQuantsMarginRepository | None = None,
        db_repository: MarginTradingBalanceRepository | None = None,
    ):
        """初期化

        Args:
            session: SQLAlchemyの同期セッション
            api_repository: J-Quants API リポジトリ（省略時は自動生成）
            db_repository: DB永続化リポジトリ（省略時は自動生成）
        """
        self.session = session
        self.api_repo = api_repository or JQuantsMarginRepository()
        self.db_repo = db_repository or MarginTradingBalanceRepository(session)

    def execute_full(
        self,
        start_date: datetime,
        end_date: datetime,
        wait_seconds: float = 1.0,
    ) -> dict:
        """全件取得モード（期間指定）

        指定期間の信用取引週末残高データを全件取得してDBに保存。
        日単位でループ、レート制限対策として各日取得後に待機。

        Note:
            週末データは通常金曜日に存在するが、祝日・JPX停止等でずれる可能性があるため、
            全日付をループして確実に取得する設計。初回全量取得は約1時間（10年分）。

        Args:
            start_date: 取得開始日
            end_date: 取得終了日
            wait_seconds: 各日取得後の待機秒数（デフォルト: 1.0秒）

        Returns:
            dict: 実行結果
                - total_weeks: 取得日数（互換性のため変数名はweeks）
                - total_saved: 保存件数
                - elapsed_seconds: 所要時間（秒）

        Example:
            >>> usecase = FetchMarginInterestUseCase(session)
            >>> result = usecase.execute_full(
            ...     start_date=datetime(2016, 7, 24),
            ...     end_date=datetime.now(),
            ...     wait_seconds=1
            ... )
            >>> print(result['total_saved'])
            1827812  # 約4257銘柄 × 約430週分
        """
        print("=" * 80)
        print("🔄 信用取引週末残高データ取得開始（全件取得モード）")
        print("=" * 80)

        # 開始時刻を記録・表示
        start_time = time.time()
        start_datetime = datetime.now()
        print(f"🕐 開始時刻: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"📅 取得期間: {start_date.date()} 〜 {end_date.date()}")
        total_days = (end_date - start_date).days
        print(f"📊 取得日数: {total_days}日（約{total_days // 7}週間）")
        print(f"⏱️  待機時間: {wait_seconds}秒/日")
        print("")

        # 実行
        result = self._fetch_and_save_loop(
            start_date=start_date,
            end_date=end_date,
            wait_seconds=wait_seconds,
        )
        elapsed_seconds = time.time() - start_time

        # 最終結果表示
        print("\n" + "=" * 80)
        print("🎉 信用取引週末残高データ取得完了!")
        print("=" * 80)
        print(f"📊 取得日数: {result['total_weeks']}日")
        print(f"📊 DB保存件数: {result['total_saved']:,}件")
        print(f"⏱️  所要時間: {elapsed_seconds:.1f}秒")
        print("=" * 80)

        return {
            "total_weeks": result["total_weeks"],
            "total_saved": result["total_saved"],
            "elapsed_seconds": elapsed_seconds,
        }

    def execute_incremental(self, wait_seconds: float = 1.0) -> dict:
        """差分取得モード

        DBの最新週末日付から現在までの差分データを取得。

        Args:
            wait_seconds: 各週取得後の待機秒数（デフォルト: 1.0秒）

        Returns:
            dict: 実行結果
                - total_weeks: 取得週数
                - total_saved: 保存件数
                - elapsed_seconds: 所要時間（秒）
                - start_date: 取得開始日
                - end_date: 取得終了日

        Example:
            >>> usecase = FetchMarginInterestUseCase(session)
            >>> result = usecase.execute_incremental()
            >>> print(result['total_saved'])
            4444  # 1週分
        """
        print("=" * 80)
        print("🔄 信用取引週末残高データ取得開始（差分取得モード）")
        print("=" * 80)

        # DBから最新週末日付を取得
        latest_date = self.db_repo.get_latest_date()

        if latest_date:
            # 最新日付の翌日から取得
            start_date = datetime.combine(latest_date, datetime.min.time()) + timedelta(days=1)
            print(f"📂 DB最新週末日付: {latest_date}")
            print(f"📅 取得開始日: {start_date.date()}")
        else:
            # DBが空の場合はデフォルト開始日（Standardプラン: 現在から10年前）
            ten_years_ago = datetime.now() - timedelta(days=365 * 10)
            start_date = ten_years_ago
            print("⚠️  DBにデータが存在しません。初回取得を開始します。")
            print(f"📅 取得開始日: {start_date.date()} （Standardプラン: 現在から10年前）")

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
        print(f"📊 取得日数: {total_days}日（約{total_days // 7}週間）")
        print("")

        # 実行
        start_time = time.time()
        result = self._fetch_and_save_loop(
            start_date=start_date,
            end_date=end_date,
            wait_seconds=wait_seconds,
        )
        elapsed_seconds = time.time() - start_time

        # 最終結果表示
        print("\n" + "=" * 80)
        print("🎉 信用取引週末残高データ取得完了!")
        print("=" * 80)
        print(f"📊 取得日数: {result['total_weeks']}日")
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
        wait_seconds: float,
    ) -> dict:
        """日単位で取得・保存するループ処理

        信用取引週末残高APIは、全銘柄取得の場合は日単位（dateパラメータ）のみ対応。
        週末（金曜日）のみデータが存在するが、全日付を試行する。

        Args:
            start_date: 取得開始日
            end_date: 取得終了日
            wait_seconds: 各日取得後の待機秒数

        Returns:
            dict: 実行結果
                - total_weeks: 取得週数（実際は取得日数）
                - total_saved: 保存件数
        """
        total_saved = 0
        total_days = 0

        # 日単位でループ
        current_date = start_date
        while current_date <= end_date:
            total_days += 1

            # API呼び出し（stock_code=None、1日指定で全銘柄取得）
            print(f"📥 取得中... 日{total_days}: {current_date.date()}")
            fetch_start_time = time.time()
            df = self.api_repo.fetch_margin_interest_range(
                stock_code=None,  # 全銘柄
                start_date=current_date,
                end_date=current_date,  # 同じ日（1日のみ）
            )
            fetch_elapsed = time.time() - fetch_start_time

            # DB保存
            if len(df) > 0:
                save_start_time = time.time()
                saved_count = self.db_repo.bulk_upsert(df)
                save_elapsed = time.time() - save_start_time

                total_saved += saved_count
                print(
                    f"   ✅ 保存完了: {saved_count:,}件 "
                    f"(取得: {fetch_elapsed:.2f}秒, 保存: {save_elapsed:.2f}秒)"
                )
            else:
                print("   ⚠️  データなし（週末以外 or 営業日が2日以下の週）")

            # DBコミット（日ごと）
            self.session.commit()

            # レート制限対策：待機
            if current_date < end_date and wait_seconds > 0:
                time.sleep(wait_seconds)

            # 次の日へ
            current_date = current_date + timedelta(days=1)

        return {
            "total_weeks": total_days,  # 互換性のため変数名はそのまま
            "total_saved": total_saved,
        }
