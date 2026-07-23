"use client";

import { useRouter } from "next/navigation";

interface RoundHistoryRowProps {
  round: {
    round_id: string;
    round_type: string;
    start_date: string;
    end_date: string;
    status: string;
    performance: {
      total_recommendations: number;
      avg_predicted_return: number;
      avg_actual_return: number;
      hit_rate: number;
    };
  };
}

export function RoundHistoryRow({ round }: RoundHistoryRowProps) {
  const router = useRouter();

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  const predictionError = Math.abs(
    round.performance.avg_actual_return - round.performance.avg_predicted_return
  );
  const isBuy = round.round_type === "BUY";

  // 予測誤差の色分け
  const getErrorColor = (error: number) => {
    if (error < 1) return "text-emerald-400";
    if (error < 3) return "text-muted-foreground";
    return "text-red-400";
  };

  const handleClick = () => {
    router.push(`/history/${round.round_id}`);
  };

  return (
    <tr
      onClick={handleClick}
      className="border-b border-border hover:bg-accent/30 hover:shadow-lg cursor-pointer transition-all group"
    >
      <td className="p-4">
        <div className="flex items-center gap-3">
          <span
            className={`text-sm font-semibold px-2 py-1 rounded ${
              isBuy
                ? "text-emerald-400 bg-emerald-950/40 border border-emerald-500/20"
                : "text-red-400 bg-red-950/40 border border-red-500/20"
            }`}
          >
            {isBuy ? "BUY" : "SELL"}
          </span>
          <div>
            <div className="font-semibold">{round.round_id}</div>
            <div className="text-sm text-muted-foreground">
              {formatDate(round.start_date)} 〜 {formatDate(round.end_date)}
            </div>
          </div>
        </div>
      </td>

      <td className="p-4 text-center">
        <span className="font-mono">{round.performance.total_recommendations}</span>
      </td>

      <td className="p-4 text-right">
        <span
          className={`font-mono font-semibold ${isBuy ? "neon-text-green-sm" : "neon-text-red-sm"}`}
        >
          {formatPercent(round.performance.avg_predicted_return)}
        </span>
      </td>

      <td className="p-4 text-right">
        <span
          className={`font-mono font-semibold ${
            round.performance.avg_actual_return >= 0 ? "text-emerald-400" : "text-red-400"
          }`}
        >
          {formatPercent(round.performance.avg_actual_return)}
        </span>
      </td>

      <td className="p-4 text-right">
        <span className={`font-mono ${getErrorColor(predictionError)}`}>
          {predictionError.toFixed(2)}%
        </span>
      </td>

      <td className="p-4 text-center">
        <span className="font-mono font-semibold text-emerald-400">
          {(round.performance.hit_rate * 100).toFixed(0)}%
        </span>
      </td>

      <td className="p-4 text-right opacity-0 group-hover:opacity-100 transition-opacity">
        <span className="text-muted-foreground">→</span>
      </td>
    </tr>
  );
}
