"use client";

interface PerformanceSummaryProps {
  buyPerformance: {
    total_rounds: number;
    avg_hit_rate: number;
    avg_predicted_return: number;
    avg_actual_return: number;
    total_profit_loss: number;
  };
  sellPerformance: {
    total_rounds: number;
    avg_hit_rate: number;
    avg_predicted_return: number;
    avg_actual_return: number;
    total_profit_loss: number;
  };
}

export function PerformanceSummary({ buyPerformance, sellPerformance }: PerformanceSummaryProps) {
  const formatPercent = (value: number) => {
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}%`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      {/* BUY統計 */}
      <div className="relative overflow-hidden rounded-lg border border-emerald-500/20 bg-gradient-to-br from-emerald-950/40 to-emerald-900/20 p-6">
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent" />
        <div className="relative">
          <h3 className="text-lg font-semibold mb-4">
            <span className="neon-text-green">買い推奨の実績</span>
          </h3>

          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">総ラウンド数</span>
              <span className="font-mono font-semibold">{buyPerformance.total_rounds}回</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">的中率</span>
              <span className="font-mono font-semibold text-emerald-400">
                {(buyPerformance.avg_hit_rate * 100).toFixed(1)}%
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">平均予測騰落率</span>
              <span className="font-mono font-semibold neon-text-green">
                {formatPercent(buyPerformance.avg_predicted_return)}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">平均実績騰落率</span>
              <span className="font-mono font-semibold neon-text-green">
                {formatPercent(buyPerformance.avg_actual_return)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* SELL統計 */}
      <div className="relative overflow-hidden rounded-lg border border-red-500/20 bg-gradient-to-br from-red-950/40 to-red-900/20 p-6">
        <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-transparent" />
        <div className="relative">
          <h3 className="text-lg font-semibold mb-4">
            <span className="neon-text-red">売り推奨の実績</span>
          </h3>

          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">総ラウンド数</span>
              <span className="font-mono font-semibold">{sellPerformance.total_rounds}回</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">的中率</span>
              <span className="font-mono font-semibold text-emerald-400">
                {(sellPerformance.avg_hit_rate * 100).toFixed(1)}%
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">平均予測騰落率</span>
              <span className="font-mono font-semibold neon-text-red">
                {formatPercent(sellPerformance.avg_predicted_return)}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">平均実績騰落率</span>
              <span className="font-mono font-semibold neon-text-red">
                {formatPercent(sellPerformance.avg_actual_return)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
