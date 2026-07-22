import { notFound } from "next/navigation";
import Link from "next/link";
import { StockDataTabs } from "./_components/StockDataTabs";
import { RecommendationTabs } from "./_components/RecommendationTabs";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface StockDetailProps {
  params: Promise<{
    stock_code: string;
  }>;
}

async function getStockDetail(stockCode: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/stocks/${stockCode}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    if (res.status === 404) {
      return null;
    }
    throw new Error(`Failed to fetch stock detail: ${res.statusText}`);
  }

  return res.json();
}

async function getStockPrices(stockCode: string) {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/stocks/${stockCode}/prices?limit=240`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error(`Failed to fetch stock prices: ${res.statusText}`);
  }

  return res.json();
}

async function getStockTechnicalIndicatorsFull(stockCode: string) {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/stocks/${stockCode}/technical-indicators/full?limit=240`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error(`Failed to fetch technical indicators: ${res.statusText}`);
  }

  return res.json();
}

async function getStockRecommendations(stockCode: string) {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/stocks/${stockCode}/recommendations`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error(`Failed to fetch recommendations: ${res.statusText}`);
  }

  return res.json();
}

export default async function StockDetailPage({ params }: StockDetailProps) {
  const { stock_code } = await params;

  // 並列データ取得
  const [stockDetail, stockPrices, technicalIndicators, recommendations] =
    await Promise.all([
      getStockDetail(stock_code),
      getStockPrices(stock_code),
      getStockTechnicalIndicatorsFull(stock_code),
      getStockRecommendations(stock_code),
    ]);

  if (!stockDetail) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#1e1e1e] to-[#252526]">
      {/* Header */}
      <div className="border-b border-[#3e3e42] bg-[#252526]/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <Link
            href="/all"
            className="text-sm text-[#858585] hover:text-[#cccccc] transition-colors inline-block mb-2"
          >
            ← 戻る
          </Link>
          <h1 className="text-2xl font-bold text-[#cccccc] mb-1">
            {stockDetail.company_name}
          </h1>
          <div className="flex items-center gap-3 text-xs text-[#858585]">
            <span className="font-mono text-sm">{stockDetail.stock_code}</span>
            {stockDetail.sector_name && <span>• {stockDetail.sector_name}</span>}
            {stockDetail.market_name && <span>• {stockDetail.market_name}</span>}
          </div>

          {/* 指数バッジ */}
          {(stockDetail.is_nikkei225 || stockDetail.is_topix || stockDetail.is_topix_core30 || stockDetail.is_jpx400) && (
            <div className="flex gap-2 mt-3">
              {stockDetail.is_nikkei225 && (
                <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs font-medium rounded-full border border-blue-500/30">
                  日経225
                </span>
              )}
              {stockDetail.is_topix && (
                <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs font-medium rounded-full border border-purple-500/30">
                  TOPIX
                </span>
              )}
              {stockDetail.is_topix_core30 && (
                <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs font-medium rounded-full border border-purple-500/30">
                  TOPIX Core30
                </span>
              )}
              {stockDetail.is_jpx400 && (
                <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs font-medium rounded-full border border-green-500/30">
                  JPX400
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-6">
        {/* 最新株価 */}
        {stockDetail.latest_price && (
          <div className="mb-6 bg-[#252526] border border-[#3e3e42] rounded-lg p-4">
            <h2 className="text-sm font-semibold text-[#cccccc] mb-3">最新株価</h2>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
              <div>
                <div className="text-xs text-[#858585] mb-0.5">日付</div>
                <div className="text-xs font-mono text-[#cccccc]">
                  {stockDetail.latest_price.date}
                </div>
              </div>
              <div>
                <div className="text-xs text-[#858585] mb-0.5">終値</div>
                <div className="text-sm font-mono font-semibold text-[#cccccc]">
                  {stockDetail.latest_price.close?.toLocaleString() || "-"}
                </div>
              </div>
              <div>
                <div className="text-xs text-[#858585] mb-0.5">始値</div>
                <div className="text-xs font-mono text-[#cccccc]">
                  {stockDetail.latest_price.open?.toLocaleString() || "-"}
                </div>
              </div>
              <div>
                <div className="text-xs text-[#858585] mb-0.5">高値</div>
                <div className="text-xs font-mono text-[#cccccc]">
                  {stockDetail.latest_price.high?.toLocaleString() || "-"}
                </div>
              </div>
              <div>
                <div className="text-xs text-[#858585] mb-0.5">安値</div>
                <div className="text-xs font-mono text-[#cccccc]">
                  {stockDetail.latest_price.low?.toLocaleString() || "-"}
                </div>
              </div>
              <div>
                <div className="text-xs text-[#858585] mb-0.5">出来高</div>
                <div className="text-xs font-mono text-[#cccccc]">
                  {stockDetail.latest_price.volume?.toLocaleString() || "-"}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* タブ切り替え（チャート / 株価データ / テクニカル指標） */}
        <div className="mb-6">
          <StockDataTabs
            prices={stockPrices}
            technicalIndicators={technicalIndicators}
          />
        </div>

        {/* 推奨履歴（タブ切り替え: チャート / 詳細） */}
        <RecommendationTabs items={recommendations.items} />
      </div>
    </div>
  );
}
