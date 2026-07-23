import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "404 - ページが見つかりません | Platinum Axe",
  description: "お探しのページは存在しないか、移動した可能性があります。",
};

export default function NotFoundPage() {
  return (
    <div className="container mx-auto px-4 py-16 flex items-center justify-center min-h-[70vh]">
      <div className="max-w-md w-full text-center">
        {/* アイコン */}
        <div className="mb-8">
          <span className="text-6xl">🔍</span>
        </div>

        {/* タイトル */}
        <h1 className="text-4xl font-bold mb-4 text-foreground">
          404 - ページが見つかりません
        </h1>

        {/* 説明文 */}
        <p className="text-lg text-muted-foreground mb-8">
          お探しのページは存在しないか、
          <br />
          移動した可能性があります。
        </p>

        {/* ホームに戻るボタン */}
        <Link
          href="/all"
          className="inline-block bg-gradient-to-r from-accent via-yellow-400 to-accent text-primary-foreground font-semibold px-8 py-3 rounded-lg hover:opacity-90 transition-opacity shadow-lg"
        >
          ホームに戻る
        </Link>

        {/* 補足リンク */}
        <div className="mt-8 space-y-2">
          <p className="text-sm text-muted-foreground">または以下のページへ：</p>
          <div className="flex flex-wrap justify-center gap-4 text-sm">
            <Link
              href="/all"
              className="text-accent hover:text-accent/80 underline"
            >
              総合ランキング
            </Link>
            <Link
              href="/history"
              className="text-accent hover:text-accent/80 underline"
            >
              過去の結果
            </Link>
            <Link
              href="/about"
              className="text-accent hover:text-accent/80 underline"
            >
              使い方
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
