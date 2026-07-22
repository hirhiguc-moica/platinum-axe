import { notFound } from "next/navigation";
import type {
  GetRoundsResponse,
  GetRoundRecommendationsResponse,
} from "@/generated/types.gen";
import { FilterTabs } from "@/app/_components/FilterTabs";
import { RecommendationCard } from "@/app/_components/RecommendationCard";

const API_URL = process.env.API_URL || "http://localhost:8000";

// 有効なフィルタとタイプ
const VALID_FILTERS = ["all", "nikkei225", "topix"];
const VALID_TYPES = ["buy", "sell"];

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

export default async function RecommendationPage({
  params,
}: {
  params: Promise<{ filter: string; type: string }>;
}) {
  const { filter, type } = await params;

  // バリデーション
  if (!VALID_FILTERS.includes(filter) || !VALID_TYPES.includes(type)) {
    notFound();
  }

  // ラウンド取得
  const roundsData = await getRounds();
  const roundType = type.toUpperCase();
  const targetRound = roundsData.rounds?.find(
    (r) => r.round_type === roundType
  );

  if (!targetRound) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-center text-muted-foreground">
          ラウンドデータがありません
        </p>
      </div>
    );
  }

  // 推奨銘柄取得
  const recommendationsData = await getRoundRecommendations(
    targetRound.round_id
  );

  // フィルタリング
  let filteredRecommendations = recommendationsData.recommendations;

  if (filter === "nikkei225") {
    filteredRecommendations = filteredRecommendations.filter(
      (rec) => rec.stock?.is_nikkei225
    );
  } else if (filter === "topix") {
    filteredRecommendations = filteredRecommendations.filter(
      (rec) => rec.stock?.is_topix
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">
          {FILTER_LABELS[filter]}の{type === "buy" ? "買い" : "売り"}推奨
        </h1>
        <p className="text-muted-foreground mb-4">
          {targetRound.start_date} 〜 {targetRound.end_date} (
          {targetRound.round_id})
        </p>
        <div className="bg-card/50 border border-border rounded-lg p-4 text-sm text-muted-foreground">
          <p>
            機械学習（LightGBM）による日本株の週次騰落率予測です。
            {type === "buy" ? "買い推奨" : "売り推奨"}は今週
            {type === "buy" ? "上昇" : "下落"}
            が期待される銘柄をランキング形式で表示しています。
          </p>
        </div>
      </div>

      {/* BUY/SELL切り替えタブ */}
      <div className="mb-6">
        <FilterTabs filter={filter} />
      </div>

      {/* 推奨銘柄一覧 */}
      {filteredRecommendations.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRecommendations.map((rec) => (
            <RecommendationCard
              key={rec.id}
              recommendation={rec}
              type={type.toUpperCase() as "BUY" | "SELL"}
            />
          ))}
        </div>
      ) : (
        <p className="text-center text-muted-foreground py-12">
          該当する推奨銘柄がありません
        </p>
      )}
    </div>
  );
}
