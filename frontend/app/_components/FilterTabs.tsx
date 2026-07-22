"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";

interface FilterTabsProps {
  filter: string; // "all" | "nikkei225" | "topix"
}

export function FilterTabs({ filter }: FilterTabsProps) {
  const pathname = usePathname();
  const currentType = pathname.includes("/sell") ? "sell" : "buy";

  const tabs = [
    { label: "📈 買い推奨", value: "buy", color: "emerald" },
    { label: "📉 売り推奨", value: "sell", color: "red" },
  ];

  return (
    <div className="flex gap-2">
      {tabs.map((tab) => {
        const isActive = currentType === tab.value;
        return (
          <Link key={tab.value} href={`/${filter}/${tab.value}`}>
            <Button
              variant={isActive ? "default" : "outline"}
              className={`${
                isActive
                  ? tab.value === "buy"
                    ? "bg-emerald-600 hover:bg-emerald-700"
                    : "bg-red-600 hover:bg-red-700"
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
