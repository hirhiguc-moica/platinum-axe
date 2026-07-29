import type { Metadata } from "next";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export const metadata: Metadata = {
  title: "Platinum Axeについて | 日本株AI推奨システム",
  description:
    "プラチナの斧は、クオンツ分析とAI機械学習を活用した日本株銘柄推奨システムです。125項目のテクニカル指標と勾配ブーストモデルで週次予測を提供します。",
};

export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      {/* ヘッダー */}
      <div className="mb-12 text-center">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-yellow-400 via-amber-500 to-yellow-600 bg-clip-text text-transparent">
          Platinum Axeについて
        </h1>
        <p className="text-lg text-muted-foreground">
          個人投資家にクオンツ分析 × AI によるデータ・ドリブンな株取引を
        </p>
      </div>

      {/* セクション1: サービスの目的 */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <span className="text-emerald-400">🎯</span>
          サービスの目的
        </h2>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-base leading-relaxed text-foreground">
            プラチナの斧は、
            <strong className="text-emerald-400">
              すべての個人投資家にクオンツとAI学習モデルを活用したモダンな投資判断
            </strong>
            を提供することを目的としています。
          </p>
          <p className="text-base leading-relaxed text-foreground mt-4">
            従来、機関投資家やヘッジファンドのみが活用してきた高度な定量分析手法を、個人投資家でも簡単に利用できるよう設計されています。週次で更新される推奨銘柄を参考に、データドリブンな投資判断をサポートします。
          </p>
        </div>
      </section>

      {/* セクション2: データ更新タイミング */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <span className="text-blue-400">⏰</span>
          データ更新タイミング
        </h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2 text-emerald-400">📈 週次予測データ</h3>
            <p className="text-sm text-muted-foreground mb-2">毎週土曜日の朝に更新</p>
            <p className="text-base text-foreground">
              前週の市場データを分析し、翌週（月曜〜金曜）の推奨銘柄を算出します。買い推奨・売り推奨それぞれTop
              10銘柄を提示します。
            </p>
          </div>
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2 text-blue-400">📊 日次市場データ</h3>
            <p className="text-sm text-muted-foreground mb-2">毎営業日 18:00頃に更新</p>
            <p className="text-base text-foreground">
              J-Quants
              APIから取引終了後の株価・出来高・信用取引データを取得し、テクニカル指標を計算します。
            </p>
          </div>
        </div>
      </section>

      {/* セクション3: 分析に使用する特徴量 */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <span className="text-purple-400">🔬</span>
          分析に使用する特徴量
        </h2>
        <p className="text-base text-muted-foreground mb-6">
          機械学習モデルの特徴量として、以下の指標を使用しています。
        </p>

        {/* テクニカル指標セクション */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <h3 className="text-xl font-bold text-emerald-400">
              📊 テクニカル指標（125項目）
            </h3>
            <span className="px-2 py-1 text-xs font-semibold bg-emerald-500/20 text-emerald-400 rounded border border-emerald-500/30">
              実装済み
            </span>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            株価データから計算される125種類のテクニカル指標。クリックして詳細を表示できます。
          </p>

          <Accordion type="multiple" className="w-full">
            {/* 1. 移動平均系 */}
            <AccordionItem value="ma" className="border-border">
              <AccordionTrigger className="text-base hover:text-emerald-400">
                <span className="flex items-center gap-2">
                  <span className="text-emerald-400">📈</span>
                  <span>1. 移動平均系（19項目）</span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    価格のトレンドを把握する基本的な指標。異なる期間の移動平均線とその派生指標。
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="border-b border-border">
                        <tr className="text-left">
                          <th className="py-2 px-3 font-semibold">指標名</th>
                          <th className="py-2 px-3 font-semibold">説明</th>
                          <th className="py-2 px-3 font-semibold">分析軸</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/50">
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_5</td><td className="py-2 px-3">5日単純移動平均</td><td className="py-2 px-3 text-muted-foreground">超短期トレンド</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_10</td><td className="py-2 px-3">10日単純移動平均</td><td className="py-2 px-3 text-muted-foreground">短期トレンド</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_25</td><td className="py-2 px-3">25日単純移動平均</td><td className="py-2 px-3 text-muted-foreground">中期トレンド</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_50</td><td className="py-2 px-3">50日単純移動平均</td><td className="py-2 px-3 text-muted-foreground">中期トレンド</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_75</td><td className="py-2 px-3">75日単純移動平均</td><td className="py-2 px-3 text-muted-foreground">中長期トレンド</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_100</td><td className="py-2 px-3">100日単純移動平均</td><td className="py-2 px-3 text-muted-foreground">長期トレンド</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_200</td><td className="py-2 px-3">200日単純移動平均</td><td className="py-2 px-3 text-muted-foreground">長期トレンド</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ema_5</td><td className="py-2 px-3">5日指数移動平均</td><td className="py-2 px-3 text-muted-foreground">超短期トレンド（直近重視）</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ema_12</td><td className="py-2 px-3">12日指数移動平均</td><td className="py-2 px-3 text-muted-foreground">短期トレンド（MACD用）</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ema_26</td><td className="py-2 px-3">26日指数移動平均</td><td className="py-2 px-3 text-muted-foreground">中期トレンド（MACD用）</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ema_50</td><td className="py-2 px-3">50日指数移動平均</td><td className="py-2 px-3 text-muted-foreground">中期トレンド（直近重視）</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ema_200</td><td className="py-2 px-3">200日指数移動平均</td><td className="py-2 px-3 text-muted-foreground">長期トレンド（直近重視）</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">wma_20</td><td className="py-2 px-3">20日加重移動平均</td><td className="py-2 px-3 text-muted-foreground">中期トレンド（線形加重）</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">deviation_from_ma5</td><td className="py-2 px-3">5日線からの乖離率(%)</td><td className="py-2 px-3 text-muted-foreground">超短期乖離</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">deviation_from_ma25</td><td className="py-2 px-3">25日線からの乖離率(%)</td><td className="py-2 px-3 text-muted-foreground">中期乖離</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">deviation_from_ma75</td><td className="py-2 px-3">75日線からの乖離率(%)</td><td className="py-2 px-3 text-muted-foreground">中長期乖離</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">deviation_from_ma200</td><td className="py-2 px-3">200日線からの乖離率(%)</td><td className="py-2 px-3 text-muted-foreground">長期乖離</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_5_25_deviation</td><td className="py-2 px-3">5日線と25日線の乖離率(%)</td><td className="py-2 px-3 text-muted-foreground">短期・中期トレンド相対</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_25_75_deviation</td><td className="py-2 px-3">25日線と75日線の乖離率(%)</td><td className="py-2 px-3 text-muted-foreground">中期・中長期トレンド相対</td></tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* 2. 移動平均派生特徴量 */}
            <AccordionItem value="ma-derived" className="border-border">
              <AccordionTrigger className="text-base hover:text-blue-400">
                <span className="flex items-center gap-2">
                  <span className="text-blue-400">📐</span>
                  <span>2. 移動平均派生特徴量（9項目）</span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    移動平均線の傾きやクロスの検出など、移動平均から派生する高度な指標。
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="border-b border-border">
                        <tr className="text-left">
                          <th className="py-2 px-3 font-semibold">指標名</th>
                          <th className="py-2 px-3 font-semibold">説明</th>
                          <th className="py-2 px-3 font-semibold">分析軸</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/50">
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_75_200_deviation</td><td className="py-2 px-3">75日線と200日線の乖離率(%)</td><td className="py-2 px-3 text-muted-foreground">中長期・長期トレンド相対</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_5_slope_5d</td><td className="py-2 px-3">5日線の5日前からの傾き(%)</td><td className="py-2 px-3 text-muted-foreground">超短期トレンド加速度</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_25_slope_5d</td><td className="py-2 px-3">25日線の5日前からの傾き(%)</td><td className="py-2 px-3 text-muted-foreground">中期トレンド加速度</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ma_75_slope_10d</td><td className="py-2 px-3">75日線の10日前からの傾き(%)</td><td className="py-2 px-3 text-muted-foreground">中長期トレンド加速度</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">days_since_gc_5_25</td><td className="py-2 px-3">5日線が25日線をGC後の経過日数</td><td className="py-2 px-3 text-muted-foreground">トレンド転換からの期間</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">days_since_dc_5_25</td><td className="py-2 px-3">5日線が25日線をDC後の経過日数</td><td className="py-2 px-3 text-muted-foreground">トレンド転換からの期間</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">days_since_gc_25_75</td><td className="py-2 px-3">25日線が75日線をGC後の経過日数</td><td className="py-2 px-3 text-muted-foreground">中期トレンド転換からの期間</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">days_since_dc_25_75</td><td className="py-2 px-3">25日線が75日線をDC後の経過日数</td><td className="py-2 px-3 text-muted-foreground">中期トレンド転換からの期間</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">is_perfect_order_bullish</td><td className="py-2 px-3">パーフェクトオーダー（上昇）判定</td><td className="py-2 px-3 text-muted-foreground">強い上昇トレンド</td></tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* 3. モメンタム・騰落率系 */}
            <AccordionItem value="momentum" className="border-border">
              <AccordionTrigger className="text-base hover:text-red-400">
                <span className="flex items-center gap-2">
                  <span className="text-red-400">⚡</span>
                  <span>3. モメンタム・騰落率系（30項目）</span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    価格の変化率と勢い（モメンタム）を測定する指標。RSI、MACD、ストキャスティクス等。
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="border-b border-border">
                        <tr className="text-left">
                          <th className="py-2 px-3 font-semibold">指標名</th>
                          <th className="py-2 px-3 font-semibold">説明</th>
                          <th className="py-2 px-3 font-semibold">分析軸</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/50">
                        <tr><td className="py-2 px-3 font-mono text-xs">is_perfect_order_bearish</td><td className="py-2 px-3">パーフェクトオーダー（下落）判定</td><td className="py-2 px-3 text-muted-foreground">強い下降トレンド</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">return_1d</td><td className="py-2 px-3">1日騰落率(%)</td><td className="py-2 px-3 text-muted-foreground">超短期モメンタム</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">return_3d</td><td className="py-2 px-3">3日騰落率(%)</td><td className="py-2 px-3 text-muted-foreground">短期モメンタム</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">return_5d</td><td className="py-2 px-3">5日騰落率(%)</td><td className="py-2 px-3 text-muted-foreground">短期モメンタム</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">return_10d</td><td className="py-2 px-3">10日騰落率(%)</td><td className="py-2 px-3 text-muted-foreground">中期モメンタム</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">return_20d</td><td className="py-2 px-3">20日騰落率(%)</td><td className="py-2 px-3 text-muted-foreground">中期モメンタム</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">return_60d</td><td className="py-2 px-3">60日騰落率(%)</td><td className="py-2 px-3 text-muted-foreground">中長期モメンタム</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">return_120d</td><td className="py-2 px-3">120日騰落率(%)</td><td className="py-2 px-3 text-muted-foreground">長期モメンタム</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">log_return_1d</td><td className="py-2 px-3">1日対数収益率(%)</td><td className="py-2 px-3 text-muted-foreground">超短期リターン（複利）</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">log_return_5d</td><td className="py-2 px-3">5日対数収益率(%)</td><td className="py-2 px-3 text-muted-foreground">短期リターン（複利）</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">log_return_20d</td><td className="py-2 px-3">20日対数収益率(%)</td><td className="py-2 px-3 text-muted-foreground">中期リターン（複利）</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">rsi_9</td><td className="py-2 px-3">RSI（9日）</td><td className="py-2 px-3 text-muted-foreground">超短期買われすぎ/売られすぎ</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">rsi_14</td><td className="py-2 px-3">RSI（14日）</td><td className="py-2 px-3 text-muted-foreground">短期買われすぎ/売られすぎ</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">rsi_25</td><td className="py-2 px-3">RSI（25日）</td><td className="py-2 px-3 text-muted-foreground">中期買われすぎ/売られすぎ</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">macd</td><td className="py-2 px-3">MACD</td><td className="py-2 px-3 text-muted-foreground">トレンドの強さと方向</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">macd_signal</td><td className="py-2 px-3">MACDシグナル線</td><td className="py-2 px-3 text-muted-foreground">MACD転換点検出</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">macd_histogram</td><td className="py-2 px-3">MACDヒストグラム</td><td className="py-2 px-3 text-muted-foreground">トレンドの加速度</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">stochastic_k</td><td className="py-2 px-3">ストキャスティクス%K</td><td className="py-2 px-3 text-muted-foreground">短期買われすぎ/売られすぎ</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">stochastic_d</td><td className="py-2 px-3">ストキャスティクス%D</td><td className="py-2 px-3 text-muted-foreground">%Kのスムージング版</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">stochastic_slow_d</td><td className="py-2 px-3">ストキャスティクススロー%D</td><td className="py-2 px-3 text-muted-foreground">%Dのスムージング版</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">roc_12</td><td className="py-2 px-3">12日ROC（変化率）</td><td className="py-2 px-3 text-muted-foreground">短期変化率</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">roc_25</td><td className="py-2 px-3">25日ROC（変化率）</td><td className="py-2 px-3 text-muted-foreground">中期変化率</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">momentum_10</td><td className="py-2 px-3">10日モメンタム</td><td className="py-2 px-3 text-muted-foreground">短期価格差分</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">momentum_20</td><td className="py-2 px-3">20日モメンタム</td><td className="py-2 px-3 text-muted-foreground">中期価格差分</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">cci_14</td><td className="py-2 px-3">CCI（14日）</td><td className="py-2 px-3 text-muted-foreground">中期買われすぎ/売られすぎ</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">cci_20</td><td className="py-2 px-3">CCI（20日）</td><td className="py-2 px-3 text-muted-foreground">中長期買われすぎ/売られすぎ</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">williams_r_14</td><td className="py-2 px-3">ウィリアムズ%R（14日）</td><td className="py-2 px-3 text-muted-foreground">短期買われすぎ/売られすぎ</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">mfi_14</td><td className="py-2 px-3">MFI（14日）</td><td className="py-2 px-3 text-muted-foreground">出来高加味買われすぎ/売られすぎ</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">ultimate_oscillator</td><td className="py-2 px-3">アルティメットオシレーター</td><td className="py-2 px-3 text-muted-foreground">多期間モメンタム総合</td></tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* 4. トレンド指標 - 残りも同様に実装 */}
            <AccordionItem value="trend" className="border-border">
              <AccordionTrigger className="text-base hover:text-green-400">
                <span className="flex items-center gap-2">
                  <span className="text-green-400">📐</span>
                  <span>4. トレンド指標（11項目）</span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    トレンドの強さと方向性を判定する指標。ADX、パラボリックSAR、一目均衡表等。
                  </p>
                  <div className="text-sm text-muted-foreground">
                    <p className="mb-2">主な指標:</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>ADX、+DI、-DI（14日）</li>
                      <li>パラボリックSAR、SAR方向</li>
                      <li>一目均衡表（転換線、基準線、先行スパンA/B、遅行スパン、雲の厚さ、雲の上下判定）</li>
                    </ul>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* 5. ボラティリティ系 */}
            <AccordionItem value="volatility" className="border-border">
              <AccordionTrigger className="text-base hover:text-purple-400">
                <span className="flex items-center gap-2">
                  <span className="text-purple-400">📊</span>
                  <span>5. ボラティリティ系（11項目）</span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    価格の変動幅を測定する指標。ボリンジャーバンド、ATR、ヒストリカルボラティリティ等。
                  </p>
                  <div className="text-sm text-muted-foreground">
                    <p className="mb-2">主な指標:</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>ボリンジャーバンド（上限、中心線、下限、幅、バンド内位置）</li>
                      <li>ATR（14日、20日）</li>
                      <li>ヒストリカルボラティリティ（10日、20日、60日）</li>
                      <li>ケルトナーチャネル（上限、中心線、下限）</li>
                    </ul>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* 6. 出来高系 */}
            <AccordionItem value="volume" className="border-border">
              <AccordionTrigger className="text-base hover:text-cyan-400">
                <span className="flex items-center gap-2">
                  <span className="text-cyan-400">📦</span>
                  <span>6. 出来高系（13項目）</span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    出来高とその派生指標。売買の活発度や資金フローを測定。
                  </p>
                  <div className="text-sm text-muted-foreground">
                    <p className="mb-2">主な指標:</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>出来高移動平均（5日、10日、20日、60日）</li>
                      <li>出来高比率（5日、20日）、出来高変化率（1日、5日）</li>
                      <li>OBV（On-Balance Volume）、OBV移動平均</li>
                      <li>VWAP、VWMA（出来高加重移動平均）</li>
                      <li>CMF（Chaikin Money Flow）</li>
                    </ul>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* 7. 価格位置系 */}
            <AccordionItem value="price-position" className="border-border">
              <AccordionTrigger className="text-base hover:text-yellow-400">
                <span className="flex items-center gap-2">
                  <span className="text-yellow-400">📍</span>
                  <span>7. 価格位置系（16項目）</span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    高値・安値からの位置関係を測定する指標。
                  </p>
                  <div className="text-sm text-muted-foreground">
                    <p className="mb-2">主な指標:</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>高値・安値（5日、20日、60日、52週）</li>
                      <li>高値・安値からの乖離率（5日、20日、52週）</li>
                      <li>価格の相対位置（20日、52週レンジ内の位置）</li>
                      <li>新高値・新安値判定（20日、52週）</li>
                    </ul>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* 8. ローソク足パターン系 */}
            <AccordionItem value="candlestick" className="border-border">
              <AccordionTrigger className="text-base hover:text-orange-400">
                <span className="flex items-center gap-2">
                  <span className="text-orange-400">🕯️</span>
                  <span>8. ローソク足パターン系（13項目）</span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    ローソク足のパターンと形状を分析する指標。
                  </p>
                  <div className="text-sm text-muted-foreground">
                    <p className="mb-2">主な指標:</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>パターン判定（十字線、ハンマー、逆ハンマー、流れ星、首吊り線）</li>
                      <li>連続陽線・陰線日数</li>
                      <li>実体サイズ比率</li>
                      <li>上ヒゲ・下ヒゲ比率</li>
                    </ul>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* 9. その他の指標 */}
            <AccordionItem value="others" className="border-border">
              <AccordionTrigger className="text-base hover:text-pink-400">
                <span className="flex items-center gap-2">
                  <span className="text-pink-400">⭐</span>
                  <span>9. その他の指標（3項目）</span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    複合的な指標。
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="border-b border-border">
                        <tr className="text-left">
                          <th className="py-2 px-3 font-semibold">指標名</th>
                          <th className="py-2 px-3 font-semibold">説明</th>
                          <th className="py-2 px-3 font-semibold">分析軸</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/50">
                        <tr><td className="py-2 px-3 font-mono text-xs">awesome_oscillator</td><td className="py-2 px-3">Awesome Oscillator</td><td className="py-2 px-3 text-muted-foreground">中期モメンタムの変化</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">aroon_up</td><td className="py-2 px-3">Aroon Up（25日）</td><td className="py-2 px-3 text-muted-foreground">上昇トレンドの強さ</td></tr>
                        <tr><td className="py-2 px-3 font-mono text-xs">aroon_down</td><td className="py-2 px-3">Aroon Down（25日）</td><td className="py-2 px-3 text-muted-foreground">下降トレンドの強さ</td></tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>

        {/* ファンダメンタル指標セクション（今後実装予定） */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <h3 className="text-xl font-bold text-blue-400">
              💼 ファンダメンタル指標（20項目）
            </h3>
            <span className="px-2 py-1 text-xs font-semibold bg-muted text-muted-foreground rounded border border-border">
              実装予定
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            財務データから計算される20種類のファンダメンタル指標（PER、PBR、ROE等）。今後実装予定です。
          </p>
        </div>
      </section>

      {/* セクション4: モデリング手法 */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <span className="text-amber-400">🤖</span>
          モデリング手法
        </h2>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-base leading-relaxed text-foreground mb-4">
            <strong className="text-amber-400">LightGBM</strong>
            を中心とした勾配ブーストモデルと、その他の機械学習モデルを
            <strong className="text-emerald-400">スタッキング</strong>
            して予測精度を向上させています。
          </p>
          <p className="text-base leading-relaxed text-foreground mb-4">
            各モデルは過去の株価データと125項目のテクニカル指標を学習し、翌週の騰落率を予測します。予測結果は信頼度スコアとともに提供され、ユーザーは順位とスコアを参考に投資判断を行えます。
          </p>
          <div className="border-t border-border pt-4 mt-4">
            <p className="text-sm text-muted-foreground mb-2">
              ⚠️ モデルの詳細なアーキテクチャやハイパーパラメータは非公開としています。
            </p>
            <p className="text-sm text-foreground">
              📖 ソースコードは GitHub で公開しています：
              <a
                href="https://github.com/yourusername/platinum-axe"
                target="_blank"
                rel="noopener noreferrer"
                className="text-amber-400 hover:text-amber-300 underline ml-2"
              >
                github.com/yourusername/platinum-axe
              </a>
            </p>
          </div>
        </div>
      </section>

      {/* フッター */}
      <section className="text-center py-8 border-t border-border">
        <p className="text-sm text-muted-foreground">
          ⚠️ 本サービスは投資助言ではありません。投資判断は自己責任でお願いします。
        </p>
      </section>
    </div>
  );
}
