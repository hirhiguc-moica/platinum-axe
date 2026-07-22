"use client";

import { RoundHistoryRow } from "./RoundHistoryRow";

interface RoundHistoryTableProps {
  rounds: Array<{
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
  }>;
}

export function RoundHistoryTable({ rounds }: RoundHistoryTableProps) {
  if (rounds.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        該当するラウンドがありません
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/50 border-b border-border sticky top-0 z-10">
            <tr>
              <th className="p-4 text-left font-semibold">ラウンド</th>
              <th className="p-4 text-center font-semibold">推奨数</th>
              <th className="p-4 text-right font-semibold">予測騰落率</th>
              <th className="p-4 text-right font-semibold">実績騰落率</th>
              <th className="p-4 text-right font-semibold">
                予測誤差
                <span className="block text-xs text-muted-foreground font-normal">
                  (小さいほど精度高)
                </span>
              </th>
              <th className="p-4 text-center font-semibold">的中率</th>
              <th className="p-4 text-right font-semibold"></th>
            </tr>
          </thead>
          <tbody>
            {rounds.map((round) => (
              <RoundHistoryRow key={round.round_id} round={round} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
