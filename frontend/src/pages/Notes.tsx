import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Heart, Star, MessageCircle, ExternalLink, Search, PenLine, BarChart3 } from "lucide-react";
import { api } from "@/api/client";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, Input, Select, Badge } from "@/components/ui/primitives";
import { Button } from "@/components/ui/Button";
import { Drawer } from "@/components/ui/overlay";
import { Skeleton, EmptyState, ErrorState } from "@/components/ui/states";
import { formatNumber, formatDate } from "@/lib/utils";
import type { Note } from "@/lib/types";

type SortKey = "collect" | "likes" | "time";

function NoteCard({ note, onClick }: { note: Note; onClick: () => void }) {
  return (
    <button onClick={onClick} className="group text-left">
      <Card className="h-full overflow-hidden transition-shadow hover:shadow-cardHover">
        <div className="flex h-32 items-end p-3" style={{ background: note.cover }}>
          <span className="rounded-sm bg-black/10 px-2 py-0.5 text-xs text-text">
            {note.author}
          </span>
        </div>
        <div className="p-4">
          <p className="line-clamp-2 text-sm font-medium text-text">{note.title}</p>
          <div className="mt-3 flex items-center gap-4 text-xs text-text-mut">
            <span className="flex items-center gap-1">
              <Heart className="h-3.5 w-3.5" /> {formatNumber(note.likes)}
            </span>
            <span className="flex items-center gap-1">
              <Star className="h-3.5 w-3.5" /> {formatNumber(note.collects)}
            </span>
            <span className="flex items-center gap-1">
              <MessageCircle className="h-3.5 w-3.5" /> {formatNumber(note.comments)}
            </span>
          </div>
        </div>
      </Card>
    </button>
  );
}

export function Notes() {
  const navigate = useNavigate();
  const notes = useQuery({ queryKey: ["notes"], queryFn: () => api.listNotes() });
  const tasks = useQuery({ queryKey: ["tasks"], queryFn: api.listTasks });
  const [keyword, setKeyword] = useState("");
  const [sort, setSort] = useState<SortKey>("collect");
  const [grouped, setGrouped] = useState(false);
  const [active, setActive] = useState<Note | null>(null);

  const filtered = useMemo(() => {
    let list = notes.data ?? [];
    if (keyword.trim()) {
      const k = keyword.trim();
      list = list.filter((n) => n.title.includes(k) || n.author.includes(k));
    }
    return [...list].sort((a, b) => {
      if (sort === "likes") return b.likes - a.likes;
      if (sort === "time") return b.publishTime.localeCompare(a.publishTime);
      return b.createdAt.localeCompare(a.createdAt);
    });
  }, [notes.data, keyword, sort]);

  const groups = useMemo(() => {
    const taskMap = new Map((tasks.data ?? []).map((t) => [t.id, t]));
    const byTask = new Map<string, Note[]>();
    for (const n of filtered) {
      if (!byTask.has(n.taskId)) byTask.set(n.taskId, []);
      byTask.get(n.taskId)!.push(n);
    }
    return [...byTask.entries()]
      .map(([taskId, items]) => ({ taskId, task: taskMap.get(taskId), items }))
      .sort((a, b) => {
        const ta = a.task?.createdAt ?? a.items[0]?.createdAt ?? "";
        const tb = b.task?.createdAt ?? b.items[0]?.createdAt ?? "";
        return tb.localeCompare(ta);
      });
  }, [filtered, tasks.data]);

  return (
    <div>
      <PageHeader title="笔记库" description="已采集的笔记内容与互动数据" />

      <Card className="mb-4 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[220px] flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-mut" />
            <Input
              className="pl-9"
              placeholder="搜索标题或作者"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
          </div>
          <Select
            className="w-40"
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
          >
            <option value="collect">按采集时间</option>
            <option value="likes">按互动量</option>
            <option value="time">按发布时间</option>
          </Select>
          <Select
            className="w-40"
            value={grouped ? "task" : "flat"}
            onChange={(e) => setGrouped(e.target.value === "task")}
          >
            <option value="flat">不分组</option>
            <option value="task">按采集任务分组</option>
          </Select>
        </div>
      </Card>

      {notes.isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-56" />
          ))}
        </div>
      ) : notes.isError ? (
        <Card>
          <ErrorState onRetry={() => notes.refetch()} />
        </Card>
      ) : filtered.length === 0 ? (
        <Card>
          <EmptyState title="没有匹配的笔记" description="调整筛选条件或先去采集" />
        </Card>
      ) : grouped ? (
        <div className="space-y-6">
          {groups.map((g) => (
            <section key={g.taskId}>
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <h3 className="text-sm font-semibold text-text">
                  {g.task?.topic ?? "未知任务"}
                </h3>
                <Badge tone="accent">{g.items.length} 篇</Badge>
                {g.task && (
                  <span className="text-xs text-text-mut">
                    采集于 {formatDate(g.task.createdAt)}
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {g.items.map((n) => (
                  <NoteCard key={n.id} note={n} onClick={() => setActive(n)} />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((n) => (
            <NoteCard key={n.id} note={n} onClick={() => setActive(n)} />
          ))}
        </div>
      )}

      <Drawer open={!!active} onClose={() => setActive(null)} title="笔记详情">
        {active && (
          <div className="space-y-4">
            <div className="h-40 rounded-md" style={{ background: active.cover }} />
            <h2 className="text-base font-semibold text-text">{active.title}</h2>
            <div className="flex items-center gap-2 text-sm text-text-mut">
              <span>{active.author}</span>
              <span>·</span>
              <span>{formatDate(active.publishTime)}</span>
            </div>
            <div className="grid grid-cols-4 gap-2 text-center">
              {[
                { label: "点赞", v: active.likes },
                { label: "收藏", v: active.collects },
                { label: "评论", v: active.comments },
                { label: "分享", v: active.shares },
              ].map((s) => (
                <div key={s.label} className="rounded-md bg-bg py-2">
                  <p className="text-sm font-semibold tabular text-text">{formatNumber(s.v)}</p>
                  <p className="text-xs text-text-mut">{s.label}</p>
                </div>
              ))}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {active.tags.map((t) => (
                <Badge key={t} tone="accent">
                  #{t}
                </Badge>
              ))}
            </div>
            <p className="whitespace-pre-line text-sm leading-relaxed text-text">{active.content}</p>
            <div className="flex flex-wrap gap-2 pt-2">
              <Button size="sm" onClick={() => navigate("/compose")}>
                <PenLine className="h-4 w-4" /> 拿去仿写
              </Button>
              <Button size="sm" variant="secondary" onClick={() => navigate("/insights")}>
                <BarChart3 className="h-4 w-4" /> 去拆解
              </Button>
              <a href={active.url} target="_blank" rel="noreferrer">
                <Button size="sm" variant="ghost">
                  <ExternalLink className="h-4 w-4" /> 原文
                </Button>
              </a>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}
