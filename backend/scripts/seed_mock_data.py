"""モックデータ投入スクリプト"""

import asyncio
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domain.models import Round, RoundRecommendation, StockMaster
from app.shared.config import settings


async def seed_data():
    """モックデータを投入"""
    # 非同期エンジン作成
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. 銘柄マスタデータ（サンプル10銘柄）
        stock_master_data = [
            StockMaster(
                stock_code="7203",
                company_name="トヨタ自動車",
                company_name_en="Toyota Motor Corporation",
                sector_code="3700",  # 輸送用機器
                market_code="PRIME",  # プライム（内国株式）
                listing_date=date(1949, 5, 16),
                is_active=True,
                is_nikkei225=True,
                is_topix=True,
                is_jpx400=True,
                market_cap=45000000.00,
                fetched_at=datetime.now(),
            ),
            StockMaster(
                stock_code="6758",
                company_name="ソニーグループ",
                company_name_en="Sony Group Corporation",
                sector_code="3650",  # 電気機器
                market_code="PRIME",  # プライム（内国株式）
                listing_date=date(1958, 12, 1),
                is_active=True,
                is_nikkei225=True,
                is_topix=True,
                is_jpx400=True,
                market_cap=15000000.00,
                fetched_at=datetime.now(),
            ),
            StockMaster(
                stock_code="9984",
                company_name="ソフトバンクグループ",
                company_name_en="SoftBank Group Corp.",
                sector_code="5250",  # 情報・通信業
                market_code="PRIME",  # プライム（内国株式）
                listing_date=date(1994, 7, 22),
                is_active=True,
                is_nikkei225=True,
                is_topix=True,
                is_jpx400=True,
                market_cap=10000000.00,
                fetched_at=datetime.now(),
            ),
            StockMaster(
                stock_code="6861",
                company_name="キーエンス",
                company_name_en="KEYENCE CORPORATION",
                sector_code="3650",  # 電気機器
                market_code="PRIME",  # プライム（内国株式）
                listing_date=date(1987, 10, 1),
                is_active=True,
                is_nikkei225=True,
                is_topix=True,
                is_jpx400=True,
                market_cap=18000000.00,
                fetched_at=datetime.now(),
            ),
            StockMaster(
                stock_code="8306",
                company_name="三菱UFJフィナンシャル・グループ",
                company_name_en="Mitsubishi UFJ Financial Group, Inc.",
                sector_code="7050",  # 銀行業
                market_code="PRIME",  # プライム（内国株式）
                listing_date=date(2001, 4, 2),
                is_active=True,
                is_nikkei225=True,
                is_topix=True,
                is_jpx400=True,
                market_cap=12000000.00,
                fetched_at=datetime.now(),
            ),
            StockMaster(
                stock_code="9432",
                company_name="日本電信電話",
                company_name_en="NIPPON TELEGRAPH AND TELEPHONE CORPORATION",
                sector_code="5250",  # 情報・通信業
                market_code="PRIME",  # プライム（内国株式）
                listing_date=date(1987, 2, 9),
                is_active=True,
                is_nikkei225=True,
                is_topix=True,
                is_jpx400=True,
                market_cap=16000000.00,
                fetched_at=datetime.now(),
            ),
            StockMaster(
                stock_code="4063",
                company_name="信越化学工業",
                company_name_en="Shin-Etsu Chemical Co., Ltd.",
                sector_code="3200",  # 化学
                market_code="PRIME",  # プライム（内国株式）
                listing_date=date(1949, 5, 16),
                is_active=True,
                is_nikkei225=True,
                is_topix=True,
                is_jpx400=True,
                market_cap=8000000.00,
                fetched_at=datetime.now(),
            ),
            StockMaster(
                stock_code="7974",
                company_name="任天堂",
                company_name_en="Nintendo Co., Ltd.",
                sector_code="3650",  # 電気機器
                market_code="PRIME",  # プライム（内国株式）
                listing_date=date(1962, 1, 16),
                is_active=True,
                is_nikkei225=True,
                is_topix=True,
                is_jpx400=True,
                market_cap=9000000.00,
                fetched_at=datetime.now(),
            ),
            StockMaster(
                stock_code="6098",
                company_name="リクルートホールディングス",
                company_name_en="Recruit Holdings Co., Ltd.",
                sector_code="9050",  # サービス業
                market_code="PRIME",  # プライム（内国株式）
                listing_date=date(2014, 10, 16),
                is_active=True,
                is_nikkei225=True,
                is_topix=True,
                is_jpx400=True,
                market_cap=11000000.00,
                fetched_at=datetime.now(),
            ),
            StockMaster(
                stock_code="4502",
                company_name="武田薬品工業",
                company_name_en="Takeda Pharmaceutical Company Limited",
                sector_code="3250",  # 医薬品
                market_code="PRIME",  # プライム（内国株式）
                listing_date=date(1949, 5, 16),
                is_active=True,
                is_nikkei225=True,
                is_topix=True,
                is_jpx400=True,
                market_cap=7000000.00,
                fetched_at=datetime.now(),
            ),
        ]

        session.add_all(stock_master_data)
        await session.flush()

        # 2. ラウンドデータ（サンプル：今週のBUYラウンド）
        round_buy = Round(
            round_id="2026-W30-BUY",
            round_type="BUY",
            start_date=date(2026, 7, 20),  # 月曜
            end_date=date(2026, 7, 24),  # 金曜
            status="ACTIVE",
            model_version="v1.0.0",
            feature_version="v1",
            prediction_date=date(2026, 7, 19),
        )

        round_sell = Round(
            round_id="2026-W30-SELL",
            round_type="SELL",
            start_date=date(2026, 7, 20),
            end_date=date(2026, 7, 24),
            status="ACTIVE",
            model_version="v1.0.0",
            feature_version="v1",
            prediction_date=date(2026, 7, 19),
        )

        session.add_all([round_buy, round_sell])
        await session.flush()  # UUID生成のためflush

        # 3. ラウンド推奨銘柄データ（BUY Top 5）
        buy_recommendations = [
            RoundRecommendation(
                round_id=round_buy.id,  # UUID
                stock_code="7203",
                rank=1,
                predicted_return=0.0850,  # +8.5%
                confidence_score=0.9200,
                reason_features={
                    "rsi": 35.5,
                    "macd_signal": "BUY",
                    "volume_trend": "UP",
                    "sector_momentum": "STRONG",
                },
            ),
            RoundRecommendation(
                round_id=round_buy.id,  # UUID
                stock_code="6861",
                rank=2,
                predicted_return=0.0720,  # +7.2%
                confidence_score=0.8900,
                reason_features={
                    "rsi": 42.0,
                    "macd_signal": "BUY",
                    "revenue_growth": 0.15,
                },
            ),
            RoundRecommendation(
                round_id=round_buy.id,  # UUID
                stock_code="6758",
                rank=3,
                predicted_return=0.0680,  # +6.8%
                confidence_score=0.8700,
                reason_features={"rsi": 38.5, "pe_ratio": 12.5, "sector_momentum": "UP"},
            ),
            RoundRecommendation(
                round_id=round_buy.id,  # UUID
                stock_code="9984",
                rank=4,
                predicted_return=0.0620,  # +6.2%
                confidence_score=0.8500,
                reason_features={"volume_trend": "UP", "macd_signal": "BUY"},
            ),
            RoundRecommendation(
                round_id=round_buy.id,  # UUID
                stock_code="6098",
                rank=5,
                predicted_return=0.0590,  # +5.9%
                confidence_score=0.8300,
                reason_features={"rsi": 40.0, "revenue_growth": 0.12},
            ),
        ]

        # SELL Top 5
        sell_recommendations = [
            RoundRecommendation(
                round_id=round_sell.id,  # UUID
                stock_code="8306",
                rank=1,
                predicted_return=-0.0650,  # -6.5%
                confidence_score=0.8800,
                reason_features={"rsi": 72.0, "macd_signal": "SELL", "volume_trend": "DOWN"},
            ),
            RoundRecommendation(
                round_id=round_sell.id,  # UUID
                stock_code="9432",
                rank=2,
                predicted_return=-0.0580,  # -5.8%
                confidence_score=0.8600,
                reason_features={"rsi": 68.5, "pe_ratio": 25.0},
            ),
            RoundRecommendation(
                round_id=round_sell.id,  # UUID
                stock_code="4502",
                rank=3,
                predicted_return=-0.0520,  # -5.2%
                confidence_score=0.8400,
                reason_features={"macd_signal": "SELL", "sector_momentum": "WEAK"},
            ),
            RoundRecommendation(
                round_id=round_sell.id,  # UUID
                stock_code="7974",
                rank=4,
                predicted_return=-0.0480,  # -4.8%
                confidence_score=0.8200,
                reason_features={"rsi": 65.0, "volume_trend": "DOWN"},
            ),
            RoundRecommendation(
                round_id=round_sell.id,  # UUID
                stock_code="4063",
                rank=5,
                predicted_return=-0.0420,  # -4.2%
                confidence_score=0.8000,
                reason_features={"rsi": 70.0, "sector_momentum": "DOWN"},
            ),
        ]

        session.add_all(buy_recommendations + sell_recommendations)

        # コミット
        await session.commit()

        print("✅ モックデータ投入完了")
        print(f"   - 銘柄マスタ: {len(stock_master_data)}件")
        print(f"   - ラウンド: 2件（BUY/SELL）")
        print(f"   - 推奨銘柄: {len(buy_recommendations + sell_recommendations)}件")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())
