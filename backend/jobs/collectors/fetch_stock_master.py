"""銘柄マスタ取得スクリプト

J-Quants API から銘柄マスタを取得してDBに保存する。

使用例:
    # 全銘柄取得
    python backend/jobs/collectors/fetch_stock_master.py

実装:
    - 初回実行: 全銘柄を新規追加
    - 2回目以降: info_dateで更新判断（新しいデータのみ更新）
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# .envファイルを読み込み
env_path = project_root / ".env"
load_dotenv(env_path)

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.domain.models import StockMaster  # noqa: E402
from jobs.collectors.jquants_client import JQuantsClient  # noqa: E402


def fetch_and_save_stock_master():
    """銘柄マスタを取得してDBに保存"""

    print("🔄 銘柄マスタ取得開始...")

    # 1. APIクライアント初期化
    try:
        client = JQuantsClient()
        print("✅ J-Quants APIクライアント初期化成功")
    except ValueError as e:
        print(f"❌ APIキーが設定されていません: {e}")
        return

    # 2. 銘柄マスタ取得
    print("\n🔄 J-Quants API から銘柄マスタ取得中...")
    df = client.get_equities_master()
    print(f"✅ 銘柄マスタ取得成功: {len(df)}銘柄")

    # 3. DB接続
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URLが設定されていません")
        return

    # 非同期版のURL（+asyncpg）を同期版に変換
    database_url = database_url.replace("+asyncpg", "")

    engine = create_engine(database_url)
    print("✅ DB接続成功")

    # 4. データ保存
    print("\n🔄 DBに保存中...")
    session = Session(engine)

    try:
        inserted_count = 0
        updated_count = 0
        skipped_count = 0

        for _, row in df.iterrows():
            stock_code = row["Code"]

            # 既存データ確認
            existing = session.execute(
                select(StockMaster).where(StockMaster.stock_code == stock_code)
            ).scalar_one_or_none()

            # APIのDate（情報適用年月日）
            info_date = row["Date"].date() if hasattr(row["Date"], "date") else row["Date"]

            if existing is None:
                # 新規追加
                stock = StockMaster(
                    stock_code=stock_code,
                    company_name=row["CoName"],
                    company_name_en=row.get("CoNameEn"),
                    sector_code=row.get("S33"),
                    sector17_code=row.get("S17"),
                    market_code=row.get("Mkt"),
                    scale_category=row.get("ScaleCat") if row.get("ScaleCat") != "-" else None,
                    margin_code=row.get("Mrgn"),
                    info_date=info_date,
                    is_active=True,
                    is_nikkei225=False,  # TODO: 判定ロジック実装
                    is_topix=False,  # TODO: 判定ロジック実装
                    is_topix_core30=False,  # TODO: 判定ロジック実装
                    is_jpx400=False,  # TODO: 判定ロジック実装
                    fetched_at=datetime.now(),
                )
                session.add(stock)
                inserted_count += 1

            elif existing.info_date is None or existing.info_date < info_date:
                # 更新（info_dateが新しい場合のみ）
                existing.company_name = row["CoName"]
                existing.company_name_en = row.get("CoNameEn")
                existing.sector_code = row.get("S33")
                existing.sector17_code = row.get("S17")
                existing.market_code = row.get("Mkt")
                existing.scale_category = (
                    row.get("ScaleCat") if row.get("ScaleCat") != "-" else None
                )
                existing.margin_code = row.get("Mrgn")
                existing.info_date = info_date
                existing.fetched_at = datetime.now()
                updated_count += 1

            else:
                # スキップ（既に最新データ）
                skipped_count += 1

            # 進捗表示（100件ごと）
            if (inserted_count + updated_count + skipped_count) % 100 == 0:
                print(
                    f"  処理中: {inserted_count + updated_count + skipped_count}/{len(df)} "
                    f"(新規: {inserted_count}, 更新: {updated_count}, スキップ: {skipped_count})"
                )

        # コミット
        session.commit()
        print("\n✅ DB保存完了")
        print(f"  - 新規追加: {inserted_count}件")
        print(f"  - 更新: {updated_count}件")
        print(f"  - スキップ: {skipped_count}件")

    except Exception as e:
        session.rollback()
        print(f"\n❌ エラー発生: {e}")
        import traceback

        traceback.print_exc()

    finally:
        session.close()

    print("\n🎉 銘柄マスタ取得完了!")


if __name__ == "__main__":
    fetch_and_save_stock_master()
