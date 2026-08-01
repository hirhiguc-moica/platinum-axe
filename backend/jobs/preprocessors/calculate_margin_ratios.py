"""信用倍率・増減率計算スクリプト（全量計算）

信用取引週末残高データ（margin_trading_balance）から以下を計算してDBに保存する。

計算項目:
    - margin_ratio: 信用倍率（買い残 ÷ 売り残）
    - long_vol_change: 買い残前週比増減（株数）
    - short_vol_change: 売り残前週比増減（株数）
    - long_vol_change_rate: 買い残前週比増減率（%）
    - short_vol_change_rate: 売り残前週比増減率（%）

使用例:
    # 全量計算
    $ uv run python backend/jobs/preprocessors/calculate_margin_ratios.py

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - 全データ（全期間・全銘柄）を対象に計算
    - stock_codeごとにグループ化して前週比計算
    - PostgreSQL UPDATE（バインドパラメータ）で安全に一括保存

所要時間見積もり:
    - 全データ: 約30-60秒

実行タイミング:
    - 初回のみ: 全量計算（このスクリプト）
    - 日次: 差分計算（calculate_daily_margin_ratios.py）
"""

import logging
import os
import sys
from pathlib import Path

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

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.usecase.calculate_margin_ratios_usecase import CalculateMarginRatiosUseCase  # noqa: E402


def main() -> None:
    """メイン処理"""
    print("=" * 80)
    print("📊 信用倍率・増減率計算（全量）開始")
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
            # UseCase実行
            usecase = CalculateMarginRatiosUseCase(session)
            result = usecase.execute_full()

            print("\n✅ 正常終了")
            print(f"  計算件数: {result['total_calculated']:,}件")
            print(f"  更新件数: {result['total_updated']:,}件")

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
