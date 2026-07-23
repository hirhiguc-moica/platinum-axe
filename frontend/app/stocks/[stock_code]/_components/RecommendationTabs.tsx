"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RecommendationAccuracyChart } from "./RecommendationAccuracyChart";

interface RecommendationHistoryItem {
  round_id: string;
  round_type: string;
  start_date: string;
  end_date: string;
  status: string;
  rank: number;
  predicted_return: number | null;
  confidence_score: number | null;
  actual_return: number | null;
  prediction_hit: boolean | null;
  start_price: number | null;
  end_price: number | null;
}

interface RecommendationTabsProps {
  items: RecommendationHistoryItem[];
}

export function RecommendationTabs({ items }: RecommendationTabsProps) {
  return (
    <div className="bg-[#252526] border border-[#3e3e42] rounded-lg">
      <div className="p-4 border-b border-[#3e3e42]">
        <h2 className="text-sm font-semibold text-[#cccccc]">推奨履歴</h2>
        <p className="text-xs text-[#858585] mt-1">過去の推奨実績 • 予測 vs 実績</p>
      </div>

      <Tabs defaultValue="chart" className="w-full">
        <div className="px-4 pt-4">
          <TabsList className="grid w-full max-w-md grid-cols-2 bg-[#1e1e1e] border border-[#3e3e42]">
            <TabsTrigger value="chart">予測 vs 実績チャート</TabsTrigger>
            <TabsTrigger value="details">詳細リスト</TabsTrigger>
          </TabsList>
        </div>

        {/* チャートタブ */}
        <TabsContent value="chart" className="p-4">
          {items.length > 0 ? (
            <RecommendationAccuracyChart items={items} />
          ) : (
            <div className="text-center py-8 text-[#858585] text-sm">
              推奨履歴データがありません
            </div>
          )}
        </TabsContent>

        {/* 詳細リストタブ */}
        <TabsContent value="details" className="p-4">
          <div className="space-y-3">
            {items.map((rec, idx) => (
              <div
                key={idx}
                className="p-4 bg-[#1e1e1e] border border-[#3e3e42] rounded-lg hover:border-[#4e4e52] transition-colors"
              >
                {/* ヘッダー */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        rec.round_type === "BUY"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : "bg-red-500/20 text-red-400 border border-red-500/30"
                      }`}
                    >
                      {rec.round_type === "BUY" ? "📈 買い" : "📉 売り"} #{rec.rank}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-[#cccccc]">{rec.round_id}</div>
                      <div className="text-xs text-[#858585]">
                        {rec.start_date} 〜 {rec.end_date}
                      </div>
                    </div>
                  </div>
                  <div
                    className={`px-2 py-0.5 rounded text-xs ${
                      rec.status === "CLOSED"
                        ? "bg-gray-500/20 text-gray-400 border border-gray-500/30"
                        : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                    }`}
                  >
                    {rec.status === "CLOSED" ? "終了" : "予測中"}
                  </div>
                </div>

                {/* 予測 vs 実績 */}
                <div className="grid grid-cols-2 gap-4 pt-3 border-t border-[#3e3e42]">
                  {/* 予測 */}
                  <div>
                    <div className="text-xs text-[#858585] mb-2">📊 予測</div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-[#858585]">騰落率</span>
                        <span
                          className={`font-mono font-semibold ${
                            (rec.predicted_return || 0) >= 0 ? "text-emerald-400" : "text-red-400"
                          }`}
                        >
                          {rec.predicted_return !== null
                            ? `${rec.predicted_return > 0 ? "+" : ""}${(rec.predicted_return * 100).toFixed(2)}%`
                            : "-"}
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-[#858585]">信頼度</span>
                        <span className="font-mono text-[#cccccc]">
                          {rec.confidence_score !== null
                            ? `${(rec.confidence_score * 100).toFixed(1)}%`
                            : "-"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 実績 */}
                  <div>
                    <div className="text-xs text-[#858585] mb-2">
                      {rec.actual_return !== null ? "✅ 実績" : "⏳ 予測中..."}
                    </div>
                    {rec.actual_return !== null ? (
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-[#858585]">実際の騰落率</span>
                          <span
                            className={`font-mono font-semibold ${
                              (rec.actual_return || 0) >= 0 ? "text-emerald-400" : "text-red-400"
                            }`}
                          >
                            {rec.actual_return > 0 ? "+" : ""}
                            {(rec.actual_return * 100).toFixed(2)}%
                          </span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-[#858585]">判定</span>
                          <span
                            className={`font-medium ${
                              rec.prediction_hit ? "text-emerald-400" : "text-red-400"
                            }`}
                          >
                            {rec.prediction_hit ? "的中 🎯" : "外れ"}
                          </span>
                        </div>
                        {rec.start_price && rec.end_price && (
                          <div className="flex justify-between text-xs">
                            <span className="text-[#858585]">株価</span>
                            <span className="font-mono text-[#cccccc]">
                              {rec.start_price.toLocaleString()} → {rec.end_price.toLocaleString()}
                            </span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-xs text-[#858585]">期間終了後に実績が確定します</div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
