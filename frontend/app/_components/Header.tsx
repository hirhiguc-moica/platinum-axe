"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function Header() {
  const pathname = usePathname();

  const navItems = [
    { label: "総合", href: "/all" },
    { label: "💎 日経225", href: "/nikkei225" },
    { label: "📊 TOPIX", href: "/topix" },
    { label: "過去の結果", href: "/history" },
    { label: "About", href: "/about" },
  ];

  const isActive = (href: string) => {
    if (href === "/history" || href === "/about") {
      return pathname === href;
    }
    // /all, /nikkei225, /topix などのフィルタページ
    return pathname === href || pathname.startsWith(href + "/");
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 flex h-14 items-center">
        <div className="mr-4 flex">
          <Link href="/all" className="mr-6 flex items-center space-x-2">
            <span className="text-xl">🪓</span>
            <span className="hidden font-bold sm:inline-block">
              Platinum Axe
            </span>
          </Link>
        </div>
        <nav className="flex items-center space-x-6 text-sm font-medium">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`transition-colors hover:text-foreground/80 ${
                isActive(item.href)
                  ? "text-foreground"
                  : "text-foreground/60"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
