"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  roundType?: string;
  indexFilter: string;
}

export function Pagination({ currentPage, totalPages, roundType, indexFilter }: PaginationProps) {
  const buildHref = (page: number) => {
    const params = new URLSearchParams();
    params.set("page", page.toString());
    params.set("index_filter", indexFilter);
    if (roundType) {
      params.set("round_type", roundType);
    }
    return `/history?${params.toString()}`;
  };

  // ページ番号の配列を生成（現在のページ前後2ページ）
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const showRange = 2; // 現在のページ前後に表示するページ数

    if (totalPages <= 7) {
      // 総ページ数が少ない場合は全て表示
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // 常に最初のページを表示
      pages.push(1);

      // 左側の省略記号
      if (currentPage > showRange + 2) {
        pages.push("...");
      }

      // 現在のページ周辺
      const start = Math.max(2, currentPage - showRange);
      const end = Math.min(totalPages - 1, currentPage + showRange);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      // 右側の省略記号
      if (currentPage < totalPages - showRange - 1) {
        pages.push("...");
      }

      // 常に最後のページを表示
      pages.push(totalPages);
    }

    return pages;
  };

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="flex items-center justify-center gap-2 mt-8">
      {/* 前へ */}
      <Link href={buildHref(Math.max(1, currentPage - 1))}>
        <Button
          variant="outline"
          size="sm"
          disabled={currentPage === 1}
          className="disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ← 前へ
        </Button>
      </Link>

      {/* ページ番号 */}
      <div className="flex gap-1">
        {getPageNumbers().map((page, index) => {
          if (page === "...") {
            return (
              <span key={`ellipsis-${index}`} className="px-3 py-2 text-muted-foreground">
                ...
              </span>
            );
          }

          const pageNum = page as number;
          const isActive = pageNum === currentPage;

          return (
            <Link key={pageNum} href={buildHref(pageNum)}>
              <Button
                variant={isActive ? "default" : "outline"}
                size="sm"
                className={isActive ? "bg-blue-600 hover:bg-blue-700" : ""}
              >
                {pageNum}
              </Button>
            </Link>
          );
        })}
      </div>

      {/* 次へ */}
      <Link href={buildHref(Math.min(totalPages, currentPage + 1))}>
        <Button
          variant="outline"
          size="sm"
          disabled={currentPage === totalPages}
          className="disabled:opacity-50 disabled:cursor-not-allowed"
        >
          次へ →
        </Button>
      </Link>
    </div>
  );
}
