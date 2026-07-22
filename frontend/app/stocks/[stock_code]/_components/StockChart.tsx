"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  IChartApi,
  ISeriesApi,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
} from "lightweight-charts";

interface StockPrice {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

interface TechnicalIndicator {
  date: string;
  ma_5: number | null;
  ma_25: number | null;
  ma_75: number | null;
}

interface StockChartProps {
  prices: StockPrice[];
  technicalIndicators: TechnicalIndicator[];
}

export function StockChart({ prices, technicalIndicators }: StockChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

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
      height: 500,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: "#3e3e42",
      },
      rightPriceScale: {
        borderColor: "#3e3e42",
      },
      crosshair: {
        mode: 1,
      },
    });

    chartRef.current = chart;

    // ローソク足データ準備
    const candlestickData = prices
      .filter((p) => p.open && p.high && p.low && p.close)
      .map((p) => ({
        time: p.date,
        open: p.open!,
        high: p.high!,
        low: p.low!,
        close: p.close!,
      }))
      .reverse(); // 古い順にソート

    // ローソク足シリーズ追加
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: false,
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });
    candlestickSeries.setData(candlestickData);

    // 移動平均線データ準備
    const ma5Data = technicalIndicators
      .filter((t) => t.ma_5 !== null)
      .map((t) => ({ time: t.date, value: t.ma_5! }))
      .reverse();

    const ma25Data = technicalIndicators
      .filter((t) => t.ma_25 !== null)
      .map((t) => ({ time: t.date, value: t.ma_25! }))
      .reverse();

    const ma75Data = technicalIndicators
      .filter((t) => t.ma_75 !== null)
      .map((t) => ({ time: t.date, value: t.ma_75! }))
      .reverse();

    // 移動平均線追加
    if (ma5Data.length > 0) {
      const ma5Series = chart.addSeries(LineSeries, {
        color: "#2196F3",
        lineWidth: 1,
        title: "MA5",
      });
      ma5Series.setData(ma5Data);
    }

    if (ma25Data.length > 0) {
      const ma25Series = chart.addSeries(LineSeries, {
        color: "#FF9800",
        lineWidth: 2,
        title: "MA25",
      });
      ma25Series.setData(ma25Data);
    }

    if (ma75Data.length > 0) {
      const ma75Series = chart.addSeries(LineSeries, {
        color: "#9C27B0",
        lineWidth: 2,
        title: "MA75",
      });
      ma75Series.setData(ma75Data);
    }

    // 出来高データ準備
    const volumeData = prices
      .filter((p) => p.volume !== null && p.close !== null && p.open !== null)
      .map((p) => ({
        time: p.date,
        value: p.volume!,
        color: p.close! >= p.open! ? "#26a69a80" : "#ef535080",
      }))
      .reverse();

    // 出来高チャート追加
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "#26a69a",
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "volume",
    });
    volumeSeries.setData(volumeData);

    chart.priceScale("volume").applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

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
  }, [prices, technicalIndicators]);

  return (
    <div className="w-full">
      <div ref={chartContainerRef} className="w-full" />
      <div className="mt-3 flex gap-4 text-xs text-[#858585]">
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-[#2196F3]"></div>
          <span>MA5（5日移動平均）</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-[#FF9800]"></div>
          <span>MA25（25日移動平均）</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-[#9C27B0]"></div>
          <span>MA75（75日移動平均）</span>
        </div>
      </div>
    </div>
  );
}
