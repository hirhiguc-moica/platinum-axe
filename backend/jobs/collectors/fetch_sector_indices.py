"""セクター指数データ取得スクリプト（全件取得）

J-Quants API からセクター指数日次データ（TOPIX、東証33業種等、全47指数）を全件取得してDBに保存する。

コマンドライン引数:
    --start-date: 取得開始日（YYYY-MM-DD形式）
        デフォルト: 実行日から10年前（J-Quants Standardプランの取得可能期間）

    --end-date: 取得終了日（YYYY-MM-DD形式）
        デフォルト: 今日

    --test: テストモード（1ヶ月のみ取得）
        デフォルト: False

    --wait: 各指数取得後の待機秒数
        デフォルト: 1秒
        rate limit: 60req/分（1req/秒）を考慮
        0秒まで短縮可能だが、rate limitに注意

使用例:
    # テストモード（1ヶ月のみ取得）
    $ uv run python backend/jobs/collectors/fetch_sector_indices.py --test

    # 過去10年分取得（デフォルトwait=1秒で約1時間）
    $ uv run python backend/jobs/collectors/fetch_sector_indices.py

    # wait時間なし（約50分、rate limit注意）
    $ uv run python backend/jobs/collectors/fetch_sector_indices.py --wait 0

    # 期間指定（2009年2月2日以降を指定可能）
    $ uv run python backend/jobs/collectors/fetch_sector_indices.py \
        --start-date 2024-01-01 --end-date 2024-12-31

実装詳細:
    - UseCase層を使用した実装（DDD構造）
    - 日単位で分割（47指数を1日ずつ取得）
    - 各日取得後1秒待機（--waitで調整可能）
    - PostgreSQL UPSERT で高速保存（重複実行OK）
    - 進捗保存なし（エラー時は最初から再実行）

所要時間見積もり（全47指数×約3700営業日）:
    - wait=1秒: 約3700秒（約1時間、推奨）
    - wait=0秒: 約30分（rate limit注意）
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
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

from app.usecase.fetch_sector_indices_usecase import FetchSectorIndicesUseCase  # noqa: E402


def main() -> None:
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="セクター指数データ取得（全件取得モード）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="取得開始日（YYYY-MM-DD形式）。デフォルト: 実行日から10年前",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="取得終了日（YYYY-MM-DD形式）。デフォルト: 今日",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモード（1ヶ月のみ取得）",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=1.0,
        help="各指数取得後の待機秒数（デフォルト: 1.0秒、小数点可）",
    )

    args = parser.parse_args()

    # 日付範囲の設定
    if args.test:
        # テストモード: 直近1ヶ月のみ取得
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        print("🧪 テストモード: 直近1ヶ月のみ取得します")
    else:
        # 本番モード: J-Quants API取得可能開始日から現在まで
        if args.start_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        else:
            # デフォルト: 現在から10年前（J-Quants Standardプラン）
            ten_years_ago = datetime.now() - timedelta(days=365 * 10)
            start_date = ten_years_ago

        if args.end_date:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        else:
            # デフォルト: 今日
            end_date = datetime.now()

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
        usecase = FetchSectorIndicesUseCase(session)

        try:
            result = usecase.execute_full(
                start_date=start_date, end_date=end_date, wait_seconds=args.wait
            )

            print("\n✅ 正常終了")
            print(f"  取得日数: {result['total_days']}日")
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
