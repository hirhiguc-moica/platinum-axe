"""信用取引週末残高データ取得スクリプト（差分取得）

J-Quants API から信用取引週末残高データ（全銘柄）の差分を取得してDBに保存する。

DBの最新日付+1日から現在までを自動取得（バックフィル対応）。

使用例:
    # DBの最新日付から自動取得
    $ uv run python backend/jobs/collectors/fetch_daily_margin_interest.py

    # wait時間なし（rate limit注意）
    $ uv run python backend/jobs/collectors/fetch_daily_margin_interest.py --wait 0

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - DBの最新日付を自動取得して差分を判定
    - 日単位で取得（APIの仕様上、全銘柄取得はdateパラメータのみ対応）
    - 週末（金曜日）のみデータが存在（他の日はデータなし）
    - 各日取得後1秒待機（--waitで調整可能）
    - PostgreSQL UPSERT で高速保存（重複実行OK）

所要時間見積もり（1週間=7日分）:
    - wait=1秒: 約7秒（うち週末1日分のみデータあり）
    - wait=0秒: 約4秒（rate limit注意）

実行タイミング:
    - 手動実行: 上記コマンド
    - 自動実行: GCP Cloud Scheduler（毎営業日17:30、株価・財務取得後）
"""

import argparse
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

from app.usecase.fetch_margin_interest_usecase import FetchMarginInterestUseCase  # noqa: E402


def main() -> None:
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="信用取引週末残高データ取得（差分取得モード）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=1.0,
        help="各日取得後の待機秒数（デフォルト: 1.0秒、小数点可）",
    )

    args = parser.parse_args()

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
        usecase = FetchMarginInterestUseCase(session)

        try:
            result = usecase.execute_incremental(wait_seconds=args.wait)

            print("\n✅ 正常終了")
            print(f"  取得日数: {result['total_weeks']}日")  # 変数名は互換性のためweeksだがdaysの意味
            print(f"  DB保存件数: {result['total_saved']:,}件")
            print(f"  所要時間: {result['elapsed_seconds']:.1f}秒")

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
