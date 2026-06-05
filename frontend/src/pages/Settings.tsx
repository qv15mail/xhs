import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plug, Radar, Database, Save, CheckCircle2, AlertTriangle } from "lucide-react";
import { api } from "@/api/client";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardHeader, Input, Label, Select, Switch } from "@/components/ui/primitives";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/states";
import { useAppStore } from "@/store/app";
import type { Settings as SettingsType } from "@/lib/types";

export function Settings() {
  const qc = useQueryClient();
  const setLoggedIn = useAppStore((s) => s.setLoggedIn);
  const q = useQuery({ queryKey: ["settings"], queryFn: api.getSettings });
  const [form, setForm] = useState<SettingsType | null>(null);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);

  useEffect(() => {
    if (q.data && !form) setForm(q.data);
  }, [q.data, form]);

  const save = useMutation({
    mutationFn: (s: SettingsType) => api.saveSettings(s),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings"] }),
  });
  const test = useMutation({ mutationFn: () => api.testLLM(), onSuccess: setTestResult });

  if (q.isLoading || !form) {
    return (
      <div>
        <PageHeader title="设置" />
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      </div>
    );
  }

  const upLlm = <K extends keyof SettingsType["llm"]>(k: K, v: SettingsType["llm"][K]) =>
    setForm({ ...form, llm: { ...form.llm, [k]: v } });
  const upCollect = <K extends keyof SettingsType["collect"]>(k: K, v: SettingsType["collect"][K]) =>
    setForm({ ...form, collect: { ...form.collect, [k]: v } });

  return (
    <div>
      <PageHeader
        title="设置"
        description="LLM、采集与账号数据配置"
        action={
          <Button loading={save.isPending} onClick={() => save.mutate(form)}>
            <Save className="h-4 w-4" /> 保存设置
          </Button>
        }
      />

      <div className="space-y-6">
        <Card>
          <CardHeader title="LLM 配置" description="OpenAI 兼容接口，可切换厂商或本地模型" />
          <div className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <Label htmlFor="baseUrl">Base URL</Label>
              <Input
                id="baseUrl"
                value={form.llm.baseUrl}
                onChange={(e) => upLlm("baseUrl", e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="apiKey">API Key</Label>
              <Input
                id="apiKey"
                type="password"
                placeholder="sk-..."
                value={form.llm.apiKey}
                onChange={(e) => upLlm("apiKey", e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="model">模型</Label>
              <Input id="model" value={form.llm.model} onChange={(e) => upLlm("model", e.target.value)} />
            </div>
            <div>
              <Label htmlFor="temp">温度：{form.llm.temperature.toFixed(1)}</Label>
              <input
                id="temp"
                type="range"
                min={0}
                max={1}
                step={0.1}
                value={form.llm.temperature}
                onChange={(e) => upLlm("temperature", Number(e.target.value))}
                className="h-10 w-full accent-[var(--accent)]"
              />
            </div>
            <div className="flex items-center gap-3 sm:col-span-2">
              <Button variant="secondary" size="sm" loading={test.isPending} onClick={() => test.mutate()}>
                <Plug className="h-4 w-4" /> 测试连接
              </Button>
              {testResult && (
                <span
                  className={`flex items-center gap-1 text-sm ${
                    testResult.ok ? "text-success" : "text-danger"
                  }`}
                >
                  {testResult.ok ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    <AlertTriangle className="h-4 w-4" />
                  )}
                  {testResult.message}
                </span>
              )}
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="采集配置" description="默认采集参数与限速策略" />
          <div className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2">
            <div>
              <Label htmlFor="count">默认采集数量：{form.collect.defaultCount}</Label>
              <input
                id="count"
                type="range"
                min={10}
                max={100}
                step={10}
                value={form.collect.defaultCount}
                onChange={(e) => upCollect("defaultCount", Number(e.target.value))}
                className="h-10 w-full accent-[var(--accent)]"
              />
            </div>
            <div>
              <Label htmlFor="rate">限速档位</Label>
              <Select
                id="rate"
                value={form.collect.rateLevel}
                onChange={(e) => upCollect("rateLevel", e.target.value as "conservative" | "standard")}
              >
                <option value="conservative">保守（推荐，更安全）</option>
                <option value="standard">标准</option>
              </Select>
            </div>
            <div>
              <Label htmlFor="conc">并发数：{form.collect.concurrency}</Label>
              <input
                id="conc"
                type="range"
                min={1}
                max={3}
                step={1}
                value={form.collect.concurrency}
                onChange={(e) => upCollect("concurrency", Number(e.target.value))}
                className="h-10 w-full accent-[var(--accent)]"
              />
            </div>
            <div className="flex items-center justify-between rounded-md border border-border px-4 py-3">
              <span className="text-sm font-medium text-text">默认采集评论</span>
              <Switch
                checked={form.collect.includeComments}
                onChange={(v) => upCollect("includeComments", v)}
                label="默认采集评论"
              />
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="账号与数据" description="登录态与本地数据管理" />
          <div className="flex flex-wrap gap-3 p-5">
            <Button variant="secondary" size="sm" onClick={() => setLoggedIn(false)}>
              <Radar className="h-4 w-4" /> 清除登录态
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => {
                localStorage.removeItem("redscope.settings");
                qc.clear();
                q.refetch();
              }}
            >
              <Database className="h-4 w-4" /> 清空本地数据
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
