import { notFound } from "next/navigation";
import type {
  GetRoundsResponse,
  GetRoundRecommendationsResponse,
} from "@/generated/types.gen";
import { RecommendationCard } from "@/app/_components/RecommendationCard";
import { StockSearch } from "@/app/_components/StockSearch";

const API_URL = process.env.API_URL || "http://localhost:8000";

// 直近のラウンド結果の型定義
interface LatestRoundResult {
  round_id: string;
  start_date: string;
  end_date: string;
  avg_predicted_return: number;
  avg_actual_return: number;
  hit_rate: number;
  total_recommendations: number;
}

interface GetLatestResultsResponse {
  buy_latest: LatestRoundResult | null;
  sell_latest: LatestRoundResult | null;
}

// 有効なフィルタ
const VALID_FILTERS = ["all", "nikkei225", "topix"];

// 日付フォーマット用ヘルパー関数
function formatDateRangeJa(startDate: string, endDate: string): string {
  const dayOfWeekJa = ["日", "月", "火", "水", "木", "金", "土"];

  const start = new Date(startDate);
  const end = new Date(endDate);

  const startMonth = start.getMonth() + 1;
  const startDay = start.getDate();
  const startDayOfWeek = dayOfWeekJa[start.getDay()];

  const endMonth = end.getMonth() + 1;
  const endDay = end.getDate();
  const endDayOfWeek = dayOfWeekJa[end.getDay()];

  return `${startMonth}月${startDay}日（${startDayOfWeek}）〜 ${endMonth}月${endDay}日（${endDayOfWeek}）`;
}

// 次の土曜日を計算（予測更新日）
function getNextSaturday(endDate: string): string {
  const dayOfWeekJa = ["日", "月", "火", "水", "木", "金", "土"];

  const end = new Date(endDate);
  // 金曜終了日の翌日（土曜）を次回更新日とする
  const nextSaturday = new Date(end);
  nextSaturday.setDate(end.getDate() + 1);

  const month = nextSaturday.getMonth() + 1;
  const day = nextSaturday.getDate();
  const dayOfWeek = dayOfWeekJa[nextSaturday.getDay()];

  return `${month}月${day}日（${dayOfWeek}）`;
}

// フィルタ名の日本語表示
const FILTER_LABELS: Record<string, string> = {
  all: "総合ランキング",
  nikkei225: "💎 日経225",
  topix: "📊 TOPIX",
};

async function getRounds(): Promise<GetRoundsResponse> {
  const res = await fetch(`${API_URL}/api/v1/rounds`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch rounds");
  }

  return res.json();
}

async function getRoundRecommendations(
  roundId: string
): Promise<GetRoundRecommendationsResponse> {
  const res = await fetch(
    `${API_URL}/api/v1/rounds/${roundId}/recommendations`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error("Failed to fetch recommendations");
  }

  return res.json();
}

async function getLatestResults(
  indexFilter: string
): Promise<GetLatestResultsResponse> {
  const res = await fetch(
    `${API_URL}/api/v1/history/latest?index_filter=${indexFilter}`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error("Failed to fetch latest results");
  }

  return res.json();
}

