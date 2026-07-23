import Link from "next/link";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type Params = Promise<{ round_id: string }>;

async function getRoundDetail(roundId: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/history/${roundId}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch round detail");
  }

  return res.json();
}

export default async function RoundDetailPage({ params }: { params: Params }) {
  const { round_id } = await params;
  const data = await getRoundDetail(round_id);

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const weekday = ["日", "月", "火", "水", "木", "金", "土"][date.getDay()];
    return `${month}月${day}日（${weekday}）`;
  };

  const isBuy = data.round.round_type === "BUY";

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="container mx-auto space-y-6">
        {/* 戻るボタン */}
        <Link
          href="/history"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          ← 過去の結果に戻る
        </Link>

        {/* ヘッダー */}
        <div>
          <div className="flex items-center gap-4 mb-2">
            <span
              className={`text-lg font-semibold px-3 py-1.5 rounded ${
                isBuy
                  ? "text-emerald-400 bg-emerald-950/40 border border-emerald-500/20"
                  : "text-red-400 bg-red-950/40 border border-red-500/20"
              }`}
            >
              {isBuy ? "BUY" : "SELL"}
            </span>
            <h1 className="text-4xl font-bold bg-gradient-gold bg-clip-text text-transparent">
              {data.round.round_id}
            </h1>
          </div>
          <p className="text-muted-foreground">
            {formatDate(data.round.start_date)} 〜 {formatDate(data.round.end_date)}
          </p>
        </div>

        {/* 推奨銘柄 + 結果テーブル */}
        <div className="rounded-lg border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted/50 border-b border-border">
                <tr>
                  <th className="p-4 text-left font-semibold">順位</th>
                  <th className="p-4 text-left font-semibold">銘柄</th>
                  <th className="p-4 text-right font-semibold">予測騰落率</th>
                  <th className="p-4 text-right font-semibold">実績騰落率</th>
                  <th className="p-4 text-right font-semibold">
                    予測誤差
                    <span className="block text-xs text-muted-foreground font-normal">
                      (小さいほど精度高)
                    </span>
                  </th>
                  <th className="p-4 text-center font-semibold">的中</th>
                  <th className="p-4 text-right font-semibold">信頼度</th>
                </tr>
              </thead>
              <tbody>
                {data.recommendations.map((rec: any) => {
                  const predictionError = Math.abs(rec.prediction_error || 0);

                  // 予測誤差の色分け
                  const getErrorColor = (error: number) => {
                    if (error < 1) return "text-emerald-400";
                    if (error < 3) return "text-muted-foreground";
                    return "text-red-400";
                  };

                  return (
                    <tr
                      key={rec.rank}
                      className="border-b border-border hover:bg-accent/50 transition-colors"
                    >
                      <td className="p-4">
                        <span className="font-mono font-semibold">#{rec.rank}</span>
                      </td>

                      <td className="p-4">
                        <Link href={`/stocks/${rec.stock_code}`} className="hover:underline">
                          <div className="font-semibold">{rec.company_name}</div>
                          <div className="text-sm text-muted-foreground">
                            {rec.stock_code}
                            {rec.sector_name && ` • ${rec.sector_name}`}
                          </div>
                        </Link>
                      </td>

                      <td className="p-4 text-right">
                        <span
                          className={`font-mono font-semibold ${
                            isBuy ? "neon-text-green-sm" : "neon-text-red-sm"
                          }`}
                        >
                          {formatPercent(rec.predicted_return)}
                        </span>
                      </td>

                      <td className="p-4 text-right">
                        {rec.actual_return !== null ? (
                          <span
                            className={`font-mono font-semibold ${
                              rec.actual_return >= 0 ? "text-emerald-400" : "text-red-400"
                            }`}
                          >
                            {formatPercent(rec.actual_return)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>

                      <td className="p-4 text-right">
                        {rec.prediction_error !== null ? (
                          <span className={`font-mono ${getErrorColor(predictionError)}`}>
                            {predictionError.toFixed(2)}%
                          </span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>

                      <td className="p-4 text-center">
                        {rec.prediction_hit !== null ? (
                          <span
                            className={`text-sm font-semibold ${
                              rec.prediction_hit ? "text-emerald-400" : "text-red-400"
                            }`}
                          >
                            {rec.prediction_hit ? "的中" : "外れ"}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>

                      <td className="p-4 text-right">
                        <span className="font-mono text-muted-foreground">
                          {(rec.confidence_score * 100).toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
