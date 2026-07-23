"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

interface IndexFilterTabsProps {
  currentIndex: string;
  roundType?: string;
}

export function IndexFilterTabs({ currentIndex, roundType }: IndexFilterTabsProps) {
  const tabs = [
    { label: "総合", value: "all" },
    { label: "NIKKEI225", value: "nikkei225" },
    { label: "TOPIX", value: "topix" },
  ];

  return (
    <div className="flex gap-2 flex-wrap">
      {tabs.map((tab) => {
        const isActive = currentIndex === tab.value;
        const params = new URLSearchParams();
        params.set("index_filter", tab.value);
        if (roundType) {
          params.set("round_type", roundType);
        }
        const href = `/history?${params.toString()}`;

        return (
          <Link key={tab.value} href={href}>
            <Button variant={isActive ? "default" : "ghost"} size="sm">
              {tab.label}
            </Button>
          </Link>
        );
      })}
    </div>
  );
}
