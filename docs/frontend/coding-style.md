# Frontend コーディング規約

**最終更新**: 2026-07-21

---

## 概要

Next.js 15 + React 19 + TypeScript を使用したFrontend開発のコーディング規約です。

---

## ツール構成

### フォーマッター: Prettier

```bash
cd frontend
pnpm format        # フォーマット実行
pnpm format:check  # チェックのみ
```

### リンター: ESLint

```bash
cd frontend
pnpm lint     # リント実行
pnpm lint:fix # 自動修正
```

### 型チェック: TypeScript

```bash
cd frontend
pnpm type-check
```

---

## 基本スタイル

### インデント・改行

- **インデント**: スペース2つ（Prettierデフォルト）
- **行長**: 100文字以内
- **改行**: Unix形式（LF）
- **セミコロン**: なし（Prettierデフォルト）

### インポート

**順序**（ESLintが自動整理）:

1. React
2. 外部ライブラリ
3. 内部モジュール（エイリアス使用）
4. 相対パス
5. CSS/型定義

```typescript
// 1. React
import { useState, useEffect } from 'react'

// 2. 外部ライブラリ
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'

// 3. 内部モジュール（エイリアス）
import { getRounds } from '@/lib/api/rounds'
import type { Round } from '@/types/api'

// 4. 相対パス
import { RoundCard } from './_components/RoundCard'

// 5. CSS/型定義
import styles from './page.module.css'
```

---

## ファイル・ディレクトリ構造

### ファイル命名

- **コンポーネント**: パスカルケース `RoundCard.tsx`
- **ユーティリティ**: キャメルケース `formatDate.ts`
- **定数**: キャメルケース `apiRoutes.ts`
- **型定義**: キャメルケース `types.ts`

### ディレクトリ構造

```
frontend/app/
├── _components/        # 共有コンポーネント（アンダースコアプレフィックス）
│   ├── Header.tsx
│   └── Footer.tsx
├── _lib/               # ユーティリティ・API（アンダースコアプレフィックス）
│   ├── api/
│   │   └── rounds.ts
│   └── utils/
│       └── formatDate.ts
├── _constants/         # 定数（アンダースコアプレフィックス）
│   └── routes.ts
├── [feature]/          # 機能別ディレクトリ
│   ├── _components/    # 機能専用コンポーネント
│   ├── page.tsx        # ページコンポーネント
│   └── layout.tsx      # レイアウトコンポーネント（必要な場合）
├── layout.tsx          # ルートレイアウト
└── providers.tsx       # プロバイダー設定
```

**アンダースコアプレフィックス**:
- Next.js App Routerでは、`_`プレフィックスのディレクトリはルーティングから除外される
- 共有コンポーネント・ユーティリティに使用

---

## React コンポーネント

### Server Components vs Client Components

**原則**: デフォルトはServer Components、必要な時のみClient Components

```typescript
// Server Component（デフォルト）
// ファイル先頭に 'use client' がない
export default async function RoundsPage() {
  const rounds = await getRounds()
  return <div>{/* ... */}</div>
}

// Client Component（必要な場合のみ）
// useState, useEffect, イベントハンドラー等を使う場合
'use client'

import { useState } from 'react'

export function RoundCard() {
  const [isExpanded, setIsExpanded] = useState(false)
  return <div onClick={() => setIsExpanded(!isExpanded)}>{/* ... */}</div>
}
```

### コンポーネント定義

**名前付きエクスポート vs デフォルトエクスポート**:

- **ページコンポーネント**: デフォルトエクスポート（Next.js要件）
- **それ以外**: 名前付きエクスポート推奨

```typescript
// ページコンポーネント（page.tsx）
export default function RoundsPage() {
  return <div>Rounds</div>
}

// 通常のコンポーネント
export function RoundCard({ round }: { round: Round }) {
  return <div>{round.round_id}</div>
}
```

### Props の型定義

```typescript
// Good: インライン型定義（シンプルな場合）
export function RoundCard({ round }: { round: Round }) {
  return <div>{round.round_id}</div>
}

// Good: 型エイリアス（複雑な場合）
type RoundCardProps = {
  round: Round
  onSelect?: (round: Round) => void
  isActive?: boolean
}

export function RoundCard({ round, onSelect, isActive = false }: RoundCardProps) {
  return <div onClick={() => onSelect?.(round)}>{round.round_id}</div>
}

// Bad: インターフェース（型エイリアス推奨）
interface RoundCardProps {
  round: Round
}
```

### 条件付きレンダリング

```typescript
// Good: 早期リターン
if (!round) {
  return <div>Loading...</div>
}

return <div>{round.round_id}</div>

// Good: 三項演算子（シンプルな場合）
return <div>{isActive ? 'Active' : 'Inactive'}</div>

// Good: 論理演算子（条件によって表示/非表示）
return (
  <div>
    {isActive && <span>Active</span>}
    {error && <ErrorMessage error={error} />}
  </div>
)

// Bad: 複雑な三項演算子のネスト
return (
  <div>
    {isActive ? (
      isExpanded ? (
        <ExpandedView />
      ) : (
        <CollapsedView />
      )
    ) : (
      <InactiveView />
    )}
  </div>
)
```

---

## shadcn/ui の使い方

### インストール

```bash
cd frontend
pnpm dlx shadcn@latest init
pnpm dlx shadcn@latest add button
```

### コンポーネント使用

