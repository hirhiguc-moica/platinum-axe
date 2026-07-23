"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StockChart } from "./StockChart";

interface StockPrice {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  adjusted_close: number | null;
}

interface TechnicalIndicator {
  date: string;
  ma_5: number | null;
  ma_25: number | null;
  ma_75: number | null;
  ema_12: number | null;
  ema_26: number | null;
  rsi_14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;
  bollinger_upper_2sigma: number | null;
  bollinger_middle: number | null;
  bollinger_lower_2sigma: number | null;
  atr_14: number | null;
  volume_ma_20: number | null;
  obv: number | null;
  adx_14: number | null;
}

interface StockDataTabsProps {
  prices: {
    items: StockPrice[];
    pagination: {
      total: number;
    };
  };
  technicalIndicators: {
    items: TechnicalIndicator[];
    pagination: {
      total: number;
    };
  };
}

export function StockDataTabs({ prices, technicalIndicators }: StockDataTabsProps) {
  return (
    <Tabs defaultValue="chart" className="w-full">
      <TabsList className="grid w-full max-w-2xl grid-cols-3 bg-[#252526] border border-[#3e3e42]">
        <TabsTrigger value="chart">チャート</TabsTrigger>
        <TabsTrigger value="prices">株価データ</TabsTrigger>
        <TabsTrigger value="technical">テクニカル指標</TabsTrigger>
      </TabsList>

      {/* チャートタブ */}
      <TabsContent value="chart" className="mt-4">
        <div className="bg-[#252526] border border-[#3e3e42] rounded-lg p-4">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-[#cccccc]">株価チャート</h2>
            <p className="text-xs text-[#858585] mt-1">
              ローソク足 + 移動平均線（MA5/MA25/MA75）+ 出来高
            </p>
          </div>
          <StockChart prices={prices.items} technicalIndicators={technicalIndicators.items} />
        </div>
      </TabsContent>

      {/* 株価データタブ */}
      <TabsContent value="prices" className="mt-4">
        <div className="bg-[#252526] border border-[#3e3e42] rounded-lg">
          <div className="p-4 border-b border-[#3e3e42]">
            <h2 className="text-sm font-semibold text-[#cccccc]">株価データ</h2>
            <p className="text-xs text-[#858585] mt-1">時系列順（新しい順）</p>
          </div>
          <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="bg-[#1e1e1e] sticky top-0 z-10">
                <tr className="border-b border-[#3e3e42]">
                  <th className="text-left p-2 font-medium text-[#858585] sticky left-0 bg-[#1e1e1e] z-20 whitespace-nowrap">
                    日付
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    終値
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    始値
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    高値
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    安値
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    出来高
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    調整後終値
                  </th>
                </tr>
              </thead>
              <tbody>
                {prices.items.map((price, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-[#3e3e42] hover:bg-[#2a2a2a] transition-colors"
                  >
                    <td className="p-2 font-mono text-[#cccccc] sticky left-0 bg-[#252526] z-10">
                      {price.date}
                    </td>
                    <td className="p-2 font-mono text-right text-[#cccccc] font-semibold">
                      {price.close?.toLocaleString() || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {price.open?.toLocaleString() || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {price.high?.toLocaleString() || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {price.low?.toLocaleString() || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {price.volume?.toLocaleString() || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {price.adjusted_close?.toLocaleString() || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </TabsContent>

      {/* テクニカル指標タブ */}
      <TabsContent value="technical" className="mt-4">
        <div className="bg-[#252526] border border-[#3e3e42] rounded-lg">
          <div className="p-4 border-b border-[#3e3e42]">
            <h2 className="text-sm font-semibold text-[#cccccc]">テクニカル指標</h2>
            <p className="text-xs text-[#858585] mt-1">
              時系列順（新しい順）• 主要16指標 • 横スクロール可能
            </p>
          </div>
          <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="bg-[#1e1e1e] sticky top-0 z-10">
                <tr className="border-b border-[#3e3e42]">
                  <th className="text-left p-2 font-medium text-[#858585] sticky left-0 bg-[#1e1e1e] z-20">
                    日付
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    MA5
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    MA25
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    MA75
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    EMA12
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    EMA26
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    RSI14
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    MACD
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    MACDシグナル
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    MACDヒスト
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    BB上限
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    BB中央
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    BB下限
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    ATR14
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    出来高MA20
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    OBV
                  </th>
                  <th className="text-right p-2 font-medium text-[#858585] whitespace-nowrap">
                    ADX14
                  </th>
                </tr>
              </thead>
              <tbody>
                {technicalIndicators.items.map((ind, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-[#3e3e42] hover:bg-[#2a2a2a] transition-colors"
                  >
                    <td className="p-2 font-mono text-[#cccccc] sticky left-0 bg-[#252526] z-10">
                      {ind.date}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.ma_5?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.ma_25?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.ma_75?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.ema_12?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.ema_26?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.rsi_14?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.macd?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.macd_signal?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.macd_histogram?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.bollinger_upper_2sigma?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.bollinger_middle?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.bollinger_lower_2sigma?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.atr_14?.toFixed(2) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.volume_ma_20?.toFixed(0) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.obv?.toFixed(0) || "-"}
                    </td>
                    <td className="p-2 font-mono text-right text-[#858585]">
                      {ind.adx_14?.toFixed(2) || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="p-3 bg-[#1e1e1e] text-xs text-[#858585] border-t border-[#3e3e42]">
            ℹ️ 主要16指標のみ表示中。FULL版125指標は今後のバージョンで対応予定です。
          </div>
        </div>
      </TabsContent>
    </Tabs>
  );
}
