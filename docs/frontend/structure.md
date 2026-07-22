# Frontend構造

## 概要

platinum-axeのFrontendは、**Next.js 15 (App Router)** を採用したシンプルなWebアプリケーションです。

**技術スタック**:
- Next.js 15 (App Router)
- React 19
- TypeScript
- TanStack Query (データフェッチング)
- shadcn/ui (UIコンポーネント)
- Tailwind CSS v4 (スタイリング)
- @hey-api/openapi-ts (Backend API型自動生成)

**特徴**:
- ❌ Turborepo不要（アプリ1つのみ）
- ❌ 認証なし（将来的にFirebase Auth導入予定）
- ✅ レスポンシブ対応（PC/タブレット/スマホ）

---

## ディレクトリ構造

```
frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # ルートレイアウト
│   ├── page.tsx                  # トップページ
│   ├── globals.css               # グローバルスタイル
│   │
│   ├── predictions/              # 今週の予測
│   │   └── page.tsx
│   │
│   ├── rounds/                   # 過去の結果
│   │   ├── page.tsx              # ラウンド一覧
│   │   └── [roundId]/
│   │       └── page.tsx          # ラウンド詳細
│   │
│   └── stocks/                   # 銘柄詳細
│       └── [stockCode]/
│           └── page.tsx
│
├── components/                   # Reactコンポーネント
│   ├── ui/                       # shadcn/uiコンポーネント
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── table.tsx
│   │   ├── tabs.tsx
│   │   ├── badge.tsx
│   │   └── ...
│   │
│   ├── layout/                   # レイアウトコンポーネント
│   │   ├── header.tsx            # ヘッダー
│   │   ├── navigation.tsx        # ナビゲーション（タブメニュー）
│   │   ├── footer.tsx            # フッター
│   │   └── mobile-nav.tsx        # モバイルナビ（ハンバーガー）
│   │
│   ├── rounds/                   # ラウンド関連
│   │   ├── round-summary.tsx     # ラウンドサマリーカード
│   │   ├── round-list.tsx        # ラウンド一覧
│   │   ├── recommendation-table.tsx  # 推奨銘柄テーブル
│   │   └── round-performance.tsx # パフォーマンス表示
│   │
│   ├── stocks/                   # 銘柄関連
│   │   ├── stock-search.tsx      # 銘柄検索
│   │   ├── stock-card.tsx        # 銘柄カード
│   │   ├── stock-chart.tsx       # 株価チャート
│   │   └── stock-info.tsx        # 銘柄基本情報
│   │
│   └── market/                   # マーケット情報
│       └── market-summary.tsx    # マーケットサマリー
│
├── lib/                          # ライブラリ・ユーティリティ
│   ├── api/                      # API Client
│   │   ├── client.ts             # APIクライアント設定
│   │   └── generated/            # 自動生成ファイル
│   │       ├── client.gen.ts
│   │       ├── types.gen.ts
│   │       └── ...
│   │
│   ├── hooks/                    # カスタムフック
│   │   ├── use-rounds.ts         # ラウンドデータ取得
│   │   ├── use-current-round.ts  # 今週のラウンド取得
│   │   ├── use-stocks.ts         # 銘柄データ取得
│   │   └── use-stock-search.ts   # 銘柄検索
│   │
│   ├── utils/                    # ユーティリティ関数
│   │   ├── format.ts             # フォーマット関数
│   │   ├── date.ts               # 日付処理
│   │   └── cn.ts                 # classname utility
│   │
│   └── types/                    # 追加型定義
│       └── index.ts
│
├── public/                       # 静的ファイル
│   ├── favicon.ico
│   └── images/
│
├── .eslintrc.json                # ESLint設定
├── next.config.js                # Next.js設定
├── package.json                  # 依存関係
├── postcss.config.js             # PostCSS設定
├── tailwind.config.ts            # Tailwind CSS設定
├── tsconfig.json                 # TypeScript設定
└── openapi-ts.config.ts          # OpenAPI型生成設定
```

---

## ページ構成

### 1. **トップページ（ホーム）**

**URL**: `/`

**レイアウト**:
```
┌────────────────────────────────────────┐
│  Header                                 │
│  ├─ Logo: プラチナの斧                  │
│  └─ 銘柄検索バー                        │
├────────────────────────────────────────┤
│  Navigation (タブメニュー)              │
│  ├─ 🏠 ホーム                           │
│  ├─ 🤖 今週の予測                       │
│  └─ 📊 過去の結果                       │
├────────────────────────────────────────┤
│  今週のAI予測 (2025年W10)               │
│  ┌──────────────┬──────────────┐        │
│  │ Buy推奨      │ Sell推奨     │        │
│  │ Top 10       │ Top 10       │        │
│  └──────────────┴──────────────┘        │
│                                         │
│  先週の戦績                              │
│  ├─ Buy: 勝率 70% (+12.3%)              │
│  ├─ Sell: 勝率 60% (-8.5%)              │
│  └─ → 詳細を見る                        │
│                                         │
│  過去のラウンド                          │
│  [W09] [W08] [W07] [W06] ... もっと見る │
└────────────────────────────────────────┘
```

