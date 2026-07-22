"""過去のラウンド結果モックデータ生成

過去15週分のラウンド（BUY/SELL × 15週 = 30ラウンド）のモックデータを生成
"""

import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domain.models.round import Round, RoundRecommendation
from app.domain.models.round_result import RoundResult
from app.shared.config import settings


def get_week_dates(year: int, week: int) -> tuple[date, date]:
    """週番号から月曜日と金曜日の日付を取得"""
    # ISO week date から日付を計算
    jan4 = date(year, 1, 4)
    week_one_monday = jan4 - timedelta(days=jan4.weekday())
    target_monday = week_one_monday + timedelta(weeks=week - 1)
    target_friday = target_monday + timedelta(days=4)
    return target_monday, target_friday


def generate_round_data(
    week_num: int, year: int, round_type: str, stock_codes: list[str]
) -> tuple[Round, list[RoundRecommendation], list[RoundResult]]:
    """1ラウンド分のデータを生成"""
    start_date, end_date = get_week_dates(year, week_num)
    round_id_str = f"{year}-W{week_num:02d}-{round_type}"

    # Round作成
    round_obj = Round(
        round_id=round_id_str,
        round_type=round_type,
        start_date=start_date,
        end_date=end_date,
        status="CLOSED",
        model_version="v1.0.0",
        feature_version="v1",
        prediction_date=start_date - timedelta(days=2),  # 土曜日に予測
    )

    # 推奨銘柄をランダムに10銘柄選択（重複なし）
    selected_stocks = random.sample(stock_codes, 10)

    recommendations = []
    results = []

    for rank, stock_code in enumerate(selected_stocks, start=1):
        # 予測騰落率生成
        if round_type == "BUY":
            # BUY: 1.0% ~ 8.0%
            predicted_return = Decimal(str(round(random.uniform(1.0, 8.0), 4)))
        else:  # SELL
            # SELL: -8.0% ~ -1.0%
            predicted_return = Decimal(str(round(random.uniform(-8.0, -1.0), 4)))

        # 信頼度スコア: 0.70 ~ 0.95
        confidence_score = Decimal(str(round(random.uniform(0.70, 0.95), 4)))

        # 推奨銘柄データ
        recommendation = RoundRecommendation(
            stock_code=stock_code,
            rank=rank,
            predicted_return=predicted_return,
            confidence_score=confidence_score,
            reason_features={
                "top_features": [
                    {"name": "RSI_14", "importance": 0.25},
                    {"name": "MACD", "importance": 0.20},
                    {"name": "Volume_Ratio", "importance": 0.15},
                ]
            },
        )
        recommendations.append(recommendation)

        # 実績データ生成
        # 的中率60-70%程度になるよう調整
        is_hit = random.random() < 0.65  # 65%の確率で的中

        if is_hit:
            # 的中: 予測と同じ符号、誤差は±30%程度
            error_ratio = random.uniform(-0.3, 0.3)
            actual_return = predicted_return * Decimal(str(1 + error_ratio))
        else:
            # 外れ: 予測と逆の符号、または大きく外れる
            if round_type == "BUY":
                # BUY予測が外れ → マイナスになる
                actual_return = Decimal(str(round(random.uniform(-3.0, -0.5), 4)))
            else:  # SELL
                # SELL予測が外れ → プラスになる
                actual_return = Decimal(str(round(random.uniform(0.5, 3.0), 4)))

        # 予測誤差
        prediction_error = actual_return - predicted_return

        # 株価データ生成（1000円〜10000円）
        start_price = Decimal(str(round(random.uniform(1000, 10000), 2)))
        end_price = start_price * (Decimal("1") + actual_return / Decimal("100"))
        end_price = Decimal(str(round(float(end_price), 2)))

        # 期間中の最高値・最安値（start/endの±5%程度）
        price_range = float(start_price) * 0.05
        highest_price = Decimal(
            str(round(max(float(start_price), float(end_price)) + random.uniform(0, price_range), 2))
        )
        lowest_price = Decimal(
            str(round(min(float(start_price), float(end_price)) - random.uniform(0, price_range), 2))
        )

        # 損益計算（100株投資と仮定）
        entry_shares = 100
        profit_loss = (end_price - start_price) * entry_shares
        profit_loss_rate = actual_return  # 騰落率 = 損益率

        # 結果データ
        result = RoundResult(
            stock_code=stock_code,
            start_price=start_price,
            end_price=end_price,
            highest_price=highest_price,
            lowest_price=lowest_price,
            actual_return=actual_return,
            predicted_return=predicted_return,
            prediction_error=prediction_error,
            prediction_hit=is_hit,
            entry_shares=entry_shares,
            profit_loss=profit_loss,
            profit_loss_rate=profit_loss_rate,
        )
        results.append(result)

    return round_obj, recommendations, results


async def seed_round_history():
    """過去15週分のラウンド結果データを投入"""

    # 既存の銘柄コード（10銘柄）
    stock_codes = [
        "7203",  # トヨタ自動車
        "6758",  # ソニーグループ
        "9984",  # SoftBankグループ
        "7974",  # 任天堂
        "6861",  # キーエンス
        "8035",  # 東京エレクトロン
        "6098",  # リクルートHD
        "9983",  # ファーストリテイリング
        "4063",  # 信越化学工業
        "9433",  # KDDI
    ]

    # 非同期エンジン作成
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        session: AsyncSession

        # 現在の最新ラウンドは 2026-W30
        # 2026-W29から遡って15週分生成（2026-W29 → 2026-W15）
        year = 2026
        start_week = 29
        num_weeks = 15

        for i in range(num_weeks):
            week_num = start_week - i

            # BUYラウンド
            round_buy, recs_buy, results_buy = generate_round_data(
                week_num, year, "BUY", stock_codes
            )
            session.add(round_buy)
            await session.flush()  # round.idを生成

            for rec in recs_buy:
                rec.round_id = round_buy.id
                session.add(rec)

            for result in results_buy:
                result.round_id = round_buy.id
                session.add(result)

            # SELLラウンド
            round_sell, recs_sell, results_sell = generate_round_data(
                week_num, year, "SELL", stock_codes
            )
            session.add(round_sell)
            await session.flush()  # round.idを生成

            for rec in recs_sell:
                rec.round_id = round_sell.id
                session.add(rec)

            for result in results_sell:
                result.round_id = round_sell.id
                session.add(result)

            print(f"✅ Week {week_num} (BUY/SELL) データ生成完了")

        await session.commit()
        print(f"\n🎉 過去{num_weeks}週分のラウンド結果データ投入完了！")
        print(f"   - 総ラウンド数: {num_weeks * 2}件")
        print(f"   - 推奨銘柄数: {num_weeks * 2 * 10}件")
        print(f"   - 結果データ数: {num_weeks * 2 * 10}件")


if __name__ == "__main__":
    asyncio.run(seed_round_history())
