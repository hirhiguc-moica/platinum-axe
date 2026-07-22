import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { RankBadge } from "./RankBadge";
import type { RoundRecommendationSchema } from "@/generated/types.gen";

interface RecommendationCardProps {
  recommendation: RoundRecommendationSchema;
  type: "BUY" | "SELL";
}

export function RecommendationCard({
  recommendation,
  type,
}: RecommendationCardProps) {
  const {
    rank,
    stock_code,
    predicted_return,
    confidence_score,
    stock,
  } = recommendation;

  const returnPercent = ((predicted_return ?? 0) * 100).toFixed(2);
  const confidencePercent = Math.round((confidence_score ?? 0) * 100);
  const isPositive = (predicted_return ?? 0) >= 0;

  return (
    <Card className="card-hover cursor-pointer transition-all duration-200 hover:scale-[1.02]">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <RankBadge rank={rank} />
          <div className="text-right">
            <div className="text-xs text-muted-foreground mb-1">
              信頼度
            </div>
            <div className="text-sm font-semibold mb-1">
              {confidencePercent}%
            </div>
            <Progress value={confidencePercent} className="w-20 h-2" />
          </div>
        </div>

        <div className="space-y-2 mb-4">
          <div className="text-sm text-muted-foreground">
            {stock_code}
          </div>
          <div className="text-lg font-bold">
            {stock?.company_name}
          </div>
          <div className="text-sm text-muted-foreground">
            {stock?.sector_name} | {stock?.market_name}
          </div>
        </div>

        <div className="flex items-center justify-center py-4">
          <div
            className={`text-4xl font-bold font-mono-num ${
              type === "BUY"
                ? "text-emerald-400 neon-text-green"
                : "text-red-400 neon-text-red"
            }`}
          >
            {isPositive ? "+" : ""}
            {returnPercent}%
          </div>
          <div className="ml-2 text-2xl">
            {type === "BUY" ? "↗" : "↘"}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
