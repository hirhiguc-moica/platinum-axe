import { Badge } from "@/components/ui/badge";

interface RankBadgeProps {
  rank: number;
}

export function RankBadge({ rank }: RankBadgeProps) {
  if (rank === 1) {
    return (
      <Badge className="gradient-gold text-white font-bold px-3 py-1 text-sm">
        🏆 {rank}位
      </Badge>
    );
  }

  if (rank === 2) {
    return (
      <Badge className="bg-slate-400 text-slate-900 font-bold px-3 py-1 text-sm">
        🥈 {rank}位
      </Badge>
    );
  }

  if (rank === 3) {
    return (
      <Badge className="bg-amber-700 text-white font-bold px-3 py-1 text-sm">
        🥉 {rank}位
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className="px-3 py-1 text-sm font-semibold">
      {rank}位
    </Badge>
  );
}
