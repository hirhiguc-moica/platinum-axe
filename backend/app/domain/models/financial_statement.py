"""財務データ関連モデル"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin


class FinancialStatement(TimestampMixin, Base):
    """財務サマリーデータ（決算短信・業績予想・配当予想）"""

    __tablename__ = "financial_statements"

    # TimestampMixinから: id, created_at, updated_at（先頭に配置される）

    # === 基本情報 ===
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False, comment="銘柄コード")
    disc_date: Mapped[date] = mapped_column(Date, nullable=False, comment="開示日")
    disc_time: Mapped[str] = mapped_column(String(20), nullable=False, comment="開示時刻")
    disc_no: Mapped[str | None] = mapped_column(String(50), comment="開示番号")
    type_of_document: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="開示書類種別"
    )

    # === 会計期間 ===
    cur_per_type: Mapped[str | None] = mapped_column(
        String(20), comment="会計期間種別（1Q/2Q/3Q/FY等）"
    )
    cur_per_st: Mapped[date | None] = mapped_column(Date, comment="当期開始日")
    cur_per_en: Mapped[date | None] = mapped_column(Date, comment="当期終了日")
    cur_fy_st: Mapped[date | None] = mapped_column(Date, comment="当期会計年度開始日")
    cur_fy_en: Mapped[date | None] = mapped_column(Date, comment="当期会計年度終了日")
    nxt_fy_st: Mapped[date | None] = mapped_column(Date, comment="翌期会計年度開始日")
    nxt_fy_en: Mapped[date | None] = mapped_column(Date, comment="翌期会計年度終了日")

    # === 財務実績（連結） ===
    sales: Mapped[Decimal | None] = mapped_column(Numeric(17, 2), comment="売上高（百万円）")
    op: Mapped[Decimal | None] = mapped_column(Numeric(17, 2), comment="営業利益（百万円）")
    od_p: Mapped[Decimal | None] = mapped_column(Numeric(17, 2), comment="経常利益（百万円）")
    np: Mapped[Decimal | None] = mapped_column(Numeric(17, 2), comment="当期純利益（百万円）")
    eps: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="1株当たり利益（円）")
    deps: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="希薄化後EPS（円）")
    ta: Mapped[Decimal | None] = mapped_column(Numeric(17, 2), comment="総資産（百万円）")
    eq: Mapped[Decimal | None] = mapped_column(Numeric(17, 2), comment="純資産（百万円）")
    eq_ar: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="自己資本比率（%）")
    bps: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="1株当たり純資産（円）")
    cfo: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="営業キャッシュフロー（百万円）"
    )
    cfi: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="投資キャッシュフロー（百万円）"
    )
    cff: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="財務キャッシュフロー（百万円）"
    )
    cash_eq: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="現金及び現金同等物（百万円）"
    )

    # === 株式数情報 ===
    sh_out_fy: Mapped[int | None] = mapped_column(BigInteger, comment="期末発行済株式数（千株）")
    tr_sh_fy: Mapped[int | None] = mapped_column(BigInteger, comment="期末自己株式数（千株）")
    avg_sh: Mapped[int | None] = mapped_column(BigInteger, comment="期中平均株式数（千株）")

    # === 配当情報（実績） ===
    div_1q: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="第1四半期配当金（円）")
    div_2q: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="第2四半期配当金（円）")
    div_3q: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="第3四半期配当金（円）")
    div_fy: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="期末配当金（円）")
    div_ann: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="年間配当金（円）")
    div_unit: Mapped[str | None] = mapped_column(String(20), comment="配当単位")
    div_total_ann: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="年間配当総額（百万円）"
    )
    payout_ratio_ann: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="配当性向（%）")

    # === 配当情報（予想） ===
    f_div_1q: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="第1四半期配当金予想（円）"
    )
    f_div_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="第2四半期配当金予想（円）"
    )
    f_div_3q: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="第3四半期配当金予想（円）"
    )
    f_div_fy: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="期末配当金予想（円）")
    f_div_ann: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="年間配当金予想（円）"
    )
    f_div_unit: Mapped[str | None] = mapped_column(String(20), comment="配当単位・予想")
    f_div_total_ann: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="年間配当総額予想（百万円）"
    )
    f_payout_ratio_ann: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), comment="配当性向予想（%）"
    )

    # === 当期業績予想（連結） ===
    f_sales_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="売上高予想・第2四半期末（百万円）"
    )
    f_op_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="営業利益予想・第2四半期末（百万円）"
    )
    f_od_p_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="経常利益予想・第2四半期末（百万円）"
    )
    f_np_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="当期純利益予想・第2四半期末（百万円）"
    )
    f_eps_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="EPS予想・第2四半期末（円）"
    )
    f_sales: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="売上高予想・期末（百万円）"
    )
    f_op: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="営業利益予想・期末（百万円）"
    )
    f_od_p: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="経常利益予想・期末（百万円）"
    )
    f_np: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="当期純利益予想・期末（百万円）"
    )
    f_eps: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="EPS予想・期末（円）")

    # === 翌期業績予想（連結） ===
    nx_f_sales_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="売上高予想・翌事業年度第2四半期末（百万円）"
    )
    nx_f_op_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="営業利益予想・翌事業年度第2四半期末（百万円）"
    )
    nx_f_od_p_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="経常利益予想・翌事業年度第2四半期末（百万円）"
    )
    nx_f_np_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="当期純利益予想・翌事業年度第2四半期末（百万円）"
    )
    nx_f_eps_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="EPS予想・翌事業年度第2四半期末（円）"
    )
    nx_f_sales: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="売上高予想・翌事業年度期末（百万円）"
    )
    nx_f_op: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="営業利益予想・翌事業年度期末（百万円）"
    )
    nx_f_od_p: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="経常利益予想・翌事業年度期末（百万円）"
    )
    nx_f_np: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="当期純利益予想・翌事業年度期末（百万円）"
    )
    nx_f_eps: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="EPS予想・翌事業年度期末（円）"
    )

    # === 翌期配当予想 ===
    nx_f_div_1q: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="第1四半期配当金予想・翌事業年度（円）"
    )
    nx_f_div_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="第2四半期配当金予想・翌事業年度（円）"
    )
    nx_f_div_3q: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="第3四半期配当金予想・翌事業年度（円）"
    )
    nx_f_div_fy: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="期末配当金予想・翌事業年度（円）"
    )
    nx_f_div_ann: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="年間配当金予想・翌事業年度（円）"
    )
    nx_f_div_unit: Mapped[str | None] = mapped_column(
        String(20), comment="配当単位・翌事業年度予想"
    )
    nx_f_payout_ratio_ann: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), comment="配当性向予想・翌事業年度（%）"
    )

    # === 非連結データ（実績） ===
    nc_sales: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="売上高・非連結（百万円）"
    )
    nc_op: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="営業利益・非連結（百万円）"
    )
    nc_od_p: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="経常利益・非連結（百万円）"
    )
    nc_np: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="当期純利益・非連結（百万円）"
    )
    nc_eps: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="EPS・非連結（円）")
    nc_ta: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="総資産・非連結（百万円）"
    )
    nc_eq: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="純資産・非連結（百万円）"
    )
    nc_eq_ar: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), comment="自己資本比率・非連結（%）"
    )
    nc_bps: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="BPS・非連結（円）")

    # === 非連結データ（当期予想） ===
    nc_f_sales_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="売上高予想・第2四半期末・非連結（百万円）"
    )
    nc_f_op_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="営業利益予想・第2四半期末・非連結（百万円）"
    )
    nc_f_od_p_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="経常利益予想・第2四半期末・非連結（百万円）"
    )
    nc_f_np_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="当期純利益予想・第2四半期末・非連結（百万円）"
    )
    nc_f_eps_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="EPS予想・第2四半期末・非連結（円）"
    )
    nc_f_sales: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="売上高予想・期末・非連結（百万円）"
    )
    nc_f_op: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="営業利益予想・期末・非連結（百万円）"
    )
    nc_f_od_p: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="経常利益予想・期末・非連結（百万円）"
    )
    nc_f_np: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="当期純利益予想・期末・非連結（百万円）"
    )
    nc_f_eps: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="EPS予想・期末・非連結（円）"
    )

    # === 非連結データ（翌期予想） ===
    nc_nx_f_sales_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="売上高予想・翌事業年度第2四半期末・非連結（百万円）"
    )
    nc_nx_f_op_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="営業利益予想・翌事業年度第2四半期末・非連結（百万円）"
    )
    nc_nx_f_od_p_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="経常利益予想・翌事業年度第2四半期末・非連結（百万円）"
    )
    nc_nx_f_np_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="当期純利益予想・翌事業年度第2四半期末・非連結（百万円）"
    )
    nc_nx_f_eps_2q: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="EPS予想・翌事業年度第2四半期末・非連結（円）"
    )
    nc_nx_f_sales: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="売上高予想・翌事業年度期末・非連結（百万円）"
    )
    nc_nx_f_op: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="営業利益予想・翌事業年度期末・非連結（百万円）"
    )
    nc_nx_f_od_p: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="経常利益予想・翌事業年度期末・非連結（百万円）"
    )
    nc_nx_f_np: Mapped[Decimal | None] = mapped_column(
        Numeric(17, 2), comment="当期純利益予想・翌事業年度期末・非連結（百万円）"
    )
    nc_nx_f_eps: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="EPS予想・翌事業年度期末・非連結（円）"
    )

    # === 会計処理フラグ ===
    mat_chg_sub: Mapped[str | None] = mapped_column(String(255), comment="重要な子会社の異動")
    sig_chg_in_c: Mapped[str | None] = mapped_column(String(255), comment="連結範囲の重大な変更")
    chg_by_as_rev: Mapped[str | None] = mapped_column(
        String(255), comment="会計基準の改訂による変更"
    )
    chg_no_as_rev: Mapped[str | None] = mapped_column(
        String(255), comment="会計基準の改訂以外による変更"
    )
    chg_ac_est: Mapped[str | None] = mapped_column(String(255), comment="会計上の見積りの変更")
    retro_rst: Mapped[str | None] = mapped_column(String(255), comment="遡及修正")

    # === メタ情報 ===
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="API取得日時")

    __table_args__ = (
        # ナチュラルキー: (Code, DiscDate, TypeOfDocument, DiscTime) で冪等性を保証
        # 同一銘柄・同日・同書類の訂正開示に対応（開示時刻で区別）
        UniqueConstraint(
            "stock_code",
            "disc_date",
            "type_of_document",
            "disc_time",
            name="uq_financial_statements_natural_key",
        ),
        # 銘柄別の最新データ取得用インデックス
        Index(
            "idx_financial_statements_code_date",
            "stock_code",
            "disc_date",
            postgresql_using="btree",
        ),
        # 日付順ソート用インデックス
        Index("idx_financial_statements_date", "disc_date", postgresql_using="btree"),
        # 四半期/通期フィルタ用インデックス
        Index("idx_financial_statements_per_type", "cur_per_type", postgresql_using="btree"),
        {"comment": "財務サマリーデータ（決算短信・業績予想・配当予想）"},
    )

    def __repr__(self) -> str:
        return f"<FinancialStatement(code={self.stock_code}, disc_date={self.disc_date}, type={self.type_of_document})>"
