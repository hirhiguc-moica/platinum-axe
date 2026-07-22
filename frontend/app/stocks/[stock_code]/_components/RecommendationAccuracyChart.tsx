"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  IChartApi,
  LineSeries,
} from "lightweight-charts";

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

interface RecommendationAccuracyChartProps {
  items: RecommendationHistoryItem[];
}

export function RecommendationAccuracyChart({
  items,
}: RecommendationAccuracyChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 時系列順にソート（古い順）
    const sortedItems = [...items].sort(
      (a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime()
    );

    // チャート作成
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#1e1e1e" },
        textColor: "#858585",
      },
      grid: {
        vertLines: { color: "#2a2a2a" },
        horzLines: { color: "#2a2a2a" },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      timeScale: {
        timeVisible: false,
        borderColor: "#3e3e42",
      },
      rightPriceScale: {
        borderColor: "#3e3e42",
      },
      crosshair: {
        mode: 1,
      },
      localization: {
        dateFormat: "MM/dd", // 月/日形式（例: 07/20）
      },
    });

    chartRef.current = chart;

    // 予測騰落率データ
    const predictedData = sortedItems
      .filter((item) => item.predicted_return !== null)
      .map((item, index) => ({
        time: item.start_date as any, // YYYY-MM-DD形式の文字列
        value: (item.predicted_return! * 100), // パーセント表示
      }));

    // 実績騰落率データ（実績がある場合のみ）
    const actualData = sortedItems
      .filter((item) => item.actual_return !== null)
      .map((item, index) => ({
        time: item.start_date as any, // YYYY-MM-DD形式の文字列
        value: (item.actual_return! * 100), // パーセント表示
      }));

    // 予測騰落率の線を追加
    if (predictedData.length > 0) {
      const predictedSeries = chart.addSeries(LineSeries, {
        color: "#2196F3",
        lineWidth: 2,
        title: "予測騰落率",
      });
      predictedSeries.setData(predictedData);
    }

    // 実績騰落率の線を追加
    if (actualData.length > 0) {
      const actualSeries = chart.addSeries(LineSeries, {
        color: "#FF9800",
        lineWidth: 2,
        title: "実績騰落率",
      });
      actualSeries.setData(actualData);
    }

    // タイムスケールをフィット
    chart.timeScale().fitContent();

    // リサイズ対応
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    // クリーンアップ
    return () => {
      window.removeEventListener("resize", handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [items]);

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-[#cccccc] mb-1">
          予測精度の推移
        </h3>
        <p className="text-xs text-[#858585]">
          予測騰落率と実績騰落率の比較 • 青線：予測 / 橙線：実績
        </p>
      </div>
      <div ref={chartContainerRef} className="w-full" />
      <div className="mt-3 flex gap-4 text-xs text-[#858585]">
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-[#2196F3]"></div>
          <span>予測騰落率</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-[#FF9800]"></div>
          <span>実績騰落率</span>
        </div>
      </div>
      {items.filter((item) => item.actual_return !== null).length === 0 && (
        <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded text-xs text-blue-400">
          ℹ️ 実績データがまだありません。期間終了後に実績騰落率が表示されます。
        </div>
      )}
    </div>
  );
}