**コンポーネント**:
- `components/rounds/round-summary.tsx` - 今週のラウンドカード
- `components/rounds/recommendation-table.tsx` - Buy/Sell推奨テーブル
- `components/rounds/round-performance.tsx` - 先週の戦績

---

### 2. **今週の予測**

**URL**: `/predictions`

**内容**:
- 今週のラウンド詳細
- Buy推奨 Top 10（詳細情報）
  - 銘柄コード・名称
  - 予測騰落率
  - 信頼度スコア
- Sell推奨 Top 10
- タブ切り替え: Buy | Sell | 両方

**コンポーネント**:
- `components/rounds/recommendation-table.tsx`
- `components/stocks/stock-card.tsx`

---

### 3. **過去の結果**

**URL**: `/rounds`

**内容**:
- ラウンド一覧（リスト形式）
- フィルタ: Buy/Sell、期間
- 各ラウンドのパフォーマンス表示
  - 勝率、平均リターン、vs TOPIX
- クリックでラウンド詳細へ

**コンポーネント**:
- `components/rounds/round-list.tsx`
- `components/rounds/round-performance.tsx`

---

### 4. **ラウンド詳細**

**URL**: `/rounds/[roundId]`

**例**: `/rounds/2025-W10-BUY`

**内容**:
- ラウンド情報（期間、タイプ、ステータス）
- 推奨銘柄一覧（実績付き）
  - 予測騰落率 vs 実際騰落率
  - 損益（仮想）
- パフォーマンスサマリー
  - 勝率、平均リターン
  - vs TOPIX比較

**コンポーネント**:
- `components/rounds/recommendation-table.tsx`
- `components/rounds/round-performance.tsx`

---

### 5. **銘柄詳細**

**URL**: `/stocks/[stockCode]`

**例**: `/stocks/7203`

**内容**:
- 銘柄基本情報（名称、セクター、時価総額）
- 株価チャート（過去1年）
- テクニカル指標（MA, RSI等）
- AI予測履歴（この銘柄が推奨された過去ラウンド）
- 財務情報（PER, PBR, ROE等）

**コンポーネント**:
- `components/stocks/stock-info.tsx`
- `components/stocks/stock-chart.tsx`

---

## レスポンシブ対応

### **PC / タブレット（768px〜）**
- ✅ タブメニュー（ヘッダー固定）
- ✅ Buy/Sell を横並び2カラム
- ✅ テーブル全項目表示

### **スマホ（〜767px）**
- ✅ ハンバーガーメニュー
- ✅ Buy/Sell を縦並び（タブ切り替え）
- ✅ テーブル簡略表示（重要項目のみ）

---

## データフェッチング

### **TanStack Query使用**

```typescript
// lib/hooks/use-rounds.ts
import { useQuery } from '@tanstack/react-query';
import { getRounds } from '@/lib/api/generated';

export function useRounds(roundType?: 'BUY' | 'SELL') {
  return useQuery({
    queryKey: ['rounds', roundType],
    queryFn: () => getRounds({ roundType }),
  });
}
```

### **サーバーコンポーネント vs クライアントコンポーネント**

#### サーバーコンポーネント（デフォルト）
- ✅ 初期データ取得
- ✅ SEO対応
- ✅ パフォーマンス向上

```tsx
// app/rounds/page.tsx
import { getRounds } from '@/lib/api/generated';

export default async function RoundsPage() {
  const rounds = await getRounds();

  return <RoundList rounds={rounds} />;
}
```

#### クライアントコンポーネント
- ✅ インタラクティブな操作
- ✅ リアルタイム更新
- ✅ 検索・フィルタ

```tsx
// components/stocks/stock-search.tsx
'use client';

import { useStockSearch } from '@/lib/hooks/use-stock-search';

export function StockSearch() {
  const { data, isLoading } = useStockSearch(query);

  return <CommandMenu results={data} />;
}
```

---

## コンポーネント設計

### **Atomic Design風の分類**

```
components/
├── ui/              # Atoms（shadcn/ui）
│   ├── button.tsx
│   ├── card.tsx
│   └── ...
│
├── layout/          # Layout
│   ├── header.tsx
│   └── navigation.tsx
│
├── rounds/          # Organisms（ドメイン固有）
│   ├── round-summary.tsx
│   └── recommendation-table.tsx
│
└── stocks/          # Organisms（ドメイン固有）
    ├── stock-card.tsx
    └── stock-chart.tsx
```

