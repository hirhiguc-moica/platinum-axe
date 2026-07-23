import { StockSearch } from "@/app/_components/StockSearch";
import { IndexFilterTabs } from "./_components/IndexFilterTabs";
import { Pagination } from "./_components/Pagination";
import { PerformanceSummary } from "./_components/PerformanceSummary";
import { RoundHistoryTable } from "./_components/RoundHistoryTable";
import { TypeFilterTabs } from "./_components/TypeFilterTabs";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type SearchParams = Promise<{
  round_type?: string;
  index_filter?: string;
  page?: string;
}>;

async function getHistoryData(searchParams: Awaited<SearchParams>) {
  const roundType = searchParams.round_type?.toUpperCase();
  const indexFilter = searchParams.index_filter || "all";
  const page = parseInt(searchParams.page || "1", 10);
  const limit = 10;

  // ラウンド履歴取得
  const historyParams = new URLSearchParams();
  if (roundType && ["BUY", "SELL"].includes(roundType)) {
    historyParams.set("round_type", roundType);
  }
  historyParams.set("index_filter", indexFilter);
  historyParams.set("page", page.toString());
  historyParams.set("limit", limit.toString());

  const historyRes = await fetch(`${API_BASE_URL}/api/v1/history?${historyParams.toString()}`, {
    cache: "no-store",
  });

  if (!historyRes.ok) {
    throw new Error("Failed to fetch history data");
  }

  const historyData = await historyRes.json();

  // パフォーマンスサマリー取得
  const summaryParams = new URLSearchParams({ index_filter: indexFilter });
  const summaryRes = await fetch(
    `${API_BASE_URL}/api/v1/history/summary?${summaryParams.toString()}`,
    { cache: "no-store" }
  );

  if (!summaryRes.ok) {
    throw new Error("Failed to fetch summary data");
  }

  const summaryData = await summaryRes.json();

  return {
    history: historyData,
    summary: summaryData,
    roundType: roundType || null,
    indexFilter,
    page,
  };
}

export default async function HistoryPage({ searchParams }: { searchParams: SearchParams }) {
  const params = await searchParams;
  const data = await getHistoryData(params);

  const currentType = data.roundType ? (data.roundType.toLowerCase() as "buy" | "sell") : "all";

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="container mx-auto space-y-6">
        {/* SP用検索ボックス */}
        <div className="block md:hidden">
          <StockSearch />
        </div>

        {/* ヘッダー */}
        <div>
          <h1 className="text-4xl font-bold mb-2 bg-gradient-gold bg-clip-text text-transparent">
            過去のラウンド結果
          </h1>
          <p className="text-muted-foreground">予測 vs 実績の乖離、的中率を確認できます</p>
        </div>

        {/* 指数フィルター */}
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">指数フィルター:</span>
          <IndexFilterTabs
            currentIndex={data.indexFilter}
            roundType={data.roundType || undefined}
          />
        </div>

        {/* パフォーマンスサマリー */}
        <PerformanceSummary
          buyPerformance={data.summary.buy_performance}
          sellPerformance={data.summary.sell_performance}
        />

        {/* タイプフィルター */}
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">表示:</span>
          <TypeFilterTabs currentType={currentType} indexFilter={data.indexFilter} />
        </div>

        {/* ラウンド履歴テーブル */}
        <RoundHistoryTable rounds={data.history.rounds} />

        {/* ページネーション */}
        <Pagination
          currentPage={data.history.pagination.page}
          totalPages={data.history.pagination.total_pages}
          roundType={data.roundType || undefined}
          indexFilter={data.indexFilter}
        />
      </div>
    </div>
  );
}
