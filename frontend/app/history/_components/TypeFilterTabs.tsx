"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

interface TypeFilterTabsProps {
  currentType: "all" | "buy" | "sell";
  indexFilter: string;
}

export function TypeFilterTabs({ currentType, indexFilter }: TypeFilterTabsProps) {
  const tabs = [
    { label: "すべて", value: "all" as const },
    { label: "買い推奨", value: "buy" as const },
    { label: "売り推奨", value: "sell" as const },
  ];

  return (
    <div className="flex gap-2 flex-wrap">
      {tabs.map((tab) => {
        const isActive = currentType === tab.value;
        const href =
          tab.value === "all"
            ? `/history?index_filter=${indexFilter}`
            : `/history?round_type=${tab.value.toUpperCase()}&index_filter=${indexFilter}`;

        return (
          <Link key={tab.value} href={href}>
            <Button
              variant={isActive ? "default" : "outline"}
              className={`${
                isActive
                  ? tab.value === "buy"
                    ? "bg-emerald-600 hover:bg-emerald-700"
                    : tab.value === "sell"
                      ? "bg-red-600 hover:bg-red-700"
                      : "bg-blue-600 hover:bg-blue-700"
                  : ""
              }`}
            >
              {tab.label}
            </Button>
          </Link>
        );
      })}
    </div>
  );
}
