import type { LucideIcon } from "lucide-react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { Card } from "@/components/ui/primitives";

export function MetricCard({
  label,
  value,
  icon: Icon,
  trend,
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  trend?: { dir: "up" | "down"; text: string };
}) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-text-mut">{label}</span>
        <span className="flex h-9 w-9 items-center justify-center rounded-md bg-bg text-text-mut">
          <Icon className="h-[18px] w-[18px]" />
        </span>
      </div>
      <p className="mt-3 text-2xl font-semibold tabular text-text">{value}</p>
      {trend && (
        <p
          className={`mt-1 flex items-center gap-1 text-xs ${
            trend.dir === "up" ? "text-success" : "text-danger"
          }`}
        >
          {trend.dir === "up" ? (
            <TrendingUp className="h-3.5 w-3.5" />
          ) : (
            <TrendingDown className="h-3.5 w-3.5" />
          )}
          {trend.text}
        </p>
      )}
    </Card>
  );
}
