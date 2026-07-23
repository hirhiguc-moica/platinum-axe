import type { Metadata } from "next";

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
          以下の<strong className="text-amber-400">125項目</strong>
          のテクニカル指標を機械学習モデルの特徴量として使用しています。
        </p>

        <div className="grid gap-4 md:grid-cols-2">
          {/* カテゴリ1: 移動平均線 */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-lg font-semibold mb-2 text-emerald-400">📊 移動平均線（13種）</h3>
            <p className="text-sm text-muted-foreground mb-3">
              価格のトレンドを把握する基本的な指標
            </p>
            <ul className="text-sm text-foreground space-y-1">
              <li>• 単純移動平均（MA5〜MA200）</li>
              <li>• 指数移動平均（EMA5〜EMA200）</li>
              <li>• 加重移動平均（WMA20）</li>
            </ul>
          </div>

          {/* カテゴリ2: 移動平均派生 */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-lg font-semibold mb-2 text-blue-400">
              📈 移動平均派生特徴量（14種）
            </h3>
            <p className="text-sm text-muted-foreground mb-3">移動平均線から算出される高度な指標</p>
            <ul className="text-sm text-foreground space-y-1">
              <li>• 乖離率（価格とMAの距離）</li>
              <li>• GC/DCからの経過日数</li>
              <li>• 移動平均の傾き</li>
              <li>• パーフェクトオーダー判定</li>
            </ul>
          </div>

          {/* カテゴリ3: 騰落率 */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-lg font-semibold mb-2 text-amber-400">📉 騰落率（10種）</h3>
            <p className="text-sm text-muted-foreground mb-3">価格変動の大きさを測定</p>
            <ul className="text-sm text-foreground space-y-1">
              <li>• 1日〜120日騰落率</li>
              <li>• 対数収益率（1日/5日/20日）</li>
            </ul>
          </div>

          {/* カテゴリ4: モメンタム系 */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-lg font-semibold mb-2 text-red-400">⚡ モメンタム系（16種）</h3>
            <p className="text-sm text-muted-foreground mb-3">相場の勢いを測定する指標</p>
            <ul className="text-sm text-foreground space-y-1">
              <li>• RSI（9日/14日/25日）</li>
              <li>• MACD（ヒストグラム含む）</li>
              <li>• ストキャスティクス（%K/%D）</li>
              <li>• CCI、MFI、ウィリアムズ%R等</li>
            </ul>
          </div>

          {/* カテゴリ5: トレンド指標 */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-lg font-semibold mb-2 text-green-400">📐 トレンド指標（13種）</h3>
            <p className="text-sm text-muted-foreground mb-3">トレンドの強さと方向性を判定</p>
            <ul className="text-sm text-foreground space-y-1">
              <li>• ADX（±DI含む）</li>
              <li>• パラボリックSAR</li>
              <li>• 一目均衡表（雲の厚さ等）</li>
            </ul>
          </div>

          {/* カテゴリ6: ボラティリティ */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-lg font-semibold mb-2 text-purple-400">
              📊 ボラティリティ指標（12種）
            </h3>
            <p className="text-sm text-muted-foreground mb-3">価格変動の大きさを測定</p>
            <ul className="text-sm text-foreground space-y-1">
              <li>• ボリンジャーバンド（%B含む）</li>
              <li>• ATR（14日/20日）</li>
              <li>• ヒストリカルボラティリティ</li>
              <li>• ケルトナーチャネル</li>
            </ul>
          </div>

          {/* カテゴリ7: 出来高系 */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-lg font-semibold mb-2 text-cyan-400">📦 出来高系（13種）</h3>
            <p className="text-sm text-muted-foreground mb-3">売買の活発度を測定</p>
            <ul className="text-sm text-foreground space-y-1">
              <li>• 出来高移動平均（5日〜60日）</li>
              <li>• OBV（On-Balance Volume）</li>
              <li>• VWAP（出来高加重平均）</li>
              <li>• CMF（Chaikin Money Flow）</li>
            </ul>
          </div>

          {/* カテゴリ8: 価格位置 */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-lg font-semibold mb-2 text-yellow-400">
              📍 価格位置・高値安値（19種）
            </h3>
            <p className="text-sm text-muted-foreground mb-3">価格の相対的な位置を測定</p>
            <ul className="text-sm text-foreground space-y-1">
              <li>• 高値・安値（5日〜52週）</li>
              <li>• 高値/安値からの乖離率</li>
              <li>• 新高値・新安値判定</li>
            </ul>
          </div>

          {/* カテゴリ9: ローソク足 */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-lg font-semibold mb-2 text-orange-400">
              🕯️ ローソク足パターン（10種）
            </h3>
            <p className="text-sm text-muted-foreground mb-3">価格パターンの認識</p>
            <ul className="text-sm text-foreground space-y-1">
              <li>• 十字線、ハンマー、流れ星等</li>
              <li>• 連続陽線・陰線日数</li>
              <li>• 実体・ヒゲの比率</li>
            </ul>
          </div>

          {/* カテゴリ10: その他 */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-lg font-semibold mb-2 text-pink-400">⭐ その他の指標（5種）</h3>
            <p className="text-sm text-muted-foreground mb-3">高度な複合指標</p>
            <ul className="text-sm text-foreground space-y-1">
              <li>• Awesome Oscillator</li>
              <li>• Aroon Indicator（Up/Down）</li>
            </ul>
          </div>
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
