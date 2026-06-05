import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { FileText, Radar, Heart, Activity, Plus } from "lucide-react";
import { api } from "@/api/client";
import { PageHeader } from "@/components/common/PageHeader";
import { MetricCard } from "@/components/common/MetricCard";
import { Card, CardHeader, Badge } from "@/components/ui/primitives";
import { Button } from "@/components/ui/Button";
import { Skeleton, ErrorState, EmptyState } from "@/components/ui/states";
import { formatNumber, formatDate } from "@/lib/utils";
import type { TaskStatus } from "@/lib/types";

const statusMap: Record<TaskStatus | "none", { label: string; tone: "success" | "warning" | "danger" | "neutral" | "accent" }> = {
  success: { label: "已完成", tone: "success" },
  running: { label: "采集中", tone: "accent" },
  pending: { label: "等待中", tone: "warning" },
  failed: { label: "失败", tone: "danger" },
  none: { label: "暂无", tone: "neutral" },
};

export function Dashboard() {
  const navigate = useNavigate();
  const stats = useQuery({ queryKey: ["stats"], queryFn: api.getStats });
  const tasks = useQuery({ queryKey: ["tasks"], queryFn: api.listTasks });

  return (
    <div>
      <PageHeader
        title="仪表盘"
        description="掌握采集进度与内容概览"
        action={
          <Button onClick={() => navigate("/collect")}>
            <Plus className="h-4 w-4" />
            新建采集任务
          </Button>
        }
      />

      {stats.isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : stats.isError ? (
        <Card>
          <ErrorState onRetry={() => stats.refetch()} />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="累计笔记" value={formatNumber(stats.data!.totalNotes)} icon={FileText} />
          <MetricCard label="采集任务" value={String(stats.data!.totalTasks)} icon={Radar} />
          <MetricCard
            label="平均互动"
            value={formatNumber(stats.data!.avgEngagement)}
            icon={Heart}
            trend={{ dir: "up", text: "较上周 +12%" }}
          />
          <MetricCard
            label="最近任务"
            value={statusMap[stats.data!.lastTaskStatus].label}
            icon={Activity}
          />
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="采集趋势" description="近 7 天采集笔记数量" />
          <div className="h-64 p-4">
            {stats.isLoading ? (
              <Skeleton className="h-full w-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.data?.trend ?? []}>
                  <defs>
                    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#2563EB" stopOpacity={0.25} />
                      <stop offset="100%" stopColor="#2563EB" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8EAED" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(v) => formatDate(v).slice(5)}
                    tick={{ fontSize: 12, fill: "#6B7280" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis tick={{ fontSize: 12, fill: "#6B7280" }} axisLine={false} tickLine={false} />
                  <Tooltip
                    labelFormatter={(v) => formatDate(String(v))}
                    contentStyle={{ borderRadius: 10, border: "1px solid #E8EAED", fontSize: 13 }}
                  />
                  <Area type="monotone" dataKey="count" stroke="#2563EB" strokeWidth={2} fill="url(#g)" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        <Card>
          <CardHeader title="最近任务" action={<Button variant="ghost" size="sm" onClick={() => navigate("/collect")}>全部</Button>} />
          <div className="divide-y divide-border">
            {tasks.isLoading ? (
              Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="m-4 h-12" />)
            ) : tasks.data && tasks.data.length > 0 ? (
              tasks.data.slice(0, 5).map((t) => {
                const s = statusMap[t.status];
                return (
                  <div key={t.id} className="flex items-center justify-between px-5 py-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-text">{t.topic}</p>
                      <p className="text-xs text-text-mut">
                        {formatDate(t.createdAt)} · {t.progress}/{t.total}
                      </p>
                    </div>
                    <Badge tone={s.tone}>{s.label}</Badge>
                  </div>
                );
              })
            ) : (
              <EmptyState
                title="还没有采集任务"
                description="新建一个主题，开始采集"
                action={
                  <Button size="sm" onClick={() => navigate("/collect")}>
                    去新建
                  </Button>
                }
              />
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
