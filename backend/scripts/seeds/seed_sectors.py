"""業種マスタ（33業種分類）のシードデータ"""

# J-Quants API / 東証33業種分類
SECTORS_DATA = [
    {
        "sector_code": "0050",
        "sector_name": "水産・農林業",
        "sector_name_en": "Fishery, Agriculture & Forestry",
    },
    {"sector_code": "1050", "sector_name": "鉱業", "sector_name_en": "Mining"},
    {"sector_code": "2050", "sector_name": "建設業", "sector_name_en": "Construction"},
    {"sector_code": "3050", "sector_name": "食料品", "sector_name_en": "Foods"},
    {"sector_code": "3100", "sector_name": "繊維製品", "sector_name_en": "Textiles & Apparels"},
    {"sector_code": "3150", "sector_name": "パルプ・紙", "sector_name_en": "Pulp & Paper"},
    {"sector_code": "3200", "sector_name": "化学", "sector_name_en": "Chemicals"},
    {"sector_code": "3250", "sector_name": "医薬品", "sector_name_en": "Pharmaceutical"},
    {
        "sector_code": "3300",
        "sector_name": "石油・石炭製品",
        "sector_name_en": "Oil & Coal Products",
    },
    {"sector_code": "3350", "sector_name": "ゴム製品", "sector_name_en": "Rubber Products"},
    {
        "sector_code": "3400",
        "sector_name": "ガラス・土石製品",
        "sector_name_en": "Glass & Ceramics Products",
    },
    {"sector_code": "3450", "sector_name": "鉄鋼", "sector_name_en": "Iron & Steel"},
    {"sector_code": "3500", "sector_name": "非鉄金属", "sector_name_en": "Nonferrous Metals"},
    {"sector_code": "3550", "sector_name": "金属製品", "sector_name_en": "Metal Products"},
    {"sector_code": "3600", "sector_name": "機械", "sector_name_en": "Machinery"},
    {"sector_code": "3650", "sector_name": "電気機器", "sector_name_en": "Electric Appliances"},
    {
        "sector_code": "3700",
        "sector_name": "輸送用機器",
        "sector_name_en": "Transportation Equipment",
    },
    {"sector_code": "3750", "sector_name": "精密機器", "sector_name_en": "Precision Instruments"},
    {"sector_code": "3800", "sector_name": "その他製品", "sector_name_en": "Other Products"},
    {
        "sector_code": "4050",
        "sector_name": "電気・ガス業",
        "sector_name_en": "Electric Power & Gas",
    },
    {"sector_code": "5050", "sector_name": "陸運業", "sector_name_en": "Land Transportation"},
    {"sector_code": "5100", "sector_name": "海運業", "sector_name_en": "Marine Transportation"},
    {"sector_code": "5150", "sector_name": "空運業", "sector_name_en": "Air Transportation"},
    {
        "sector_code": "5200",
        "sector_name": "倉庫・運輸関連業",
        "sector_name_en": "Warehousing & Harbor Transportation Services",
    },
    {
        "sector_code": "5250",
        "sector_name": "情報・通信業",
        "sector_name_en": "Information & Communication",
    },
    {"sector_code": "6050", "sector_name": "卸売業", "sector_name_en": "Wholesale Trade"},
    {"sector_code": "6100", "sector_name": "小売業", "sector_name_en": "Retail Trade"},
    {"sector_code": "7050", "sector_name": "銀行業", "sector_name_en": "Banks"},
    {
        "sector_code": "7100",
        "sector_name": "証券、商品先物取引業",
        "sector_name_en": "Securities & Commodity Futures",
    },
    {"sector_code": "7150", "sector_name": "保険業", "sector_name_en": "Insurance"},
    {
        "sector_code": "7200",
        "sector_name": "その他金融業",
        "sector_name_en": "Other Financing Business",
    },
    {"sector_code": "8050", "sector_name": "不動産業", "sector_name_en": "Real Estate"},
    {"sector_code": "9050", "sector_name": "サービス業", "sector_name_en": "Services"},
    # その他（業種分類なし: ETF、REIT、優先株式等）
    {
        "sector_code": "9999",
        "sector_name": "その他（業種なし）",
        "sector_name_en": "Other (No Sector)",
    },
]


async def seed_sectors(session):
    """業種マスタデータ投入"""
    from app.domain.models import Sector

    for data in SECTORS_DATA:
        sector = Sector(
            sector_code=data["sector_code"],
            sector_name=data["sector_name"],
            sector_name_en=data["sector_name_en"],
        )
        session.add(sector)

    await session.commit()
    print(f"✅ {len(SECTORS_DATA)}件の業種データを投入しました")


if __name__ == "__main__":
    import asyncio

    from app.infrastructure.database import AsyncSessionLocal

    async def main():
        async with AsyncSessionLocal() as session:
            await seed_sectors(session)

    asyncio.run(main())
