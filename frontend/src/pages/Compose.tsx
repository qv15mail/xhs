import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Sparkles, Copy, Download, RefreshCw, Check } from "lucide-react";
import { api } from "@/api/client";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardHeader, Input, Label, Select, Textarea, Badge } from "@/components/ui/primitives";
import { Button } from "@/components/ui/Button";
import { Skeleton, EmptyState } from "@/components/ui/states";
import type { ComposeResult } from "@/lib/types";

function useCopy() {
  const [copied, setCopied] = useState<string | null>(null);
  const copy = (key: string, text: string) => {
    navigator.clipboard?.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 1500);
  };
  return { copied, copy };
}

export function Compose() {
  const notes = useQuery({ queryKey: ["notes"], queryFn: () => api.listNotes() });
  const [ref, setRef] = useState("");
  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState("种草");
  const [length, setLength] = useState("中等");
  const [body, setBody] = useState("");
  const { copied, copy } = useCopy();

  const gen = useMutation({
    mutationFn: () =>
      api.compose({ topic: topic || "该主题", refNoteId: ref || undefined, style, length }),
    onSuccess: (r: ComposeResult) => setBody(r.body),
  });

  const exportMd = () => {
    if (!gen.data) return;
    const md = `# ${gen.data.titles[0]}\n\n${body}\n\n${gen.data.hashtags
      .map((t) => `#${t}`)
      .join(" ")}\n`;
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `redscope-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <PageHeader title="仿写" description="基于参考与拆解，生成同主题原创笔记" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader title="创作设置" />
          <div className="space-y-4 p-5">
            <div>
              <Label htmlFor="ref">参考笔记（可选）</Label>
              <Select id="ref" value={ref} onChange={(e) => setRef(e.target.value)}>
                <option value="">不使用参考</option>
                {notes.data?.slice(0, 12).map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.title.slice(0, 24)}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label htmlFor="topic">新主题 / 卖点</Label>
              <Input
                id="topic"
                placeholder="例如：平价学生党护肤"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="style">风格</Label>
                <Select id="style" value={style} onChange={(e) => setStyle(e.target.value)}>
                  <option>种草</option>
                  <option>测评</option>
                  <option>教程</option>
                  <option>情绪共鸣</option>
                </Select>
              </div>
              <div>
                <Label htmlFor="length">长度</Label>
                <Select id="length" value={length} onChange={(e) => setLength(e.target.value)}>
                  <option>简短</option>
                  <option>中等</option>
                  <option>详细</option>
                </Select>
              </div>
            </div>
            <Button
              className="w-full"
              loading={gen.isPending}
              disabled={!topic.trim()}
              onClick={() => gen.mutate()}
            >
              <Sparkles className="h-4 w-4" />
              生成仿写
            </Button>
          </div>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader
            title="生成结果"
            action={
              gen.data && (
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => gen.mutate()}>
                    <RefreshCw className="h-4 w-4" /> 重写
                  </Button>
                  <Button variant="secondary" size="sm" onClick={exportMd}>
                    <Download className="h-4 w-4" /> 导出
                  </Button>
                </div>
              )
            }
          />
          <div className="p-5">
            {gen.isPending ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-10" />
                ))}
              </div>
            ) : !gen.data ? (
              <EmptyState
                title="填写主题后点击生成"
                description="将输出标题矩阵、正文、推荐标签与配图建议"
              />
            ) : (
              <div className="space-y-5">
                <div>
                  <p className="mb-2 text-sm font-medium text-text">标题矩阵</p>
                  <div className="space-y-2">
                    {gen.data.titles.map((t, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between gap-2 rounded-md border border-border px-3 py-2"
                      >
                        <span className="text-sm text-text">{t}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copy(`t${i}`, t)}
                          aria-label="复制标题"
                        >
                          {copied === `t${i}` ? (
                            <Check className="h-4 w-4 text-success" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-medium text-text">正文（可编辑）</p>
                    <Button variant="ghost" size="sm" onClick={() => copy("body", body)}>
                      {copied === "body" ? (
                        <Check className="h-4 w-4 text-success" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                      复制
                    </Button>
                  </div>
                  <Textarea rows={8} value={body} onChange={(e) => setBody(e.target.value)} />
                </div>

                <div>
                  <p className="mb-2 text-sm font-medium text-text">推荐话题标签</p>
                  <div className="flex flex-wrap gap-1.5">
                    {gen.data.hashtags.map((t) => (
                      <Badge key={t} tone="accent">
                        #{t}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="mb-2 text-sm font-medium text-text">配图建议</p>
                  <ul className="space-y-1.5">
                    {gen.data.imageSuggestions.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-text-mut">
                        <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-sm bg-bg text-xs tabular text-text">
                          {i + 1}
                        </span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
