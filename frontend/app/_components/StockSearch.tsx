"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

interface StockSearchResult {
  stock_code: string;
  company_name: string;
  sector_name: string | null;
  market_name: string | null;
  market_abbreviation: string | null;
  is_nikkei225: boolean;
  is_topix: boolean;
}

export function StockSearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StockSearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // 外側クリックで閉じる
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // 検索API呼び出し（debounce処理）
  useEffect(() => {
    if (query.length === 0) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(
          `${API_URL}/api/v1/stocks/search?q=${encodeURIComponent(query)}&limit=10`
        );

        if (response.ok) {
          const data = await response.json();
          setResults(data.stocks || []);
          setIsOpen(true);
        }
      } catch (error) {
        console.error("Search error:", error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300); // 300msのdebounce

    return () => clearTimeout(timer);
  }, [query]);

  const handleSelectStock = (stockCode: string) => {
    setQuery("");
    setResults([]);
    setIsOpen(false);
    router.push(`/stocks/${stockCode}`);
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-lg">
      {/* 検索ボックス */}
      <div className="relative">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="🔍 銘柄コード or 会社名"
          className="w-full px-4 py-2 bg-[#1e1e1e] border border-[#3e3e42] rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
        />
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
      </div>

      {/* サジェストリスト */}
      {isOpen && results.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-[#1e1e1e] border border-[#3e3e42] rounded-lg shadow-lg max-h-80 overflow-y-auto">
          {results.map((stock) => (
            <button
              key={stock.stock_code}
              onClick={() => handleSelectStock(stock.stock_code)}
              className="w-full px-4 py-3 text-left hover:bg-[#2d2d30] transition-colors border-b border-[#3e3e42] last:border-b-0"
            >
              <div>
                {/* 1行目: 銘柄コード + 会社名 */}
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-mono text-accent flex-shrink-0">
                    {stock.stock_code}
                  </span>
                  <span className="text-sm font-semibold text-foreground">
                    {stock.company_name}
                  </span>
                </div>
                {/* 2行目: 市場略称 + N225 + TPX */}
                <div className="flex items-center gap-2 text-xs">
                  {stock.market_abbreviation && (
                    <span className="text-muted-foreground">{stock.market_abbreviation}</span>
                  )}
                  {stock.is_nikkei225 && (
                    <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-semibold">
                      N225
                    </span>
                  )}
                  {stock.is_topix && (
                    <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-400 font-semibold">
                      TPX
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* 検索結果なし */}
      {isOpen && query.length > 0 && results.length === 0 && !isLoading && (
        <div className="absolute z-50 w-full mt-2 bg-[#1e1e1e] border border-[#3e3e42] rounded-lg shadow-lg px-4 py-3">
          <p className="text-sm text-muted-foreground text-center">
            「{query}」に一致する銘柄が見つかりませんでした
          </p>
        </div>
      )}
    </div>
  );
}
