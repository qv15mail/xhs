import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QrCode, Play, RefreshCw, CheckCircle2, ScanLine } from "lucide-react";
import { api } from "@/api/client";
import { LoginDialog } from "@/components/layout/LoginDialog";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardHeader, Input, Label, Select, Switch, Badge, Progress } from "@/components/ui/primitives";
import { Button } from "@/components/ui/Button";
import { Skeleton, EmptyState } from "@/components/ui/states";
import { useAppStore } from "@/store/app";
import { formatDate } from "@/lib/utils";
import type { CollectTask, TaskStatus } from "@/lib/types";

const statusTone: Record<TaskStatus, "success" | "accent" | "warning" | "danger"> = {
  success: "success",
  running: "accent",
  pending: "warning",
  failed: "danger",
};
const statusLabel: Record<TaskStatus, string> = {
  success: "已完成",
  running: "采集中",
  pending: "等待中",
  failed: "失败",
};

function LoginCard() {
  const loggedIn = useAppStore((s) => s.loggedIn);
  const setLoggedIn = useAppStore((s) => s.setLoggedIn);
  const [open, setOpen] = useState(false);
  const logout = async () => {
    try {
      await api.logout();
    } catch {
      /* ignore */
    }
    setLoggedIn(false);
  };
  return (
    <Card>
      <CardHeader title="登录态" description="使用本人账号扫码登录后方可采集" />
      <div className="flex flex-col items-center gap-4 p-6">
        {loggedIn ? (
          <>
            <div className="flex h-32 w-32 items-center justify-center rounded-lg bg-success/10 text-success">
              <CheckCircle2 className="h-12 w-12" />
            </div>
            <p className="text-sm text-text">账号已登录（在线）</p>
            <Button variant="secondary" size="sm" onClick={logout}>
              退出登录
            </Button>
          </>
        ) : (
          <>
            <div className="flex h-32 w-32 items-center justify-center rounded-lg border border-dashed border-border bg-bg text-text-mut">
              <QrCode className="h-12 w-12" />
            </div>
            <p className="text-center text-sm text-text-mut">
              使用小红书 App 扫码登录本人账号后开始采集
            </p>
            <Button size="sm" onClick={() => setOpen(true)}>
              <ScanLine className="h-4 w-4" />
              扫码登录
            </Button>
          </>
        )}
      </div>
      <LoginDialog open={open} onClose={() => setOpen(false)} />
    </Card>
  );
}

export function Collect() {
  const qc = useQueryClient();
  const loggedIn = useAppStore((s) => s.loggedIn);
  const [topic, setTopic] = useState("");
  const [count, setCount] = useState(30);
  const [sort, setSort] = useState<CollectTask["sort"]>("comprehensive");
  const [includeComments, setIncludeComments] = useState(false);

  const tasks = useQuery({ queryKey: ["tasks"], queryFn: api.listTasks });

  const create = useMutation({
    mutationFn: () => api.createTask({ topic, total: count, sort, includeComments }),
    onSuccess: () => {
      setTopic("");
      qc.invalidateQueries({ queryKey: ["tasks"] });
    },
  });

  const hasActive = tasks.data?.some((t) => t.status === "running" || t.status === "pending");
  useEffect(() => {
    if (!hasActive) return;
    const id = setInterval(() => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
    }, 1200);
    return () => clearInterval(id);
  }, [hasActive, qc]);

  return (
    <div>
      <PageHeader title="采集" description="输入主题，自动采集相关笔记" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="新建采集任务" />
          <div className="space-y-4 p-5">
            <div>
              <Label htmlFor="topic">主题 / 关键词</Label>
              <Input
                id="topic"
                placeholder="例如：春季敏感肌护肤"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="count">采集数量：{count}</Label>
                <input
                  id="count"
                  type="range"
                  min={10}
                  max={100}
                  step={10}
                  value={count}
                  onChange={(e) => setCount(Number(e.target.value))}
                  className="h-10 w-full accent-[var(--accent)]"
                />
              </div>
              <div>
                <Label htmlFor="sort">排序</Label>
                <Select id="sort" value={sort} onChange={(e) => setSort(e.target.value as CollectTask["sort"])}>
                  <option value="comprehensive">综合排序</option>
                  <option value="latest">最新发布</option>
                  <option value="hottest">最多互动</option>
                </Select>
              </div>
            </div>
            <div className="flex items-center justify-between rounded-md border border-border px-4 py-3">
              <div>
                <p className="text-sm font-medium text-text">同时采集评论</p>
                <p className="text-xs text-text-mut">开启后耗时更长，限速更保守</p>
              </div>
              <Switch checked={includeComments} onChange={setIncludeComments} label="同时采集评论" />
            </div>

            {!loggedIn && (
              <p className="rounded-md bg-warning/10 px-3 py-2 text-xs text-warning">
                需先在右侧完成登录才能开始采集。
              </p>
            )}

            <Button
              className="w-full"
              loading={create.isPending}
              disabled={!topic.trim() || !loggedIn}
              onClick={() => create.mutate()}
            >
              <Play className="h-4 w-4" />
              开始采集
            </Button>
          </div>
        </Card>

        <LoginCard />
      </div>

      <Card className="mt-6">
        <CardHeader
          title="采集任务"
          action={
            <Button variant="ghost" size="sm" onClick={() => tasks.refetch()}>
              <RefreshCw className="h-4 w-4" />
              刷新
            </Button>
          }
        />
        <div className="divide-y divide-border">
          {tasks.isLoading ? (
            Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="m-4 h-16" />)
          ) : tasks.data && tasks.data.length > 0 ? (
            tasks.data.map((t) => (
              <div key={t.id} className="px-5 py-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-text">{t.topic}</p>
                    <p className="text-xs text-text-mut">
                      {formatDate(t.createdAt)} · 目标 {t.total} 条
                    </p>
                  </div>
                  <Badge tone={statusTone[t.status]}>{statusLabel[t.status]}</Badge>
                </div>
                {t.status === "running" && (
                  <div className="mt-3 flex items-center gap-3">
                    <Progress value={t.progress} total={t.total} />
                    <span className="shrink-0 text-xs tabular text-text-mut">
                      {t.progress}/{t.total}
                    </span>
                  </div>
                )}
                {t.status === "failed" && t.error && (
                  <p className="mt-2 text-xs text-danger">{t.error}</p>
                )}
              </div>
            ))
          ) : (
            <EmptyState title="还没有采集任务" description="在上方新建一个主题任务" />
          )}
        </div>
      </Card>
    </div>
  );
}