### **コンポーネント例**

#### RecommendationTable

```tsx
// components/rounds/recommendation-table.tsx
'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

interface Recommendation {
  stockCode: string;
  companyName: string;
  predictedReturn: number;
  confidenceScore: number;
}

interface Props {
  recommendations: Recommendation[];
  type: 'BUY' | 'SELL';
}

export function RecommendationTable({ recommendations, type }: Props) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>順位</TableHead>
          <TableHead>銘柄</TableHead>
          <TableHead>予測騰落率</TableHead>
          <TableHead>信頼度</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {recommendations.map((rec, index) => (
          <TableRow key={rec.stockCode}>
            <TableCell>{index + 1}</TableCell>
            <TableCell>
              {rec.stockCode} {rec.companyName}
            </TableCell>
            <TableCell className={type === 'BUY' ? 'text-green-600' : 'text-red-600'}>
              {rec.predictedReturn > 0 ? '+' : ''}{rec.predictedReturn}%
            </TableCell>
            <TableCell>
              <Badge variant="outline">{(rec.confidenceScore * 100).toFixed(1)}%</Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

---

## Backend API連携

### **OpenAPI型自動生成フロー**

```
Backend (FastAPI)
  ↓ OpenAPI Spec公開
  ↓ http://localhost:8000/openapi.json
  ↓
@hey-api/openapi-ts
  ↓ 型生成コマンド: pnpm generate
  ↓
lib/api/generated/
  ├── client.gen.ts
  ├── types.gen.ts
  └── ...
  ↓
Frontend使用
```

### **設定ファイル**

```typescript
// openapi-ts.config.ts
import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  client: '@hey-api/client-fetch',
  input: 'http://localhost:8000/openapi.json',
  output: {
    path: './lib/api/generated',
    format: 'prettier',
  },
  types: {
    enums: 'javascript',
  },
});
```

### **APIクライアント設定**

```typescript
// lib/api/client.ts
import { client } from './generated/client.gen';

// ベースURL設定
client.setConfig({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
});

export { client };
```

---

## スタイリング

### **Tailwind CSS v4**

```css
/* app/globals.css */
@import "tailwindcss";

@theme {
  /* カスタムカラー */
  --color-brand: #0ea5e9;

  /* カスタムフォント */
  --font-display: ui-serif, system-ui;
}

/* カスタムユーティリティ */
@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
}
```

### **shadcn/ui カラースキーム**

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // 騰落率カラー
        positive: '#16a34a',  // 緑
        negative: '#dc2626',  // 赤
      },
    },
  },
  plugins: [],
};

export default config;
```

---

## ナビゲーション

### **タブメニュー（PC/タブレット）**

```tsx
// components/layout/navigation.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

export function Navigation() {
  const pathname = usePathname();

  return (
    <Tabs value={pathname} className="w-full">
      <TabsList>
        <TabsTrigger value="/" asChild>
          <Link href="/">🏠 ホーム</Link>
        </TabsTrigger>
        <TabsTrigger value="/predictions" asChild>
          <Link href="/predictions">🤖 今週の予測</Link>
        </TabsTrigger>
        <TabsTrigger value="/rounds" asChild>
          <Link href="/rounds">📊 過去の結果</Link>
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
```

### **ハンバーガーメニュー（スマホ）**

```tsx
// components/layout/mobile-nav.tsx
'use client';

import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Menu } from 'lucide-react';
import Link from 'next/link';

export function MobileNav() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon">
          <Menu />
        </Button>
      </SheetTrigger>
      <SheetContent side="left">
        <nav className="flex flex-col gap-4">
          <Link href="/">🏠 ホーム</Link>
          <Link href="/predictions">🤖 今週の予測</Link>
          <Link href="/rounds">📊 過去の結果</Link>
        </nav>
      </SheetContent>
    </Sheet>
  );
}
```

---

## パフォーマンス最適化

### **Next.js App Router機能活用**

1. **Server Components（デフォルト）**
   - 初期データ取得を高速化
   - JavaScriptバンドルサイズ削減

2. **Streaming SSR**
   - Suspense境界で部分的にレンダリング
   - ローディング体験向上

3. **画像最適化**
   - `next/image`使用
   - 自動WebP変換

4. **フォント最適化**
   - `next/font`使用
   - レイアウトシフト防止

---

## 開発フロー

### **開発サーバー起動**

```bash
cd frontend
pnpm install
pnpm dev  # http://localhost:3000
```

### **型生成（Backend変更時）**

```bash
# Backend起動後に実行
pnpm generate
```

### **Lint & Format**

```bash
pnpm lint       # ESLint
pnpm lint:fix   # 自動修正
```

### **TypeScript型チェック**

```bash
pnpm typecheck
```

---

## 最終更新

- **日時**: 2026-07-21
- **更新者**: Claude Code
