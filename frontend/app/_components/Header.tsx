"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { StockSearch } from "./StockSearch";

export function Header() {
  const pathname = usePathname();

  const navItems = [
    { label: "総合", href: "/all" },
    { label: "💎 日経225", href: "/nikkei225" },
    { label: "📊 TOPIX", href: "/topix" },
    { label: "過去の結果", href: "/history" },
    { label: "使い方", href: "/about" },
  ];

  const isActive = (href: string) => {
    if (href === "/history" || href === "/about") {
      return pathname === href;
    }
    // /all, /nikkei225, /topix などのフィルタページ
    return pathname === href || pathname.startsWith(href + "/");
  };

  return (
    <>
      {/* システム説明バナー（スクロールすると消える） */}
      <div className="w-full bg-gradient-to-r from-[#1e1e1e] via-[#252526] to-[#1e1e1e] border-b border-[#3e3e42]">
        <div className="container mx-auto px-4 py-3 text-center">
          <p className="text-sm text-[#cccccc] font-medium">
            個人投資家に{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 font-semibold">
              クオンツ分析 × AI
            </span>{" "}
            によるデータ・ドリブンな株取引を
          </p>
        </div>
      </div>

      {/* メインヘッダー（sticky） */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 flex h-14 items-center justify-between gap-4">
          {/* 左側: ロゴ + ナビゲーション */}
          <div className="flex items-center gap-4">
            <div className="flex">
              <Link href="/all" className="mr-6 flex items-center space-x-2">
                <span className="text-xl">🪓</span>
                <span className="hidden font-bold sm:inline-block">
                  Platinum Axe
                </span>
              </Link>
            </div>
            <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`transition-colors hover:text-foreground/80 ${
                    isActive(item.href) ? "text-foreground" : "text-foreground/60"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>

          {/* 右側: 検索ボックス（PC用） */}
          <div className="hidden md:flex">
            <StockSearch />
          </div>

          {/* SP用: ハンバーガーメニュー（将来的に実装） */}
          <nav className="flex md:hidden items-center space-x-4 text-sm font-medium">
            {navItems.slice(0, 2).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`transition-colors hover:text-foreground/80 ${
                  isActive(item.href) ? "text-foreground" : "text-foreground/60"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
    </>
  );
}