```typescript
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

export function RoundCard({ round }: { round: Round }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{round.round_id}</CardTitle>
      </CardHeader>
      <CardContent>
        <p>Start: {round.start_date}</p>
        <Button>View Details</Button>
      </CardContent>
    </Card>
  )
}
```

### カスタマイズ

**原則**: shadcn/uiコンポーネントは `components/ui/` にコピーされるので、直接編集可能

```typescript
// components/ui/button.tsx
// 必要に応じてカスタマイズ
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
```

---

## TanStack Query の使い方

### クエリ定義

```typescript
// app/_lib/api/rounds.ts
import { getRounds as getRoundsApi } from '@/generated/api'

export async function getRounds(roundType?: 'BUY' | 'SELL') {
  const response = await getRoundsApi({ roundType })
  return response.data
}
```

### カスタムフック

```typescript
// app/_lib/hooks/useRounds.ts
import { useQuery } from '@tanstack/react-query'
import { getRounds } from '@/lib/api/rounds'

export function useRounds(roundType?: 'BUY' | 'SELL') {
  return useQuery({
    queryKey: ['rounds', roundType],
    queryFn: () => getRounds(roundType),
  })
}
```

### コンポーネントでの使用

```typescript
'use client'

import { useRounds } from '@/lib/hooks/useRounds'

export function RoundsList() {
  const { data: rounds, isLoading, error } = useRounds('BUY')

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return (
    <div>
      {rounds?.map((round) => (
        <RoundCard key={round.round_id} round={round} />
      ))}
    </div>
  )
}
```

---

## 型定義

### API型定義（自動生成）

```typescript
// generated/api.ts
// @hey-api/openapi-ts で自動生成されるファイル
// 直接編集しない！
export type Round = {
  round_id: string
  round_type: 'BUY' | 'SELL'
  start_date: string
  end_date: string
  status: 'ACTIVE' | 'COMPLETED'
}
```

### ドメイン型定義

```typescript
// app/_types/domain.ts
// 必要に応じてAPI型を拡張
import type { Round as ApiRound } from '@/generated/api'

export type Round = ApiRound & {
  // 追加のプロパティ
  isExpanded?: boolean
}
```

---

## スタイリング: Tailwind CSS v4

### 基本的な使い方

```typescript
export function RoundCard({ round }: { round: Round }) {
  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <h3 className="text-lg font-semibold">{round.round_id}</h3>
      <p className="text-sm text-muted-foreground">{round.start_date}</p>
    </div>
  )
}
```

### 条件付きクラス: cn() ヘルパー

```typescript
import { cn } from '@/lib/utils'

export function Button({ isActive, className }: { isActive: boolean; className?: string }) {
  return (
    <button
      className={cn(
        'rounded-md px-4 py-2 font-medium',
        isActive ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground',
        className
      )}
    >
      Click me
    </button>
  )
}
```

### レスポンシブデザイン

```typescript
export function RoundCard() {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* モバイル: 1列, タブレット: 2列, PC: 3列 */}
    </div>
  )
}
```

---

## フォーム処理

### React Hook Form + Zod

```typescript
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const searchSchema = z.object({
  stockCode: z.string().min(4).max(10),
})

type SearchFormData = z.infer<typeof searchSchema>

export function SearchForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SearchFormData>({
    resolver: zodResolver(searchSchema),
  })

  const onSubmit = (data: SearchFormData) => {
    console.log(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('stockCode')} placeholder="銘柄コード" />
      {errors.stockCode && <p>{errors.stockCode.message}</p>}
      <button type="submit">検索</button>
    </form>
  )
}
```

---

## エラーハンドリング

### エラー境界（Error Boundary）

```typescript
// app/error.tsx
'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <p>{error.message}</p>
      <button onClick={reset}>Try again</button>
    </div>
  )
}
```

---

## パフォーマンス最適化

### 動的インポート

```typescript
import dynamic from 'next/dynamic'

// 遅延ロード
const HeavyChart = dynamic(() => import('./_components/HeavyChart'), {
  loading: () => <p>Loading chart...</p>,
  ssr: false, // SSRを無効化（クライアントサイドのみ）
})

export function StockDetailPage() {
  return (
    <div>
      <h1>Stock Detail</h1>
      <HeavyChart />
    </div>
  )
}
```

### React.memo

```typescript
import { memo } from 'react'

export const RoundCard = memo(function RoundCard({ round }: { round: Round }) {
  return <div>{round.round_id}</div>
})
```

---

## テスト

### Vitest + React Testing Library

```typescript
import { render, screen } from '@testing-library/react'
import { RoundCard } from './RoundCard'

describe('RoundCard', () => {
  it('should render round id', () => {
    const round = {
      round_id: 'R001',
      round_type: 'BUY',
      start_date: '2026-07-21',
      end_date: '2026-07-25',
      status: 'ACTIVE',
    }

    render(<RoundCard round={round} />)

    expect(screen.getByText('R001')).toBeInTheDocument()
  })
})
```

---

## 環境変数

### 定義（.env.local）

```bash
# Public（クライアントサイドで使用可能）
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Private（サーバーサイドのみ）
API_SECRET_KEY=secret
```

### 使用

```typescript
// Server Component（サーバーサイド）
const apiKey = process.env.API_SECRET_KEY

// Client Component（クライアントサイド）
const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL
```

---

## 最終更新

- **日時**: 2026-07-21
- **更新者**: Claude Code
