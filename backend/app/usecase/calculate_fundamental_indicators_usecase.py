"""ファンダメンタル指標計算UseCase

株価データと財務データを組み合わせて、ファンダメンタル指標（20項目）を計算する。

主な機能:
- Point-in-Time設計（未来情報混入を防止）
- 株式分割の自動検出・調整
- 会計基準変更対応（YoY計算可能）
- 予想データ活用（実績PER + 予想PER 2種類）

詳細設計: docs/ml/fundamental-indicators-design.md
"""

from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.domain.models.financial_statement import FinancialStatement
from app.domain.models.stock_price import StockPriceDaily
from app.infrastructure.persistence.fundamental_indicator_repository import (
    FundamentalIndicatorRepository,
)


class CalculateFundamentalIndicatorsUseCase:
    """ファンダメンタル指標計算UseCase

    株価データと財務データを組み合わせて、バリュエーション・収益性・成長性・
    安全性・配当の5カテゴリ、計20項目の指標を計算する。

    使用例:
        >>> usecase = CalculateFundamentalIndicatorsUseCase(session)
        >>> saved = usecase.calculate_and_save(start_date, end_date)
        >>> print(saved)
        10000  # 保存件数
    """

    def __init__(self, session: Session, financial_df: pd.DataFrame | None = None):
        """初期化

        Args:
            session: SQLAlchemyの同期セッション
            financial_df: 財務データ全件（メモリキャッシュ用、約500MB）
        """
        self.session = session
        self.fundamental_repo = FundamentalIndicatorRepository(session)
        self.financial_df = financial_df  # メモリキャッシュ（Noneの場合はDBクエリ使用）

    def calculate_and_save(
        self,
        start_date: date,
        end_date: date,
        stock_codes: list[str] | None = None,
    ) -> int:
        """指定期間・指定銘柄のファンダメンタル指標を計算してDB保存

        Args:
            start_date: 計算開始日
            end_date: 計算終了日
            stock_codes: 銘柄コードリスト（Noneの場合は全銘柄）

        Returns:
            int: 保存件数

        Example:
            >>> usecase = CalculateFundamentalIndicatorsUseCase(session)
            >>> saved = usecase.calculate_and_save(
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 12, 31),
            ...     stock_codes=["72030", "67580"],
            ... )
            >>> print(saved)
            500
        """
        # 1. 営業日リストを取得
        trading_dates = self._get_trading_dates(start_date, end_date)
        if not trading_dates:
            print("  ⚠️  指定期間に営業日が見つかりません")
            return 0

        print(f"  📅 計算期間: {start_date} 〜 {end_date} ({len(trading_dates)}営業日)")

        # 2. 銘柄リストを取得
        if stock_codes is None:
            stock_codes = self._get_all_stock_codes()
        print(f"  📊 対象銘柄数: {len(stock_codes)}")

        # 3. 各営業日ごとに全銘柄の指標を計算（最適化版: 日付ごとにバッチクエリ）
        total_saved = 0
        from datetime import datetime
        start_time = datetime.now()

        for i, target_date in enumerate(trading_dates, 1):
            if i % 10 == 0 or i == 1:
                # 経過時間と残り時間を計算
                elapsed = datetime.now() - start_time
                if i > 1:
                    avg_time_per_day = elapsed.total_seconds() / (i - 1)
                    remaining_days = len(trading_dates) - i
                    eta_seconds = avg_time_per_day * remaining_days
                    eta_hours = int(eta_seconds // 3600)
                    eta_minutes = int((eta_seconds % 3600) // 60)
                    eta_str = f"残り約{eta_hours}時間{eta_minutes}分"
                else:
                    eta_str = "計算中..."

                print(f"  ⏳ 計算中: {i}/{len(trading_dates)} ({target_date}) - {eta_str}")

            # 3-1. この日付の全銘柄のデータを一括取得（バッチクエリ）
            prices_map = self._get_all_stock_prices_for_date(target_date, stock_codes)
            fy_fins_map = self._get_all_fy_financial_data_for_date(target_date, stock_codes)
            current_fins_map = self._get_all_latest_financial_data_for_date(target_date, stock_codes)
            previous_fins_map = self._get_all_previous_year_financial_data_for_date(
                target_date, stock_codes, current_fins_map
            )
            forecasts_map = self._get_all_latest_forecast_data_for_date(target_date, stock_codes)

            # 3-1-2. 株式分割検出用の株価を一括取得
            split_detection_prices_map = self._get_all_stock_prices_for_split_detection(
                current_fins_map
            )

            # 3-2. メモリ上で計算
            day_indicators = []
            for stock_code in stock_codes:
                indicators = self._calculate_indicators_from_data(
                    stock_code=stock_code,
                    target_date=target_date,
                    price_today=prices_map.get(stock_code),
                    fy_fin=fy_fins_map.get(stock_code),
                    current_fin=current_fins_map.get(stock_code),
                    previous_fin=previous_fins_map.get(stock_code),
                    forecast=forecasts_map.get(stock_code),
                    split_detection_prices=split_detection_prices_map,
                )
                if indicators:
                    day_indicators.append(indicators)

            # 3-3. この日付分をDB保存（1日ごとにcommit）
            if day_indicators:
                df = pd.DataFrame(day_indicators)
                saved = self.fundamental_repo.bulk_upsert(df)
                self.session.commit()
                total_saved += saved

        # 4. 完了メッセージ
        if total_saved == 0:
            print("  ⚠️  計算結果がありません（財務データまたは株価データ不足）")

        print(f"  ✅ 計算完了・DB保存完了: {total_saved:,}件")
        return total_saved

    def _calculate_indicators_for_stock_and_date(
        self, stock_code: str, target_date: date
    ) -> dict | None:
        """指定銘柄・指定日のファンダメンタル指標を計算

        Args:
            stock_code: 銘柄コード
            target_date: 計算対象日

        Returns:
            dict | None: 計算結果（20項目 + stock_code, date）。
                         データ不足の場合はNone。
        """
        # === ステップ1: データ取得 ===

        # 1-1. 株価データ
        price_today = self._get_stock_price(stock_code, target_date)
        if not price_today:
            return None  # 株価データがない（非営業日、上場廃止等）

        # 1-2. FY実績データ（実績PER、PBR、PSR、PCFR用）
        fy_fin = self._get_latest_fy_financial_data(stock_code, target_date)
        # fy_finがNoneでも予想PER等は計算可能

        # 1-3. 直近四半期データ（予想PER、ROE/ROA等用）
        current_fin = self._get_latest_financial_data(stock_code, target_date)
        if not current_fin:
            return None  # 財務データがない（新規上場直後、未発表等）

        # 1-4. 前年同期の財務データ（YoY成長率用）
        previous_fin = self._get_same_quarter_previous_year(stock_code, current_fin)
        # previous_finがNoneでもYoY以外は計算可能

        # 1-5. 最新の予想データ（決算短信 + 予想修正）
        f_eps, nx_f_eps, f_div_ann, nx_f_div_ann = self._get_latest_forecast_data(
            stock_code, target_date
        )

        # === ステップ2: 株式分割の検出と調整 ===

        # 2-1. 直近の分割検出（時価総額チェック）
        price_at_fin = self._get_stock_price(stock_code, current_fin.disc_date)
        split_ratio_recent = self._detect_recent_split(
            price_at_fin, price_today, current_fin.sh_out_fy
        )

        # 2-2. 前年同期との分割検出（発行済株式数チェック）
        split_ratio_yoy = 1.0
        if previous_fin and previous_fin.sh_out_fy and current_fin.sh_out_fy:
            ratio = float(current_fin.sh_out_fy) / float(previous_fin.sh_out_fy)
            if 1.5 <= ratio <= 20:
                split_ratio_yoy = ratio

        # === ステップ3: バリュエーション指標 ===

        # 3-1. PER（実績、FY実績EPS、分割調整済み）
        if fy_fin and fy_fin.eps:
            adjusted_eps = float(fy_fin.eps) / split_ratio_recent
            per = (
                float(price_today.close) / adjusted_eps
                if adjusted_eps > 0
                else None
            )
        else:
            per = None

        # 3-2. PBR（FY実績BPS、分割調整済み）
        if fy_fin and fy_fin.bps:
            adjusted_bps = float(fy_fin.bps) / split_ratio_recent
            pbr = (
                float(price_today.close) / adjusted_bps
                if adjusted_bps > 0
                else None
            )
        else:
            pbr = None

        # 3-3. PSR（時価総額ベース、FY実績売上高）
        if fy_fin and fy_fin.sh_out_fy:
            # 時価総額（円） = 株価（円） × 発行済株式数（株）
            # 注: sh_out_fyは株単位で格納されている（千株ではない）
            market_cap = float(price_today.close) * float(fy_fin.sh_out_fy)
            psr = (
                market_cap / float(fy_fin.sales)
                if fy_fin.sales and fy_fin.sales > 0
                else None
            )
        else:
            market_cap = None
            psr = None

        # 3-4. PCFR（時価総額ベース、FY実績営業CF）
        if market_cap and fy_fin and fy_fin.cfo:
            pcfr = market_cap / float(fy_fin.cfo) if fy_fin.cfo > 0 else None
        else:
            pcfr = None

        # 3-5. 予想PER（当期、分割調整済み）
        adjusted_f_eps = f_eps / split_ratio_recent if f_eps else None
        forward_per_fy = (
            float(price_today.close) / adjusted_f_eps
            if adjusted_f_eps and adjusted_f_eps > 0
            else None
        )

        # 3-6. 予想PER（翌期、分割調整済み）
        adjusted_nx_f_eps = nx_f_eps / split_ratio_recent if nx_f_eps else None
        forward_per_nx = (
            float(price_today.close) / adjusted_nx_f_eps
            if adjusted_nx_f_eps and adjusted_nx_f_eps > 0
            else None
        )

        # === ステップ4: 収益性指標 ===

        roe = float(current_fin.np) / float(current_fin.eq) if current_fin.np and current_fin.eq and current_fin.eq > 0 else None
        roa = float(current_fin.np) / float(current_fin.ta) if current_fin.np and current_fin.ta and current_fin.ta > 0 else None
        operating_margin = (
            float(current_fin.op) / float(current_fin.sales)
            if current_fin.op and current_fin.sales and current_fin.sales > 0
            else None
        )
        net_margin = (
            float(current_fin.np) / float(current_fin.sales)
            if current_fin.np and current_fin.sales and current_fin.sales > 0
            else None
        )

        # === ステップ5: 成長性指標（YoY、分割調整済み） ===

        if previous_fin:
            # 過去の値を分割係数で調整
            adj_prev_sales = float(previous_fin.sales) if previous_fin.sales else None
            adj_prev_op = float(previous_fin.op) if previous_fin.op else None
            adj_prev_np = float(previous_fin.np) if previous_fin.np else None
            adj_prev_eps = (
                float(previous_fin.eps) / split_ratio_yoy if previous_fin.eps else None
            )
            adj_prev_cfo = float(previous_fin.cfo) if previous_fin.cfo else None

            sales_growth_yoy = (
                (float(current_fin.sales) - adj_prev_sales) / adj_prev_sales
                if current_fin.sales and adj_prev_sales and adj_prev_sales > 0
                else None
            )
            op_growth_yoy = (
                (float(current_fin.op) - adj_prev_op) / adj_prev_op
                if current_fin.op and adj_prev_op and adj_prev_op != 0
                else None
            )
            np_growth_yoy = (
                (float(current_fin.np) - adj_prev_np) / adj_prev_np
                if current_fin.np and adj_prev_np and adj_prev_np != 0
                else None
            )
            eps_growth_yoy = (
                (float(current_fin.eps) - adj_prev_eps) / adj_prev_eps
                if current_fin.eps and adj_prev_eps and adj_prev_eps != 0
                else None
            )
            cfo_growth_yoy = (
                (float(current_fin.cfo) - adj_prev_cfo) / adj_prev_cfo
                if current_fin.cfo and adj_prev_cfo and adj_prev_cfo != 0
                else None
            )
        else:
            sales_growth_yoy = None
            op_growth_yoy = None
            np_growth_yoy = None
            eps_growth_yoy = None
            cfo_growth_yoy = None

        # === ステップ6: 安全性指標 ===

        equity_ratio = (
            float(current_fin.eq) / float(current_fin.ta)
            if current_fin.eq and current_fin.ta and current_fin.ta > 0
            else None
        )

        # === ステップ7: 配当指標 ===

        # 7-1. 配当利回り（実績、FY実績配当、分割調整済み）
        if fy_fin and fy_fin.div_ann:
            adjusted_div_ann = float(fy_fin.div_ann) / split_ratio_recent
            dividend_yield = (
                adjusted_div_ann / float(price_today.close)
                if price_today.close > 0
                else None
            )
        else:
            dividend_yield = None

        # 7-2. 配当性向（実績、FY実績）
        payout_ratio = (
            float(fy_fin.payout_ratio_ann)
            if fy_fin and fy_fin.payout_ratio_ann
            else None
        )

        # 7-3. 予想配当利回り（当期、分割調整済み）
        adjusted_f_div_ann = f_div_ann / split_ratio_recent if f_div_ann else None
        forward_div_yield_fy = (
            adjusted_f_div_ann / float(price_today.close)
            if adjusted_f_div_ann and price_today.close > 0
            else None
        )

        # 7-4. 予想配当利回り（翌期、分割調整済み）
        adjusted_nx_f_div_ann = nx_f_div_ann / split_ratio_recent if nx_f_div_ann else None
        forward_div_yield_nx = (
            adjusted_nx_f_div_ann / float(price_today.close)
            if adjusted_nx_f_div_ann and price_today.close > 0
            else None
        )

        # === ステップ8: 異常値フィルタリング ===

        indicators = {
            "stock_code": stock_code,
            "date": target_date,
            # バリュエーション
            "per": per,
            "pbr": pbr,
            "psr": psr,
            "pcfr": pcfr,
            "forward_per_fy": forward_per_fy,
            "forward_per_nx": forward_per_nx,
            # 収益性
            "roe": roe,
            "roa": roa,
            "operating_margin": operating_margin,
            "net_margin": net_margin,
            # 成長性
            "sales_growth_yoy": sales_growth_yoy,
            "op_growth_yoy": op_growth_yoy,
            "np_growth_yoy": np_growth_yoy,
            "eps_growth_yoy": eps_growth_yoy,
            "cfo_growth_yoy": cfo_growth_yoy,
            # 安全性
            "equity_ratio": equity_ratio,
            # 配当
            "dividend_yield": dividend_yield,
            "payout_ratio": payout_ratio,
            "forward_div_yield_fy": forward_div_yield_fy,
            "forward_div_yield_nx": forward_div_yield_nx,
        }

        indicators = self._filter_outliers(indicators)

        return indicators

    def _get_stock_price(self, stock_code: str, target_date: date) -> StockPriceDaily | None:
        """指定銘柄・指定日の株価データを取得

        Args:
            stock_code: 銘柄コード
            target_date: 日付

        Returns:
            StockPriceDaily | None: 株価データ。存在しない場合はNone。
        """
        stmt = select(StockPriceDaily).where(
            and_(
                StockPriceDaily.stock_code == stock_code,
                StockPriceDaily.date == target_date,
            )
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _get_latest_financial_data(
        self, stock_code: str, target_date: date
    ) -> FinancialStatement | None:
        """Point-in-Time設計で最新の財務データを取得

        target_date時点で「既に開示されていた最新の財務データ」を取得する。

        Args:
            stock_code: 銘柄コード
            target_date: 基準日（株価日付）

        Returns:
            FinancialStatement | None: 財務データ。存在しない場合はNone。

        Note:
            - 開示日 < 株価日付（翌営業日から使用）
            - 会計期間終了日が最新のものを優先
            - 開示日が最新のものを優先
        """
        # 実績データの優先順位（連結優先）
        preferred_types = [
            # 通期決算（最優先）
            "%FinancialStatements_Consolidated_%",
            # 非連結（フォールバック）
            "%FinancialStatements_NonConsolidated_%",
        ]

        # 会社予想・修正を除外
        excluded_types = [
            "EarnForecastRevision",
            "DividendForecastRevision",
            "REITEarnForecastRevision",
            "REITDividendForecastRevision",
        ]

        stmt = (
            select(FinancialStatement)
            .where(
                and_(
                    FinancialStatement.stock_code == stock_code,
                    FinancialStatement.disc_date < target_date,  # Point-in-Time
                    or_(
                        *[
                            FinancialStatement.type_of_document.like(pattern)
                            for pattern in preferred_types
                        ]
                    ),
                    ~FinancialStatement.type_of_document.in_(excluded_types),
                )
            )
            .order_by(
                FinancialStatement.cur_per_en.desc().nulls_last(),  # 会計期間終了日が最新
                FinancialStatement.disc_date.desc(),  # 開示日が最新
            )
            .limit(1)
        )

        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _get_latest_fy_financial_data(
        self, stock_code: str, target_date: date
    ) -> FinancialStatement | None:
        """Point-in-Time設計で直近のFY（通期）実績データを取得

        実績PER計算用。証券会社と同じ計算方法。

        Args:
            stock_code: 銘柄コード
            target_date: 基準日（株価日付）

        Returns:
            FinancialStatement | None: FY実績データ。存在しない場合はNone。

        Note:
            - cur_per_type == 'FY' のみ
            - 開示日 < 株価日付（翌営業日から使用）
            - 開示日が最新のものを優先
        """
        preferred_types = [
            "%FinancialStatements_Consolidated_%",
            "%FinancialStatements_NonConsolidated_%",
        ]

        excluded_types = [
            "EarnForecastRevision",
            "DividendForecastRevision",
            "REITEarnForecastRevision",
            "REITDividendForecastRevision",
        ]

        stmt = (
            select(FinancialStatement)
            .where(
                and_(
                    FinancialStatement.stock_code == stock_code,
                    FinancialStatement.disc_date < target_date,  # Point-in-Time
                    FinancialStatement.cur_per_type == "FY",  # FYのみ
                    or_(
                        *[
                            FinancialStatement.type_of_document.like(pattern)
                            for pattern in preferred_types
                        ]
                    ),
                    ~FinancialStatement.type_of_document.in_(excluded_types),
                )
            )
            .order_by(
                FinancialStatement.disc_date.desc(),  # 開示日が最新
            )
            .limit(1)
        )

        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _get_same_quarter_previous_year(
        self, stock_code: str, current_fin: FinancialStatement
    ) -> FinancialStatement | None:
        """前年同期（同じ四半期）の財務データを取得

        YoY成長率計算用。同じ累計期間同士を比較する。

        Args:
            stock_code: 銘柄コード
            current_fin: 今期の財務データ

        Returns:
            FinancialStatement | None: 前年同期データ。存在しない場合はNone。

        Note:
            - cur_per_type（1Q/2Q/3Q/FY）が同じもの
            - 会計期間終了日が前年の同時期（±15日）
        """
        if not current_fin.cur_per_type or not current_fin.cur_per_en:
            return None

        # 前年の同じ四半期の会計期間終了日を計算（うるう年対応）
        try:
            prev_year_end = current_fin.cur_per_en.replace(
                year=current_fin.cur_per_en.year - 1
            )
        except ValueError:
            # 2/29（うるう年）→ 前年2/28（平年）に変換
            prev_year_end = current_fin.cur_per_en.replace(
                year=current_fin.cur_per_en.year - 1, day=28
            )

        preferred_types = [
            "%FinancialStatements_Consolidated_%",
            "%FinancialStatements_NonConsolidated_%",
        ]

        excluded_types = [
            "EarnForecastRevision",
            "DividendForecastRevision",
            "REITEarnForecastRevision",
            "REITDividendForecastRevision",
        ]

        # 同じ四半期（cur_per_type）かつ前年のデータを検索
        stmt = (
            select(FinancialStatement)
            .where(
                and_(
                    FinancialStatement.stock_code == stock_code,
                    FinancialStatement.cur_per_type == current_fin.cur_per_type,  # 同じ四半期
                    FinancialStatement.cur_per_en.between(
                        prev_year_end - timedelta(days=15),  # ±15日の許容範囲
                        prev_year_end + timedelta(days=15),
                    ),
                    or_(
                        *[
                            FinancialStatement.type_of_document.like(pattern)
                            for pattern in preferred_types
                        ]
                    ),
                    ~FinancialStatement.type_of_document.in_(excluded_types),
                )
            )
            .order_by(FinancialStatement.disc_date.desc())
            .limit(1)
        )

        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _get_latest_forecast_data(
        self, stock_code: str, target_date: date
    ) -> tuple[float | None, float | None, float | None, float | None]:
        """最新の予想データを取得（決算短信 + 予想修正）

        Args:
            stock_code: 銘柄コード
            target_date: 基準日

        Returns:
            tuple: (f_eps, nx_f_eps, f_div_ann, nx_f_div_ann)
                - f_eps: 当期EPS予想
                - nx_f_eps: 翌期EPS予想
                - f_div_ann: 当期年間配当予想
                - nx_f_div_ann: 翌期年間配当予想
        """
        # 1. 決算短信から予想データを取得
        fin_stmt = self._get_latest_financial_data(stock_code, target_date)
        f_eps = float(fin_stmt.f_eps) if fin_stmt and fin_stmt.f_eps else None
        nx_f_eps = float(fin_stmt.nx_f_eps) if fin_stmt and fin_stmt.nx_f_eps else None
        f_div_ann = float(fin_stmt.f_div_ann) if fin_stmt and fin_stmt.f_div_ann else None
        nx_f_div_ann = (
            float(fin_stmt.nx_f_div_ann) if fin_stmt and fin_stmt.nx_f_div_ann else None
        )

        # 2. 予想修正から最新の予想データを取得
        forecast_revision = self._get_latest_forecast_revision(stock_code, target_date)

        # 3. disc_dateが最新のものを採用
        if forecast_revision and fin_stmt and forecast_revision.disc_date > fin_stmt.disc_date:
            # 予想修正の方が新しい → 予想修正の値を優先（NULLでなければ）
            f_eps = (
                float(forecast_revision.f_eps)
                if forecast_revision.f_eps
                else f_eps
            )
            nx_f_eps = (
                float(forecast_revision.nx_f_eps)
                if forecast_revision.nx_f_eps
                else nx_f_eps
            )
            f_div_ann = (
                float(forecast_revision.f_div_ann)
                if forecast_revision.f_div_ann
                else f_div_ann
            )
            nx_f_div_ann = (
                float(forecast_revision.nx_f_div_ann)
                if forecast_revision.nx_f_div_ann
                else nx_f_div_ann
            )

        return f_eps, nx_f_eps, f_div_ann, nx_f_div_ann

    def _get_latest_forecast_revision(
        self, stock_code: str, target_date: date
    ) -> FinancialStatement | None:
        """最新の予想修正データを取得

        Args:
            stock_code: 銘柄コード
            target_date: 基準日

        Returns:
            FinancialStatement | None: 予想修正データ。存在しない場合はNone。
        """
        revision_types = [
            "EarnForecastRevision",
            "DividendForecastRevision",
            "REITEarnForecastRevision",
            "REITDividendForecastRevision",
        ]

        stmt = (
            select(FinancialStatement)
            .where(
                and_(
                    FinancialStatement.stock_code == stock_code,
                    FinancialStatement.disc_date < target_date,
                    FinancialStatement.type_of_document.in_(revision_types),
                )
            )
            .order_by(FinancialStatement.disc_date.desc())
            .limit(1)
        )

        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _detect_recent_split(
        self,
        price_at_fin: StockPriceDaily | None,
        price_today: StockPriceDaily,
        sh_out_fy: Decimal | None,
    ) -> float:
        """直近の株式分割を検出（時価総額整合性チェック）

        Args:
            price_at_fin: 財務データ発表日時点の株価
            price_today: 今日の株価
            sh_out_fy: 発行済株式数（千株）

        Returns:
            float: 分割比率（1.0 = 分割なし、5.0 = 1→5分割）

        Note:
            - 時価総額の整合性チェックで分割を検出
            - 妥当な分割比率（1.5〜20倍）のみ採用
        """
        if not price_at_fin or not sh_out_fy or sh_out_fy == 0:
            return 1.0  # データ不足、分割なしとみなす

        market_cap_at_fin = float(price_at_fin.close) * float(sh_out_fy)
        market_cap_today_naive = float(price_today.close) * float(sh_out_fy)

        if market_cap_today_naive == 0:
            return 1.0

        split_ratio = market_cap_at_fin / market_cap_today_naive

        # 一般的な分割比率（1:2, 1:3, 1:5, 1:10等）
        if 1.5 <= split_ratio <= 20:
            return split_ratio
        else:
            # 比率が異常 → 分割ではなく、業績変化や株価急変とみなす
            return 1.0

    def _filter_outliers(self, indicators: dict) -> dict:
        """異常値をフィルタリング（株式分割の検出漏れ等）

        Args:
            indicators: 計算済み指標

        Returns:
            dict: フィルタリング後の指標
        """
        # PERの妥当な範囲（-100 〜 1000）
        if indicators["per"] is not None:
            if indicators["per"] < -100 or indicators["per"] > 1000:
                indicators["per"] = None

        # PBRの妥当な範囲（0 〜 100）
        if indicators["pbr"] is not None:
            if indicators["pbr"] < 0 or indicators["pbr"] > 100:
                indicators["pbr"] = None

        # YoY成長率の妥当な範囲（-100% 〜 +1000%）
        growth_fields = ["sales_growth_yoy", "op_growth_yoy", "np_growth_yoy", "eps_growth_yoy", "cfo_growth_yoy"]
        for field in growth_fields:
            if indicators[field] is not None:
                if indicators[field] < -1.0 or indicators[field] > 10.0:
                    indicators[field] = None

        return indicators

    def _get_trading_dates(self, start_date: date, end_date: date) -> list[date]:
        """指定期間の営業日リストを取得

        Args:
            start_date: 開始日
            end_date: 終了日

        Returns:
            list[date]: 営業日リスト（昇順）
        """
        stmt = (
            select(StockPriceDaily.date)
            .where(
                and_(
                    StockPriceDaily.date >= start_date,
                    StockPriceDaily.date <= end_date,
                )
            )
            .distinct()
            .order_by(StockPriceDaily.date)
        )

        result = self.session.execute(stmt)
        return [row[0] for row in result.all()]

    def _get_all_stock_codes(self) -> list[str]:
        """全銘柄コードを取得

        Returns:
            list[str]: 銘柄コードリスト
        """
        stmt = select(StockPriceDaily.stock_code).distinct()

        result = self.session.execute(stmt)
        return [row[0] for row in result.all()]

    # ===================================================================
    # バッチクエリ用メソッド（最適化版）
    # ===================================================================

    def _get_all_stock_prices_for_date(
        self, target_date: date, stock_codes: list[str]
    ) -> dict[str, StockPriceDaily]:
        """指定日の全銘柄の株価を一括取得

        Args:
            target_date: 対象日付
            stock_codes: 銘柄コードリスト

        Returns:
            dict[str, StockPriceDaily]: 銘柄コード → 株価データのマップ
        """
        stmt = select(StockPriceDaily).where(
            and_(
                StockPriceDaily.date == target_date,
                StockPriceDaily.stock_code.in_(stock_codes),
            )
        )

        result = self.session.execute(stmt)
        prices = result.scalars().all()

        # 銘柄コードをキーにした辞書に変換
        return {price.stock_code: price for price in prices}

    def _get_all_fy_financial_data_for_date(
        self, target_date: date, stock_codes: list[str]
    ) -> dict[str, FinancialStatement]:
        """指定日時点での全銘柄のFY実績データを一括取得

        Args:
            target_date: 基準日（株価日付）
            stock_codes: 銘柄コードリスト

        Returns:
            dict[str, FinancialStatement]: 銘柄コード → FYデータのマップ
        """
        # メモリキャッシュを使う場合
        if self.financial_df is not None:
            # pandasでフィルタリング（超高速）
            df_filtered = self.financial_df[
                (self.financial_df["stock_code"].isin(stock_codes))
                & (self.financial_df["disc_date"] < target_date)
                & (self.financial_df["cur_per_type"] == "FY")
                & (
                    self.financial_df["type_of_document"].str.contains(
                        "FinancialStatements_Consolidated_", na=False
                    )
                    | self.financial_df["type_of_document"].str.contains(
                        "FinancialStatements_NonConsolidated_", na=False
                    )
                )
                & (
                    ~self.financial_df["type_of_document"].isin(
                        [
                            "EarnForecastRevision",
                            "DividendForecastRevision",
                            "REITEarnForecastRevision",
                            "REITDividendForecastRevision",
                        ]
                    )
                )
            ]

            # disc_dateでソート（最新が先頭）
            df_sorted = df_filtered.sort_values("disc_date", ascending=False)

            # 銘柄ごとに最初の1件のみ取得
            fy_fins_map = {}
            for _, row in df_sorted.iterrows():
                stock_code = row["stock_code"]
                if stock_code not in fy_fins_map:
                    # DataFrameの行をFinancialStatementオブジェクトに変換
                    fin = self._row_to_financial_statement(row)
                    fy_fins_map[stock_code] = fin

            return fy_fins_map

        # DBクエリ使用（後方互換性）
        preferred_types = [
            "%FinancialStatements_Consolidated_%",
            "%FinancialStatements_NonConsolidated_%",
        ]

        excluded_types = [
            "EarnForecastRevision",
            "DividendForecastRevision",
            "REITEarnForecastRevision",
            "REITDividendForecastRevision",
        ]

        stmt = (
            select(FinancialStatement)
            .where(
                and_(
                    FinancialStatement.stock_code.in_(stock_codes),
                    FinancialStatement.disc_date < target_date,  # Point-in-Time
                    FinancialStatement.cur_per_type == "FY",  # FYのみ
                    or_(
                        *[
                            FinancialStatement.type_of_document.like(pattern)
                            for pattern in preferred_types
                        ]
                    ),
                    ~FinancialStatement.type_of_document.in_(excluded_types),
                )
            )
            .order_by(
                FinancialStatement.stock_code,
                FinancialStatement.disc_date.desc(),  # 開示日が最新
            )
        )

        result = self.session.execute(stmt)
        all_fy_fins = result.scalars().all()

        # 銘柄ごとに最新の1件のみを選択
        fy_fins_map = {}
        for fin in all_fy_fins:
            if fin.stock_code not in fy_fins_map:
                fy_fins_map[fin.stock_code] = fin

        return fy_fins_map

    def _get_all_latest_financial_data_for_date(
        self, target_date: date, stock_codes: list[str]
    ) -> dict[str, FinancialStatement]:
        """指定日時点での全銘柄の直近財務データを一括取得

        Args:
            target_date: 基準日（株価日付）
            stock_codes: 銘柄コードリスト

        Returns:
            dict[str, FinancialStatement]: 銘柄コード → 財務データのマップ
        """
        # メモリキャッシュを使う場合
        if self.financial_df is not None:
            # pandasでフィルタリング
            df_filtered = self.financial_df[
                (self.financial_df["stock_code"].isin(stock_codes))
                & (self.financial_df["disc_date"] < target_date)
                & (
                    self.financial_df["type_of_document"].str.contains(
                        "FinancialStatements_Consolidated_", na=False
                    )
                    | self.financial_df["type_of_document"].str.contains(
                        "FinancialStatements_NonConsolidated_", na=False
                    )
                )
                & (
                    ~self.financial_df["type_of_document"].isin(
                        [
                            "EarnForecastRevision",
                            "DividendForecastRevision",
                            "REITEarnForecastRevision",
                            "REITDividendForecastRevision",
                        ]
                    )
                )
            ]

            # cur_per_en, disc_dateでソート（最新が先頭）
            df_sorted = df_filtered.sort_values(
                by=["cur_per_en", "disc_date"], ascending=[False, False], na_position="last"
            )

            # 銘柄ごとに最初の1件のみ取得
            fins_map = {}
            for _, row in df_sorted.iterrows():
                stock_code = row["stock_code"]
                if stock_code not in fins_map:
                    fin = self._row_to_financial_statement(row)
                    fins_map[stock_code] = fin

            return fins_map

        # DBクエリ使用（後方互換性）
        preferred_types = [
            "%FinancialStatements_Consolidated_%",
            "%FinancialStatements_NonConsolidated_%",
        ]

        excluded_types = [
            "EarnForecastRevision",
            "DividendForecastRevision",
            "REITEarnForecastRevision",
            "REITDividendForecastRevision",
        ]

        stmt = (
            select(FinancialStatement)
            .where(
                and_(
                    FinancialStatement.stock_code.in_(stock_codes),
                    FinancialStatement.disc_date < target_date,  # Point-in-Time
                    or_(
                        *[
                            FinancialStatement.type_of_document.like(pattern)
                            for pattern in preferred_types
                        ]
                    ),
                    ~FinancialStatement.type_of_document.in_(excluded_types),
                )
            )
            .order_by(
                FinancialStatement.stock_code,
                FinancialStatement.cur_per_en.desc().nulls_last(),  # 会計期間終了日が最新
                FinancialStatement.disc_date.desc(),  # 開示日が最新
            )
        )

        result = self.session.execute(stmt)
        all_fins = result.scalars().all()

        # 銘柄ごとに最新の1件のみを選択（既にソート済みなので最初の1件）
        fins_map = {}
        for fin in all_fins:
            if fin.stock_code not in fins_map:
                fins_map[fin.stock_code] = fin

        return fins_map

    def _get_all_previous_year_financial_data_for_date(
        self,
        target_date: date,
        stock_codes: list[str],
        current_fins_map: dict[str, FinancialStatement],
    ) -> dict[str, FinancialStatement]:
        """全銘柄の前年同期財務データを一括取得

        Args:
            target_date: 基準日（株価日付）
            stock_codes: 銘柄コードリスト
            current_fins_map: 各銘柄の今期財務データ

        Returns:
            dict[str, FinancialStatement]: 銘柄コード → 前年同期データのマップ
        """
        # メモリキャッシュを使う場合
        if self.financial_df is not None:
            # 前年1年分のデータをフィルタ
            prev_year_start = target_date - timedelta(days=760)  # 約25ヶ月前
            prev_year_end = target_date - timedelta(days=335)  # 約11ヶ月前

            df_filtered = self.financial_df[
                (self.financial_df["stock_code"].isin(stock_codes))
                & (self.financial_df["cur_per_en"] >= prev_year_start)
                & (self.financial_df["cur_per_en"] <= prev_year_end)
                & (
                    self.financial_df["type_of_document"].str.contains(
                        "FinancialStatements_Consolidated_", na=False
                    )
                    | self.financial_df["type_of_document"].str.contains(
                        "FinancialStatements_NonConsolidated_", na=False
                    )
                )
                & (
                    ~self.financial_df["type_of_document"].isin(
                        [
                            "EarnForecastRevision",
                            "DividendForecastRevision",
                            "REITEarnForecastRevision",
                            "REITDividendForecastRevision",
                        ]
                    )
                )
            ]

            # 銘柄ごとに前年同期をマッチング
            previous_fins_map = {}
            for stock_code, current_fin in current_fins_map.items():
                if not current_fin.cur_per_type or not current_fin.cur_per_en:
                    continue

                # 前年の同じ四半期の会計期間終了日を計算（うるう年対応）
                try:
                    prev_year_en = current_fin.cur_per_en.replace(
                        year=current_fin.cur_per_en.year - 1
                    )
                except ValueError:
                    # 2/29（うるう年）→ 前年2/28（平年）に変換
                    prev_year_en = current_fin.cur_per_en.replace(
                        year=current_fin.cur_per_en.year - 1, day=28
                    )

                # 同じ銘柄・同じ四半期のデータを検索
                df_candidate = df_filtered[
                    (df_filtered["stock_code"] == stock_code)
                    & (df_filtered["cur_per_type"] == current_fin.cur_per_type)
                ]

                # ±15日の許容範囲でフィルタ
                for _, row in df_candidate.iterrows():
                    if pd.isna(row["cur_per_en"]):
                        continue

                    days_diff = abs((row["cur_per_en"] - prev_year_en).days)
                    if days_diff <= 15:
                        prev_fin = self._row_to_financial_statement(row)
                        previous_fins_map[stock_code] = prev_fin
                        break  # 最初に見つかった1件のみ

            return previous_fins_map

        # DBクエリ使用（後方互換性）
        # 前年1年分のデータを一括取得（過去13ヶ月〜25ヶ月前）
        prev_year_start = target_date - timedelta(days=760)  # 約25ヶ月前
        prev_year_end = target_date - timedelta(days=335)  # 約11ヶ月前

        preferred_types = [
            "%FinancialStatements_Consolidated_%",
            "%FinancialStatements_NonConsolidated_%",
        ]

        excluded_types = [
            "EarnForecastRevision",
            "DividendForecastRevision",
            "REITEarnForecastRevision",
            "REITDividendForecastRevision",
        ]

        stmt = (
            select(FinancialStatement)
            .where(
                and_(
                    FinancialStatement.stock_code.in_(stock_codes),
                    FinancialStatement.cur_per_en.between(prev_year_start, prev_year_end),
                    or_(
                        *[
                            FinancialStatement.type_of_document.like(pattern)
                            for pattern in preferred_types
                        ]
                    ),
                    ~FinancialStatement.type_of_document.in_(excluded_types),
                )
            )
            .order_by(
                FinancialStatement.stock_code,
                FinancialStatement.cur_per_type,
                FinancialStatement.disc_date.desc(),
            )
        )

        result = self.session.execute(stmt)
        all_prev_fins = result.scalars().all()

        # 銘柄ごとに前年同期をマッチング
        previous_fins_map = {}
        for stock_code, current_fin in current_fins_map.items():
            if not current_fin.cur_per_type or not current_fin.cur_per_en:
                continue

            # 前年の同じ四半期の会計期間終了日を計算（うるう年対応）
            try:
                prev_year_en = current_fin.cur_per_en.replace(
                    year=current_fin.cur_per_en.year - 1
                )
            except ValueError:
                # 2/29（うるう年）→ 前年2/28（平年）に変換
                prev_year_en = current_fin.cur_per_en.replace(
                    year=current_fin.cur_per_en.year - 1, day=28
                )

            # 同じ四半期（cur_per_type）かつ前年のデータを検索
            for prev_fin in all_prev_fins:
                if prev_fin.stock_code != stock_code:
                    continue
                if prev_fin.cur_per_type != current_fin.cur_per_type:
                    continue
                if not prev_fin.cur_per_en:
                    continue

                # ±15日の許容範囲
                days_diff = abs((prev_fin.cur_per_en - prev_year_en).days)
                if days_diff <= 15:
                    previous_fins_map[stock_code] = prev_fin
                    break  # 最初に見つかった1件のみ

        return previous_fins_map

    def _get_all_latest_forecast_data_for_date(
        self, target_date: date, stock_codes: list[str]
    ) -> dict[str, FinancialStatement]:
        """全銘柄の最新予想データを一括取得

        Args:
            target_date: 基準日
            stock_codes: 銘柄コードリスト

        Returns:
            dict[str, FinancialStatement]: 銘柄コード → 予想修正データのマップ
        """
        # メモリキャッシュを使う場合
        if self.financial_df is not None:
            revision_types = [
                "EarnForecastRevision",
                "DividendForecastRevision",
                "REITEarnForecastRevision",
                "REITDividendForecastRevision",
            ]

            # pandasでフィルタリング
            df_filtered = self.financial_df[
                (self.financial_df["stock_code"].isin(stock_codes))
                & (self.financial_df["disc_date"] < target_date)
                & (self.financial_df["type_of_document"].isin(revision_types))
            ]

            # disc_dateでソート（最新が先頭）
            df_sorted = df_filtered.sort_values("disc_date", ascending=False)

            # 銘柄ごとに最初の1件のみ取得
            revisions_map = {}
            for _, row in df_sorted.iterrows():
                stock_code = row["stock_code"]
                if stock_code not in revisions_map:
                    revision = self._row_to_financial_statement(row)
                    revisions_map[stock_code] = revision

            return revisions_map

        # DBクエリ使用（後方互換性）
        # 1. 予想修正データを一括取得
        revision_types = [
            "EarnForecastRevision",
            "DividendForecastRevision",
            "REITEarnForecastRevision",
            "REITDividendForecastRevision",
        ]

        stmt = (
            select(FinancialStatement)
            .where(
                and_(
                    FinancialStatement.stock_code.in_(stock_codes),
                    FinancialStatement.disc_date < target_date,
                    FinancialStatement.type_of_document.in_(revision_types),
                )
            )
            .order_by(
                FinancialStatement.stock_code,
                FinancialStatement.disc_date.desc(),
            )
        )

        result = self.session.execute(stmt)
        all_revisions = result.scalars().all()

        # 銘柄ごとに最新の予想修正を選択
        revisions_map = {}
        for revision in all_revisions:
            if revision.stock_code not in revisions_map:
                revisions_map[revision.stock_code] = revision

        # 2. 決算短信データと予想修正データを比較して、最新のものを採用
        # （決算短信データは current_fins_map から取得するため、ここでは予想修正のみを返す）
        # 実際の比較は _calculate_indicators_from_data で行う
        return revisions_map

    def _get_all_stock_prices_for_split_detection(
        self, current_fins_map: dict[str, FinancialStatement]
    ) -> dict[tuple[str, date], StockPriceDaily]:
        """株式分割検出用の株価を一括取得

        Args:
            current_fins_map: 銘柄コード → 財務データのマップ

        Returns:
            dict[tuple[str, date], StockPriceDaily]: (銘柄コード, 日付) → 株価データのマップ
        """
        # 必要な (stock_code, disc_date) のペアを収集
        needed_pairs = []
        for stock_code, fin in current_fins_map.items():
            if fin.disc_date:
                needed_pairs.append((stock_code, fin.disc_date))

        if not needed_pairs:
            return {}

        # 日付ごとにグループ化
        from collections import defaultdict
        dates_by_code = defaultdict(list)
        for stock_code, disc_date in needed_pairs:
            dates_by_code[disc_date].append(stock_code)

        # 日付ごとに一括取得
        result = {}
        for disc_date, stock_codes_list in dates_by_code.items():
            stmt = select(StockPriceDaily).where(
                and_(
                    StockPriceDaily.date == disc_date,
                    StockPriceDaily.stock_code.in_(stock_codes_list),
                )
            )
            prices = self.session.execute(stmt).scalars().all()
            for price in prices:
                result[(price.stock_code, disc_date)] = price

        return result

    def _calculate_indicators_from_data(
        self,
        stock_code: str,
        target_date: date,
        price_today: StockPriceDaily | None,
        fy_fin: FinancialStatement | None,
        current_fin: FinancialStatement | None,
        previous_fin: FinancialStatement | None,
        forecast: FinancialStatement | None,
        split_detection_prices: dict[tuple[str, date], StockPriceDaily],
    ) -> dict | None:
        """データから指標を計算（バッチ処理用）

        Args:
            stock_code: 銘柄コード
            target_date: 計算対象日
            price_today: 株価データ
            fy_fin: FY実績データ
            current_fin: 直近財務データ
            previous_fin: 前年同期データ
            forecast: 予想修正データ

        Returns:
            dict | None: 計算結果（20項目 + stock_code, date）。
                         データ不足の場合はNone。
        """
        # データ不足チェック
        if not price_today or not current_fin:
            return None

        # 予想データの取得
        # 当期予想：最新の決算短信（current_fin）を使用
        f_eps = float(current_fin.f_eps) if current_fin.f_eps else None
        f_div_ann = float(current_fin.f_div_ann) if current_fin.f_div_ann else None

        # 翌期予想：FY決算短信（fy_fin）を優先、なければcurrent_finから
        nx_f_eps = None
        nx_f_div_ann = None
        if fy_fin:
            nx_f_eps = float(fy_fin.nx_f_eps) if fy_fin.nx_f_eps else None
            nx_f_div_ann = float(fy_fin.nx_f_div_ann) if fy_fin.nx_f_div_ann else None
        # FY決算短信にない場合は current_fin から取得（フォールバック）
        if nx_f_eps is None and current_fin.nx_f_eps:
            nx_f_eps = float(current_fin.nx_f_eps)
        if nx_f_div_ann is None and current_fin.nx_f_div_ann:
            nx_f_div_ann = float(current_fin.nx_f_div_ann)

        # 予想修正の方が新しければ、そちらを優先
        if forecast and current_fin and forecast.disc_date > current_fin.disc_date:
            f_eps = float(forecast.f_eps) if forecast.f_eps else f_eps
            f_div_ann = float(forecast.f_div_ann) if forecast.f_div_ann else f_div_ann
        # 翌期予想も予想修正があれば優先（FY決算短信より新しい場合）
        if forecast and fy_fin and forecast.disc_date > fy_fin.disc_date:
            nx_f_eps = float(forecast.nx_f_eps) if forecast.nx_f_eps else nx_f_eps
            nx_f_div_ann = float(forecast.nx_f_div_ann) if forecast.nx_f_div_ann else nx_f_div_ann

        # 株式分割の検出（一括取得した株価データを使用）
        price_at_fin = split_detection_prices.get((stock_code, current_fin.disc_date))
        split_ratio_recent = self._detect_recent_split(
            price_at_fin, price_today, current_fin.sh_out_fy
        )

        split_ratio_yoy = 1.0
        if previous_fin and previous_fin.sh_out_fy and current_fin.sh_out_fy:
            ratio = float(current_fin.sh_out_fy) / float(previous_fin.sh_out_fy)
            if 1.5 <= ratio <= 20:
                split_ratio_yoy = ratio

        # === バリュエーション指標 ===

        # PER（実績、FY実績EPS）
        if fy_fin and fy_fin.eps:
            adjusted_eps = float(fy_fin.eps) / split_ratio_recent
            per = (
                float(price_today.close) / adjusted_eps if adjusted_eps > 0 else None
            )
        else:
            per = None

        # PBR
        if fy_fin and fy_fin.bps:
            adjusted_bps = float(fy_fin.bps) / split_ratio_recent
            pbr = (
                float(price_today.close) / adjusted_bps if adjusted_bps > 0 else None
            )
        else:
            pbr = None

        # PSR, PCFR（時価総額ベース）
        if fy_fin and fy_fin.sh_out_fy:
            market_cap = float(price_today.close) * float(fy_fin.sh_out_fy)
            psr = (
                market_cap / float(fy_fin.sales)
                if fy_fin.sales and fy_fin.sales > 0
                else None
            )
        else:
            market_cap = None
            psr = None

        if market_cap and fy_fin and fy_fin.cfo:
            pcfr = market_cap / float(fy_fin.cfo) if fy_fin.cfo > 0 else None
        else:
            pcfr = None

        # 予想PER（分割調整済み）
        adjusted_f_eps = f_eps / split_ratio_recent if f_eps else None
        forward_per_fy = (
            float(price_today.close) / adjusted_f_eps
            if adjusted_f_eps and adjusted_f_eps > 0
            else None
        )

        adjusted_nx_f_eps = nx_f_eps / split_ratio_recent if nx_f_eps else None
        forward_per_nx = (
            float(price_today.close) / adjusted_nx_f_eps
            if adjusted_nx_f_eps and adjusted_nx_f_eps > 0
            else None
        )

        # === 収益性指標 ===

        roe = (
            float(current_fin.np) / float(current_fin.eq)
            if current_fin.np and current_fin.eq and current_fin.eq > 0
            else None
        )
        roa = (
            float(current_fin.np) / float(current_fin.ta)
            if current_fin.np and current_fin.ta and current_fin.ta > 0
            else None
        )
        operating_margin = (
            float(current_fin.op) / float(current_fin.sales)
            if current_fin.op and current_fin.sales and current_fin.sales > 0
            else None
        )
        net_margin = (
            float(current_fin.np) / float(current_fin.sales)
            if current_fin.np and current_fin.sales and current_fin.sales > 0
            else None
        )

        # === 成長性指標（YoY） ===

        if previous_fin:
            adj_prev_sales = float(previous_fin.sales) if previous_fin.sales else None
            adj_prev_op = float(previous_fin.op) if previous_fin.op else None
            adj_prev_np = float(previous_fin.np) if previous_fin.np else None
            adj_prev_eps = (
                float(previous_fin.eps) / split_ratio_yoy if previous_fin.eps else None
            )
            adj_prev_cfo = float(previous_fin.cfo) if previous_fin.cfo else None

            sales_growth_yoy = (
                (float(current_fin.sales) - adj_prev_sales) / adj_prev_sales
                if current_fin.sales and adj_prev_sales and adj_prev_sales > 0
                else None
            )
            op_growth_yoy = (
                (float(current_fin.op) - adj_prev_op) / adj_prev_op
                if current_fin.op and adj_prev_op and adj_prev_op != 0
                else None
            )
            np_growth_yoy = (
                (float(current_fin.np) - adj_prev_np) / adj_prev_np
                if current_fin.np and adj_prev_np and adj_prev_np != 0
                else None
            )
            eps_growth_yoy = (
                (float(current_fin.eps) - adj_prev_eps) / adj_prev_eps
                if current_fin.eps and adj_prev_eps and adj_prev_eps != 0
                else None
            )
            cfo_growth_yoy = (
                (float(current_fin.cfo) - adj_prev_cfo) / adj_prev_cfo
                if current_fin.cfo and adj_prev_cfo and adj_prev_cfo != 0
                else None
            )
        else:
            sales_growth_yoy = None
            op_growth_yoy = None
            np_growth_yoy = None
            eps_growth_yoy = None
            cfo_growth_yoy = None

        # === 安全性指標 ===

        equity_ratio = (
            float(current_fin.eq) / float(current_fin.ta)
            if current_fin.eq and current_fin.ta and current_fin.ta > 0
            else None
        )

        # === 配当指標 ===

        if fy_fin and fy_fin.div_ann:
            adjusted_div_ann = float(fy_fin.div_ann) / split_ratio_recent
            dividend_yield = (
                adjusted_div_ann / float(price_today.close)
                if price_today.close > 0
                else None
            )
        else:
            dividend_yield = None

        payout_ratio = (
            float(fy_fin.payout_ratio_ann) if fy_fin and fy_fin.payout_ratio_ann else None
        )

        adjusted_f_div_ann = f_div_ann / split_ratio_recent if f_div_ann else None
        forward_div_yield_fy = (
            adjusted_f_div_ann / float(price_today.close)
            if adjusted_f_div_ann and price_today.close > 0
            else None
        )

        adjusted_nx_f_div_ann = nx_f_div_ann / split_ratio_recent if nx_f_div_ann else None
        forward_div_yield_nx = (
            adjusted_nx_f_div_ann / float(price_today.close)
            if adjusted_nx_f_div_ann and price_today.close > 0
            else None
        )

        # === 結果を返す ===

        return {
            "stock_code": stock_code,
            "date": target_date,
            "per": per,
            "pbr": pbr,
            "psr": psr,
            "pcfr": pcfr,
            "forward_per_fy": forward_per_fy,
            "forward_per_nx": forward_per_nx,
            "roe": roe,
            "roa": roa,
            "operating_margin": operating_margin,
            "net_margin": net_margin,
            "sales_growth_yoy": sales_growth_yoy,
            "op_growth_yoy": op_growth_yoy,
            "np_growth_yoy": np_growth_yoy,
            "eps_growth_yoy": eps_growth_yoy,
            "cfo_growth_yoy": cfo_growth_yoy,
            "equity_ratio": equity_ratio,
            "dividend_yield": dividend_yield,
            "payout_ratio": payout_ratio,
            "forward_div_yield_fy": forward_div_yield_fy,
            "forward_div_yield_nx": forward_div_yield_nx,
        }

    def _row_to_financial_statement(self, row: pd.Series) -> FinancialStatement:
        """pandasのDataFrame行をFinancialStatementオブジェクトに変換

        Args:
            row: DataFrameの1行（pandas Series）

        Returns:
            FinancialStatement: 財務データオブジェクト（DBセッション非紐付け）
        """
        # DBセッションに紐付けない（detached）FinancialStatementオブジェクトを作成
        fin = FinancialStatement(
            stock_code=row["stock_code"],
            disc_date=row["disc_date"],
            disc_time=row["disc_time"],
            type_of_document=row["type_of_document"],
            cur_per_type=row["cur_per_type"],
            cur_per_st=row["cur_per_st"],
            cur_per_en=row["cur_per_en"],
            sales=row["sales"],
            op=row["op"],
            od_p=row["od_p"],
            np=row["np"],
            eps=row["eps"],
            bps=row["bps"],
            cfo=row["cfo"],
            ta=row["ta"],
            eq=row["eq"],
            sh_out_fy=row["sh_out_fy"],
            div_ann=row["div_ann"],
            f_eps=row["f_eps"],
            nx_f_eps=row["nx_f_eps"],
            f_div_ann=row["f_div_ann"],
            nx_f_div_ann=row["nx_f_div_ann"],
        )
        return fin
