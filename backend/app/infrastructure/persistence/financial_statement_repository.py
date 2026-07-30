"""財務サマリーデータ永続化リポジトリ

財務データのDB保存・取得を担当。
"""

from datetime import date, datetime
from decimal import Decimal

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.models.financial_statement import FinancialStatement


class FinancialStatementRepository:
    """財務サマリーデータ永続化リポジトリ

    PostgreSQLへの財務データのUPSERT保存、最新日付取得を提供。

    使用例:
        >>> repo = FinancialStatementRepository(session)
        >>> inserted = repo.bulk_upsert(df)
        >>> print(inserted)
        1234  # 1ヶ月分の決算開示件数
    """

    def __init__(self, session: Session):
        """初期化

        Args:
            session: SQLAlchemyの同期セッション
        """
        self.session = session

    def get_latest_disc_date(self) -> date | None:
        """全銘柄の最新開示日を取得

        差分取得の開始日を決定するために使用。

        Returns:
            date | None: 最新の開示日。データが存在しない場合はNone。

        Example:
            >>> repo = FinancialStatementRepository(session)
            >>> latest = repo.get_latest_disc_date()
            >>> print(latest)
            2026-07-24
        """
        stmt = select(func.max(FinancialStatement.disc_date))
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def bulk_upsert(self, df: pd.DataFrame) -> int:
        """財務DataFrameをPostgreSQL UPSERTでDB保存

        J-Quants APIから取得したDataFrameを、DBモデルに合わせて型変換し、
        ON CONFLICT DO UPDATE (UPSERT) で保存する。

        Args:
            df: J-Quants APIから取得した財務サマリーデータ
                カラム: DiscDate, DiscTime, Code, TypeOfDocument, Sales, OP等（約140項目）

        Returns:
            int: 保存件数（新規追加 + 更新の合計）

        Note:
            - stock_code + disc_date + type_of_document + disc_time の UNIQUE制約により重複を防止
            - NaN は None に変換される
            - 数値型は Decimal または int に変換
            - 主キー（stock_code, disc_date, type_of_document, disc_time）が必須
        """
        if len(df) == 0:
            return 0

        # DataFrameのコピーを作成（元データを変更しない）
        df_copy = df.copy()

        # デバッグ: カラム名を確認
        print(f"  📋 取得したカラム名（先頭20項目）: {list(df_copy.columns[:20])}")

        # 必須カラム（ナチュラルキー: Code, DiscDate, DocType, DiscTime）が存在しないレコードを除外
        # 注: APIドキュメントでは TypeOfDocument だが、実際のレスポンスは DocType
        required_keys = ["Code", "DiscDate", "DocType", "DiscTime"]
        for key in required_keys:
            if key not in df_copy.columns:
                print(f"  ⚠️  必須カラム '{key}' が見つかりません")
                print(f"  📋 利用可能なカラム: {list(df_copy.columns)}")
                raise ValueError(
                    f"Required column '{key}' not found in DataFrame. Available columns: {list(df_copy.columns)}"
                )
            df_copy = df_copy[df_copy[key].notna()]

        if len(df_copy) == 0:
            return 0

        # NaN を None に置換（一括処理）
        df_copy = df_copy.where(pd.notna(df_copy), None)

        # DiscDate列を date 型に変換
        df_copy["DiscDate"] = pd.to_datetime(df_copy["DiscDate"]).dt.date

        # 日付カラムを date 型に変換
        date_columns = ["CurPerSt", "CurPerEn", "CurFYSt", "CurFYEn", "NxtFYSt", "NxtFYEn"]
        for col in date_columns:
            if col in df_copy.columns:
                df_copy[col] = pd.to_datetime(df_copy[col], errors="coerce").dt.date

        # カラム名をDBカラム名にマッピング（スネークケースに変換）
        column_mapping = self._get_column_mapping()
        df_copy = df_copy.rename(columns=column_mapping)

        # 重複行を削除（UNIQUE制約: stock_code, disc_date, type_of_document, disc_time）
        # ナチュラルキー（冪等性担保）: 最新のデータを保持（keep='last'）
        df_copy = df_copy.drop_duplicates(
            subset=["stock_code", "disc_date", "type_of_document", "disc_time"], keep="last"
        )

        # 数値型をDecimalに変換（財務数値）
        decimal_columns = self._get_decimal_columns()
        for col in decimal_columns:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].apply(
                    lambda x: (
                        Decimal(str(x))
                        if pd.notna(x) and x is not None and str(x).strip() != ""
                        else None
                    )
                )

        # 整数型に変換（株式数）
        int_columns = ["sh_out_fy", "tr_sh_fy", "avg_sh"]
        for col in int_columns:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].apply(
                    lambda x: (
                        int(x) if pd.notna(x) and x is not None and str(x).strip() != "" else None
                    )
                )

        # fetched_at を追加
        df_copy["fetched_at"] = datetime.now()

        # 必要なカラムのみ選択（存在するカラムのみ）
        required_columns = self._get_required_columns()
        available_columns = [col for col in required_columns if col in df_copy.columns]
        df_copy = df_copy[available_columns]

        # DataFrameをdict形式に変換（一括変換、高速）
        records = df_copy.to_dict("records")

        # fetched_atをdatetimeに変換
        fetched_at_value = datetime.now()
        for record in records:
            # fetched_at変換
            if "fetched_at" in record and hasattr(record["fetched_at"], "to_pydatetime"):
                record["fetched_at"] = record["fetched_at"].to_pydatetime()
            else:
                record["fetched_at"] = fetched_at_value

            # NaTをNoneに変換（日付型）
            for key, value in list(record.items()):
                if pd.isna(value):
                    record[key] = None

            # TimestampMixinカラムを除外（自動生成されるため）
            record.pop("id", None)
            record.pop("created_at", None)
            record.pop("updated_at", None)

        # PostgreSQL UPSERT (SQLAlchemy ORM)
        # PostgreSQLの65,535パラメータ上限対策: 500件ずつチャンク分割（111カラム×500=55,500パラメータ）
        chunk_size = 500
        total_saved = 0

        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]

            stmt = insert(FinancialStatement).values(chunk)

            # UPSERT時の更新対象カラムを動的に生成（主キー以外）
            update_dict = {
                col: getattr(stmt.excluded, col)
                for col in available_columns
                if col not in ["stock_code", "disc_date", "type_of_document", "disc_time"]
            }
            # updated_atを明示的に更新（CURRENT_TIMESTAMPで上書き）
            update_dict["updated_at"] = func.current_timestamp()

            stmt = stmt.on_conflict_do_update(
                constraint="uq_financial_statements_natural_key",
                set_=update_dict,
            )

            self.session.execute(stmt)
            total_saved += len(chunk)

        # トランザクション境界は呼び出し側（UseCase）に寄せる
        # ここではflush()のみ実行（commit()しない）
        self.session.flush()

        # 保存件数を返す
        return total_saved

    def _get_column_mapping(self) -> dict[str, str]:
        """J-Quants APIカラム名 → DBカラム名のマッピング

        Returns:
            dict[str, str]: カラム名マッピング辞書
        """
        return {
            # 基本情報
            "Code": "stock_code",
            "DiscDate": "disc_date",
            "DiscTime": "disc_time",
            "DiscNo": "disc_no",
            "DocType": "type_of_document",  # 注: APIドキュメントでは TypeOfDocument だが、実際は DocType
            # 会計期間
            "CurPerType": "cur_per_type",
            "CurPerSt": "cur_per_st",
            "CurPerEn": "cur_per_en",
            "CurFYSt": "cur_fy_st",
            "CurFYEn": "cur_fy_en",
            "NxtFYSt": "nxt_fy_st",
            "NxtFYEn": "nxt_fy_en",
            # 財務実績（連結）
            "Sales": "sales",
            "OP": "op",
            "OdP": "od_p",
            "NP": "np",
            "EPS": "eps",
            "DEPS": "deps",
            "TA": "ta",
            "Eq": "eq",
            "EqAR": "eq_ar",
            "BPS": "bps",
            "CFO": "cfo",
            "CFI": "cfi",
            "CFF": "cff",
            "CashEq": "cash_eq",
            # 株式数情報
            "ShOutFY": "sh_out_fy",
            "TrShFY": "tr_sh_fy",
            "AvgSh": "avg_sh",
            # 配当情報（実績）
            "Div1Q": "div_1q",
            "Div2Q": "div_2q",
            "Div3Q": "div_3q",
            "DivFY": "div_fy",
            "DivAnn": "div_ann",
            "DivUnit": "div_unit",
            "DivTotalAnn": "div_total_ann",
            "PayoutRatioAnn": "payout_ratio_ann",
            # 配当情報（予想）
            "FDiv1Q": "f_div_1q",
            "FDiv2Q": "f_div_2q",
            "FDiv3Q": "f_div_3q",
            "FDivFY": "f_div_fy",
            "FDivAnn": "f_div_ann",
            "FDivUnit": "f_div_unit",
            "FDivTotalAnn": "f_div_total_ann",
            "FPayoutRatioAnn": "f_payout_ratio_ann",
            # 当期業績予想（連結）
            "FSales2Q": "f_sales_2q",
            "FOP2Q": "f_op_2q",
            "FOdP2Q": "f_od_p_2q",
            "FNP2Q": "f_np_2q",
            "FEPS2Q": "f_eps_2q",
            "FSales": "f_sales",
            "FOP": "f_op",
            "FOdP": "f_od_p",
            "FNP": "f_np",
            "FEPS": "f_eps",
            # 翌期業績予想（連結）
            "NxFSales2Q": "nx_f_sales_2q",
            "NxFOP2Q": "nx_f_op_2q",
            "NxFOdP2Q": "nx_f_od_p_2q",
            "NxFNp2Q": "nx_f_np_2q",
            "NxFEPS2Q": "nx_f_eps_2q",
            "NxFSales": "nx_f_sales",
            "NxFOP": "nx_f_op",
            "NxFOdP": "nx_f_od_p",
            "NxFNp": "nx_f_np",
            "NxFEPS": "nx_f_eps",
            # 翌期配当予想
            "NxFDiv1Q": "nx_f_div_1q",
            "NxFDiv2Q": "nx_f_div_2q",
            "NxFDiv3Q": "nx_f_div_3q",
            "NxFDivFY": "nx_f_div_fy",
            "NxFDivAnn": "nx_f_div_ann",
            "NxFDivUnit": "nx_f_div_unit",
            "NxFPayoutRatioAnn": "nx_f_payout_ratio_ann",
            # 非連結データ（実績）
            "NCSales": "nc_sales",
            "NCOP": "nc_op",
            "NCOdP": "nc_od_p",
            "NCNP": "nc_np",
            "NCEPS": "nc_eps",
            "NCTA": "nc_ta",
            "NCEq": "nc_eq",
            "NCEqAR": "nc_eq_ar",
            "NCBPS": "nc_bps",
            # 非連結データ（当期予想）
            "FNCSales2Q": "nc_f_sales_2q",
            "FNCOP2Q": "nc_f_op_2q",
            "FNCOdP2Q": "nc_f_od_p_2q",
            "FNCNP2Q": "nc_f_np_2q",
            "FNCEPS2Q": "nc_f_eps_2q",
            "FNCSales": "nc_f_sales",
            "FNCOP": "nc_f_op",
            "FNCOdP": "nc_f_od_p",
            "FNCNP": "nc_f_np",
            "FNCEPS": "nc_f_eps",
            # 非連結データ（翌期予想）
            "NxFNCSales2Q": "nc_nx_f_sales_2q",
            "NxFNCOP2Q": "nc_nx_f_op_2q",
            "NxFNCOdP2Q": "nc_nx_f_od_p_2q",
            "NxFNCNP2Q": "nc_nx_f_np_2q",
            "NxFNCEPS2Q": "nc_nx_f_eps_2q",
            "NxFNCSales": "nc_nx_f_sales",
            "NxFNCOP": "nc_nx_f_op",
            "NxFNCOdP": "nc_nx_f_od_p",
            "NxFNCNP": "nc_nx_f_np",
            "NxFNCEPS": "nc_nx_f_eps",
            # 会計処理フラグ
            "MatChgSub": "mat_chg_sub",
            "SigChgInC": "sig_chg_in_c",
            "ChgByASRev": "chg_by_as_rev",
            "ChgNoASRev": "chg_no_as_rev",
            "ChgAcEst": "chg_ac_est",
            "RetroRst": "retro_rst",
        }

    def _get_decimal_columns(self) -> list[str]:
        """Decimal型に変換すべきカラムのリスト

        Returns:
            list[str]: Decimal型カラム名のリスト
        """
        return [
            # 財務実績
            "sales",
            "op",
            "od_p",
            "np",
            "eps",
            "deps",
            "ta",
            "eq",
            "eq_ar",
            "bps",
            "cfo",
            "cfi",
            "cff",
            "cash_eq",
            # 配当
            "div_1q",
            "div_2q",
            "div_3q",
            "div_fy",
            "div_ann",
            "div_total_ann",
            "payout_ratio_ann",
            "f_div_1q",
            "f_div_2q",
            "f_div_3q",
            "f_div_fy",
            "f_div_ann",
            "f_div_total_ann",
            "f_payout_ratio_ann",
            # 当期予想
            "f_sales_2q",
            "f_op_2q",
            "f_od_p_2q",
            "f_np_2q",
            "f_eps_2q",
            "f_sales",
            "f_op",
            "f_od_p",
            "f_np",
            "f_eps",
            # 翌期予想
            "nx_f_sales_2q",
            "nx_f_op_2q",
            "nx_f_od_p_2q",
            "nx_f_np_2q",
            "nx_f_eps_2q",
            "nx_f_sales",
            "nx_f_op",
            "nx_f_od_p",
            "nx_f_np",
            "nx_f_eps",
            "nx_f_div_1q",
            "nx_f_div_2q",
            "nx_f_div_3q",
            "nx_f_div_fy",
            "nx_f_div_ann",
            "nx_f_payout_ratio_ann",
            # 非連結
            "nc_sales",
            "nc_op",
            "nc_od_p",
            "nc_np",
            "nc_eps",
            "nc_ta",
            "nc_eq",
            "nc_eq_ar",
            "nc_bps",
            # 非連結予想
            "nc_f_sales_2q",
            "nc_f_op_2q",
            "nc_f_od_p_2q",
            "nc_f_np_2q",
            "nc_f_eps_2q",
            "nc_f_sales",
            "nc_f_op",
            "nc_f_od_p",
            "nc_f_np",
            "nc_f_eps",
            "nc_nx_f_sales_2q",
            "nc_nx_f_op_2q",
            "nc_nx_f_od_p_2q",
            "nc_nx_f_np_2q",
            "nc_nx_f_eps_2q",
            "nc_nx_f_sales",
            "nc_nx_f_op",
            "nc_nx_f_od_p",
            "nc_nx_f_np",
            "nc_nx_f_eps",
        ]

    def _get_required_columns(self) -> list[str]:
        """DB保存に必要なカラムのリスト

        Returns:
            list[str]: 必須カラム名のリスト
        """
        return [
            # 基本情報
            "stock_code",
            "disc_date",
            "disc_time",
            "disc_no",
            "type_of_document",
            # 会計期間
            "cur_per_type",
            "cur_per_st",
            "cur_per_en",
            "cur_fy_st",
            "cur_fy_en",
            "nxt_fy_st",
            "nxt_fy_en",
            # 財務実績
            "sales",
            "op",
            "od_p",
            "np",
            "eps",
            "deps",
            "ta",
            "eq",
            "eq_ar",
            "bps",
            "cfo",
            "cfi",
            "cff",
            "cash_eq",
            # 株式数
            "sh_out_fy",
            "tr_sh_fy",
            "avg_sh",
            # 配当実績
            "div_1q",
            "div_2q",
            "div_3q",
            "div_fy",
            "div_ann",
            "div_unit",
            "div_total_ann",
            "payout_ratio_ann",
            # 配当予想
            "f_div_1q",
            "f_div_2q",
            "f_div_3q",
            "f_div_fy",
            "f_div_ann",
            "f_div_unit",
            "f_div_total_ann",
            "f_payout_ratio_ann",
            # 当期予想
            "f_sales_2q",
            "f_op_2q",
            "f_od_p_2q",
            "f_np_2q",
            "f_eps_2q",
            "f_sales",
            "f_op",
            "f_od_p",
            "f_np",
            "f_eps",
            # 翌期予想
            "nx_f_sales_2q",
            "nx_f_op_2q",
            "nx_f_od_p_2q",
            "nx_f_np_2q",
            "nx_f_eps_2q",
            "nx_f_sales",
            "nx_f_op",
            "nx_f_od_p",
            "nx_f_np",
            "nx_f_eps",
            "nx_f_div_1q",
            "nx_f_div_2q",
            "nx_f_div_3q",
            "nx_f_div_fy",
            "nx_f_div_ann",
            "nx_f_div_unit",
            "nx_f_payout_ratio_ann",
            # 非連結
            "nc_sales",
            "nc_op",
            "nc_od_p",
            "nc_np",
            "nc_eps",
            "nc_ta",
            "nc_eq",
            "nc_eq_ar",
            "nc_bps",
            # 非連結予想
            "nc_f_sales_2q",
            "nc_f_op_2q",
            "nc_f_od_p_2q",
            "nc_f_np_2q",
            "nc_f_eps_2q",
            "nc_f_sales",
            "nc_f_op",
            "nc_f_od_p",
            "nc_f_np",
            "nc_f_eps",
            "nc_nx_f_sales_2q",
            "nc_nx_f_op_2q",
            "nc_nx_f_od_p_2q",
            "nc_nx_f_np_2q",
            "nc_nx_f_eps_2q",
            "nc_nx_f_sales",
            "nc_nx_f_op",
            "nc_nx_f_od_p",
            "nc_nx_f_np",
            "nc_nx_f_eps",
            # 会計処理
            "mat_chg_sub",
            "sig_chg_in_c",
            "chg_by_as_rev",
            "chg_no_as_rev",
            "chg_ac_est",
            "retro_rst",
            # メタ
            "fetched_at",
        ]