export default async function RecommendationPage({
  params,
}: {
  params: Promise<{ filter: string }>;
}) {
  const { filter } = await params;

  // バリデーション
  if (!VALID_FILTERS.includes(filter)) {
    notFound();
  }

  // ラウンド取得
  const roundsData = await getRounds();
  const buyRound = roundsData.rounds?.find((r) => r.round_type === "BUY");
  const sellRound = roundsData.rounds?.find((r) => r.round_type === "SELL");

  if (!buyRound || !sellRound) {
    return (
      <div className="container mx-auto py-8 px-4">
        <p className="text-center text-muted-foreground">
          ラウンドデータがありません
        </p>
      </div>
    );
  }

  // 買い推奨銘柄取得
  const buyRecommendationsData = await getRoundRecommendations(
    buyRound.round_id
  );

  // 売り推奨銘柄取得
  const sellRecommendationsData = await getRoundRecommendations(
    sellRound.round_id
  );

  // 先週の実績取得
  const latestResults = await getLatestResults(filter);

  // フィルタリング
  const filterRecommendations = (recommendations: any[]) => {
    if (filter === "nikkei225") {
      return recommendations.filter((rec) => rec.stock?.is_nikkei225);
    } else if (filter === "topix") {
      return recommendations.filter((rec) => rec.stock?.is_topix);
    }
    return recommendations;
  };

  const filteredBuyRecommendations = filterRecommendations(
    buyRecommendationsData.recommendations
  );
  const filteredSellRecommendations = filterRecommendations(
    sellRecommendationsData.recommendations
  );

  return (
    <div className="container mx-auto py-8 px-4">
      {/* SP用検索ボックス */}
      <div className="block md:hidden mb-6">
        <StockSearch />
      </div>

      {/* サイト説明 */}
      <div className="mb-6">
        <div className="bg-card/50 border border-border rounded-lg p-4 text-sm">
          <p className="text-foreground mb-2">
            <span className="font-bold text-accent">クオンツ × AI</span> による<span className="font-semibold">週次スイング取引</span>の推奨銘柄。機械学習（LightGBM）で週次騰落率を予測し、買い推奨は上昇が期待される銘柄を、売り推奨は下落が期待される銘柄をランキング形式で表示しています。
          </p>
          <div className="flex items-center justify-end">
            <a
              href="/about"
              className="text-xs text-accent hover:text-accent/80 underline"
            >
              このページの使い方 →
            </a>
          </div>
        </div>
      </div>

      {/* ページタイトル */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-6 bg-gradient-to-r from-accent via-yellow-400 to-accent bg-clip-text text-transparent">
          {FILTER_LABELS[filter]}
        </h1>
      </div>

      {/* 先週の実績 */}
      {(latestResults.buy_latest || latestResults.sell_latest) && (
        <section className="mb-8">
          <div className="bg-card border border-border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">📊 先週の実績</h2>
              <a
                href="/history"
                className="text-sm text-accent hover:text-accent/80 underline"
              >
                過去の結果を見る →
              </a>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 買い推奨の実績 */}
              {latestResults.buy_latest && (
                <div className="space-y-3 bg-emerald-950/20 border border-emerald-500/20 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-emerald-400">
                    買い推奨の実績
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">
                        平均騰落率
                      </span>
                      <span className="text-2xl font-bold text-emerald-400 neon-text-sm">
                        {latestResults.buy_latest.avg_actual_return >= 0
                          ? "+"
                          : ""}
                        {latestResults.buy_latest.avg_actual_return.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">
                        的中率
                      </span>
                      <span className="text-lg font-bold text-foreground">
                        {(
                          latestResults.buy_latest.hit_rate *
                          latestResults.buy_latest.total_recommendations
                        ).toFixed(0)}
                        /{latestResults.buy_latest.total_recommendations}{" "}
                        <span className="text-emerald-400">
                          ({(latestResults.buy_latest.hit_rate * 100).toFixed(0)}
                          %)
                        </span>
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* 売り推奨の実績 */}
              {latestResults.sell_latest && (
                <div className="space-y-3 bg-red-950/20 border border-red-500/20 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-red-400">
                    売り推奨の実績
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">
                        平均騰落率
                      </span>
                      <span className="text-2xl font-bold text-red-400 neon-text-sm">
                        {latestResults.sell_latest.avg_actual_return >= 0
                          ? "+"
                          : ""}
                        {latestResults.sell_latest.avg_actual_return.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">
                        的中率
                      </span>
                      <span className="text-lg font-bold text-foreground">
                        {(
                          latestResults.sell_latest.hit_rate *
                          latestResults.sell_latest.total_recommendations
                        ).toFixed(0)}
                        /{latestResults.sell_latest.total_recommendations}{" "}
                        <span className="text-red-400">
                          ({(latestResults.sell_latest.hit_rate * 100).toFixed(0)}
                          %)
                        </span>
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* 買い推奨セクション */}
      <section className="mb-12">
        <div className="mb-6">
          <h2 className="text-3xl font-bold mb-4 flex items-center gap-3">
            <span className="neon-text-green">📈 買い推奨</span>
          </h2>
          {/* 予測期間 */}
          <div className="bg-gradient-to-r from-emerald-950/50 to-emerald-900/30 border border-emerald-500/30 rounded-lg p-4 shadow-lg shadow-emerald-500/20">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📅</span>
              <div className="flex-1 space-y-3">
                <div>
                  <p className="text-xs text-emerald-400/70 mb-1">予測期間</p>
                  <p className="text-xl font-bold text-emerald-50">
                    {formatDateRangeJa(buyRound.start_date, buyRound.end_date)}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 neon-pulse"></span>
                    <span className="text-sm font-semibold text-emerald-400 neon-text-sm">現在予測中</span>
                  </div>
                  <div className="text-sm text-emerald-300/70">
                    次回更新: <span className="font-medium text-emerald-200">{getNextSaturday(buyRound.end_date)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {filteredBuyRecommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredBuyRecommendations.map((rec) => (
              <RecommendationCard
                key={rec.id}
                recommendation={rec}
                type="BUY"
              />
            ))}
          </div>
        ) : (
          <p className="text-center text-muted-foreground py-12">
            該当する推奨銘柄がありません
          </p>
        )}
      </section>

      {/* 売り推奨セクション */}
      <section>
        <div className="mb-6">
          <h2 className="text-3xl font-bold mb-4 flex items-center gap-3">
            <span className="neon-text-red">📉 売り推奨</span>
          </h2>
          {/* 予測期間 */}
          <div className="bg-gradient-to-r from-red-950/50 to-red-900/30 border border-red-500/30 rounded-lg p-4 shadow-lg shadow-red-500/20">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📅</span>
              <div className="flex-1 space-y-3">
                <div>
                  <p className="text-xs text-red-400/70 mb-1">予測期間</p>
                  <p className="text-xl font-bold text-red-50">
                    {formatDateRangeJa(sellRound.start_date, sellRound.end_date)}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="inline-block w-2 h-2 rounded-full bg-red-400 neon-pulse"></span>
                    <span className="text-sm font-semibold text-red-400 neon-text-sm">現在予測中</span>
                  </div>
                  <div className="text-sm text-red-300/70">
                    次回更新: <span className="font-medium text-red-200">{getNextSaturday(sellRound.end_date)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {filteredSellRecommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredSellRecommendations.map((rec) => (
              <RecommendationCard
                key={rec.id}
                recommendation={rec}
                type="SELL"
              />
            ))}
          </div>
        ) : (
          <p className="text-center text-muted-foreground py-12">
            該当する推奨銘柄がありません
          </p>
        )}
      </section>
    </div>
  );
}
