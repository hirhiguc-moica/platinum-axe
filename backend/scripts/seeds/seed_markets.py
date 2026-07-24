"""市場マスタのシードデータ（JPX公式コード）"""

# JPX（日本取引所グループ）公式の市場区分コード
# 出典: J-Quants API V2 仕様
MARKETS_DATA = [
    # === 旧市場区分（2022年4月以前） ===
    {
        "market_code": "0101",
        "market_name": "東証一部",
        "market_short_name": "東証一部",
        "market_abbreviation": "東1",
        "market_category": "LEGACY",
        "market_type": "内国株式",
        "sort_order": 11,
    },
    {
        "market_code": "0102",
        "market_name": "東証二部",
        "market_short_name": "東証二部",
        "market_abbreviation": "東2",
        "market_category": "LEGACY",
        "market_type": "内国株式",
        "sort_order": 12,
    },
    {
        "market_code": "0104",
        "market_name": "マザーズ",
        "market_short_name": "マザーズ",
        "market_abbreviation": "MTH",
        "market_category": "LEGACY",
        "market_type": "内国株式",
        "sort_order": 14,
    },
    {
        "market_code": "0106",
        "market_name": "JASDAQ スタンダード",
        "market_short_name": "JASDAQ STD",
        "market_abbreviation": "JQ-STD",
        "market_category": "LEGACY",
        "market_type": "内国株式",
        "sort_order": 16,
    },
    {
        "market_code": "0107",
        "market_name": "JASDAQ グロース",
        "market_short_name": "JASDAQ GRW",
        "market_abbreviation": "JQ-GRW",
        "market_category": "LEGACY",
        "market_type": "内国株式",
        "sort_order": 17,
    },
    # === 新市場区分（2022年4月以降） ===
    {
        "market_code": "0111",
        "market_name": "プライム",
        "market_short_name": "プライム",
        "market_abbreviation": "PR",
        "market_category": "PRIME",
        "market_type": "内国株式",
        "sort_order": 1,
    },
    {
        "market_code": "0112",
        "market_name": "スタンダード",
        "market_short_name": "スタンダード",
        "market_abbreviation": "ST",
        "market_category": "STANDARD",
        "market_type": "内国株式",
        "sort_order": 2,
    },
    {
        "market_code": "0113",
        "market_name": "グロース",
        "market_short_name": "グロース",
        "market_abbreviation": "GR",
        "market_category": "GROWTH",
        "market_type": "内国株式",
        "sort_order": 3,
    },
    # === その他 ===
    {
        "market_code": "0105",
        "market_name": "TOKYO PRO MARKET",
        "market_short_name": "PRO Market",
        "market_abbreviation": "PRO",
        "market_category": "OTHER",
        "market_type": "内国株式",
        "sort_order": 15,
    },
    {
        "market_code": "0109",
        "market_name": "その他",
        "market_short_name": "その他",
        "market_abbreviation": "OTHER",
        "market_category": "OTHER",
        "market_type": "内国株式",
        "sort_order": 99,
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
