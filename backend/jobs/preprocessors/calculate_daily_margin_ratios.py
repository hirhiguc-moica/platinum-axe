"""信用倍率・増減率計算スクリプト（差分計算）

信用取引週末残高データから以下を差分計算してDBに保存する。

計算項目:
    - margin_ratio: 信用倍率（買い残 ÷ 売り残）
    - long_vol_change: 買い残前週比増減（株数）
    - short_vol_change: 売り残前週比増減（株数）
    - long_vol_change_rate: 買い残前週比増減率（%）
    - short_vol_change_rate: 売り残前週比増減率（%）

使用例:
    # DBの最新計算日から自動計算
    $ uv run python backend/jobs/preprocessors/calculate_daily_margin_ratios.py

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - DBの最新計算日を自動取得して差分を判定
    - 前週データ取得のため最新計算日-14日からロード
    - PostgreSQL UPDATE で高速更新
    - 異常値フィルタリング（short_vol < 100, ratio > 100,000等）

実行タイミング:
    - 手動実行: 上記コマンド
    - 自動実行: GCP Cloud Scheduler（毎営業日17:30、信用取引残高取得後）
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
    print("🔄 信用倍率・増減率計算開始（差分計算モード）")
    print("=" * 80)

    # データベース接続
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URLが設定されていません。.envファイルを確認してください。")
        sys.exit(1)

    # 非同期版のURL（+asyncpg）を同期版に変換
    database_url = database_url.replace("+asyncpg", "")

    engine = create_engine(database_url, echo=False)

    # UseCase実行
    with Session(engine) as session:
        usecase = CalculateMarginRatiosUseCase(session)

        try:
            result = usecase.execute_incremental()

            print("\n✅ 正常終了")
            print(f"  計算件数: {result['total_calculated']:,}件")
            print(f"  更新件数: {result['total_updated']:,}件")

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
