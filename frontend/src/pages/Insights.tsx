import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Hash, Trophy, ScanText, Sparkles } from "lucide-react";
import { api } from "@/api/client";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardHeader, Badge } from "@/components/ui/primitives";
import { Skeleton, EmptyState, ErrorState } from "@/components/ui/states";
import { formatNumber, cn } from "@/lib/utils";

type Tab = "keywords" | "ranking" | "breakdown";

const tabs: { id: Tab; label: string; icon: typeof Hash }[] = [
  { id: "keywords", label: "选题热词", icon: Hash },
  { id: "ranking", label: "爆款榜单", icon: Trophy },
  { id: "breakdown", label: "内容拆解", icon: ScanText },
];

function Keywords() {
  const q = useQuery({ queryKey: ["keywords"], queryFn: api.keywords });
  if (q.isLoading) return <Skeleton className="h-64" />;
  if (q.isError) return <ErrorState onRetry={() => q.refetch()} />;
  const max = Math.max(...(q.data ?? []).map((k) => k.count), 1);
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader title="热词云" description="字号越大代表出现频次越高" />
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 p-6">
          {q.data!.map((k) => {
            const scale = 0.8 + (k.count / max) * 1.4;
            return (
              <span
                key={k.word}
                className="font-semibold text-accent"
                style={{ fontSize: `${scale}rem`, opacity: 0.5 + (k.count / max) * 0.5 }}
              >
                {k.word}
              </span>
            );
          })}
        </div>
      </Card>
      <Card>
        <CardHeader title="词频明细" />
        <div className="divide-y divide-border">
          {q.data!.slice(0, 10).map((k) => (
            <div key={k.word} className="flex items-center gap-3 px-5 py-2.5">
              <span className="w-20 shrink-0 text-sm text-text">{k.word}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-bg">
                <div
                  className="h-full rounded-full bg-accent"
                  style={{ width: `${(k.count / max) * 100}%` }}
                />
              </div>
              <span className="w-8 shrink-0 text-right text-xs tabular text-text-mut">{k.count}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function Ranking() {
  const q = useQuery({ queryKey: ["ranking"], queryFn: api.ranking });
  if (q.isLoading) return <Skeleton className="h-80" />;
  if (q.isError) return <ErrorState onRetry={() => q.refetch()} />;
  return (
    <Card>
      <CardHeader title="爆款榜单" description="按互动综合分排序，并标注爆款特征" />
      <div className="divide-y divide-border">
        {q.data!.map((item, idx) => (
          <div key={item.noteId} className="flex items-center gap-4 px-5 py-3">
            <span
              className={cn(
                "flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-sm font-semibold tabular",
                idx < 3 ? "bg-primary text-primary-fg" : "bg-bg text-text-mut",
              )}
            >
              {idx + 1}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-text">{item.title}</p>
              <div className="mt-1 flex flex-wrap items-center gap-1.5">
                <span className="text-xs text-text-mut">{item.author}</span>
                {item.reasons.map((r) => (
                  <Badge key={r} tone="accent">
                    {r}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="shrink-0 text-right">
              <p className="text-sm font-semibold tabular text-text">{formatNumber(item.likes)}</p>
              <p className="text-xs text-text-mut">综合分 {item.score}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function BreakdownPanel() {
  const notes = useQuery({ queryKey: ["notes"], queryFn: () => api.listNotes() });
  const [selected, setSelected] = useState<string>("");
  const bd = useMutation({ mutationFn: (id: string) => api.breakdown(id) });

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-1">
        <CardHeader title="选择参考笔记" />
        <div className="max-h-96 divide-y divide-border overflow-y-auto">
          {notes.isLoading ? (
            Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="m-3 h-10" />)
          ) : (
            notes.data?.slice(0, 12).map((n) => (
              <button
                key={n.id}
                onClick={() => {
                  setSelected(n.id);
                  bd.mutate(n.id);
                }}
                className={cn(
                  "block w-full px-5 py-3 text-left text-sm transition-colors hover:bg-bg",
                  selected === n.id && "bg-bg",
                )}
              >
                <p className="line-clamp-1 font-medium text-text">{n.title}</p>
                <p className="text-xs text-text-mut">{n.author}</p>
              </button>
            ))
          )}
        </div>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader
          title="拆解结果"
          description="基于规则与 LLM 输出爆款结构（演示数据）"
          action={<Sparkles className="h-4 w-4 text-accent" />}
        />
        <div className="p-5">
          {!selected ? (
            <EmptyState title="请选择一篇笔记" description="点击左侧笔记开始拆解" />
          ) : bd.isPending ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : bd.data ? (
            <div className="space-y-4">
              <Field label="标题公式" value={bd.data.titleFormula} />
              <Field label="开头钩子" value={bd.data.hook} />
              <div>
                <p className="mb-1.5 text-sm font-medium text-text">正文骨架</p>
                <ol className="space-y-1.5">
                  {bd.data.skeleton.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-text-mut">
                      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-sm bg-bg text-xs tabular text-text">
                        {i + 1}
                      </span>
                      {s}
                    </li>
                  ))}
                </ol>
              </div>
              <Field label="标签策略" value={bd.data.tagStrategy} />
            </div>
          ) : null}
        </div>
      </Card>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-bg p-3">
      <p className="text-sm font-medium text-text">{label}</p>
      <p className="mt-1 text-sm leading-relaxed text-text-mut">{value}</p>
    </div>
  );
}

export function Insights() {
  const [tab, setTab] = useState<Tab>("keywords");
  return (
    <div>
      <PageHeader title="分析" description="选题热词、爆款榜单与内容拆解" />
      <div className="mb-5 inline-flex rounded-md border border-border bg-surface p-1">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={cn(
              "flex items-center gap-1.5 rounded-sm px-4 py-1.5 text-sm font-medium transition-colors",
              tab === id ? "bg-bg text-text" : "text-text-mut hover:text-text",
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {tab === "keywords" && <Keywords />}
      {tab === "ranking" && <Ranking />}
      {tab === "breakdown" && <BreakdownPanel />}
    </div>
  );
}
