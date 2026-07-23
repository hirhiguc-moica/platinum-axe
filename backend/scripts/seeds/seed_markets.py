"""市場マスタのシードデータ"""

# 東証市場区分（2022年4月再編後）
MARKETS_DATA = [
    # プライム市場
    {
        "market_code": "PRIME",
        "market_name": "プライム（内国株式）",
        "market_short_name": "プライム",
        "market_abbreviation": "PR",
        "market_category": "PRIME",
        "market_type": "内国株式",
        "sort_order": 1,
    },
    {
        "market_code": "PRIME_F",
        "market_name": "プライム（外国株式）",
        "market_short_name": "プライム外国",
        "market_abbreviation": "PR(外)",
        "market_category": "PRIME",
        "market_type": "外国株式",
        "sort_order": 4,
    },
    # スタンダード市場
    {
        "market_code": "STANDARD",
        "market_name": "スタンダード（内国株式）",
        "market_short_name": "スタンダード",
        "market_abbreviation": "ST",
        "market_category": "STANDARD",
        "market_type": "内国株式",
        "sort_order": 2,
    },
    {
        "market_code": "STANDARD_F",
        "market_name": "スタンダード（外国株式）",
        "market_short_name": "スタンダード外国",
        "market_abbreviation": "ST(外)",
        "market_category": "STANDARD",
        "market_type": "外国株式",
        "sort_order": 5,
    },
    # グロース市場
    {
        "market_code": "GROWTH",
        "market_name": "グロース（内国株式）",
        "market_short_name": "グロース",
        "market_abbreviation": "GR",
        "market_category": "GROWTH",
        "market_type": "内国株式",
        "sort_order": 3,
    },
    {
        "market_code": "GROWTH_F",
        "market_name": "グロース（外国株式）",
        "market_short_name": "グロース外国",
        "market_abbreviation": "GR(外)",
        "market_category": "GROWTH",
        "market_type": "外国株式",
        "sort_order": 6,
    },
]


async def seed_markets(session):
    """市場マスタデータ投入"""
    from app.domain.models import Market

    for data in MARKETS_DATA:
        market = Market(
            market_code=data["market_code"],
            market_name=data["market_name"],
            market_short_name=data["market_short_name"],
            market_abbreviation=data["market_abbreviation"],
            market_category=data["market_category"],
            market_type=data["market_type"],
            sort_order=data["sort_order"],
        )
        session.add(market)

    await session.commit()
    print(f"✅ {len(MARKETS_DATA)}件の市場マスタデータを投入しました")


if __name__ == "__main__":
    import asyncio

    from app.infrastructure.database import AsyncSessionLocal

    async def main():
        async with AsyncSessionLocal() as session:
            await seed_markets(session)

    asyncio.run(main())
