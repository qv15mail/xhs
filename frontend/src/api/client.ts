import { ApiRoutes } from "@shared/api-routes";
import type {
  Breakdown,
  CollectTask,
  ComposeResult,
  DashboardStats,
  Keyword,
  Note,
  RankingItem,
  Settings,
} from "@/lib/types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    let detail = `请求失败 (${resp.status})`;
    try {
      const data = await resp.json();
      if (data?.detail) detail = data.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return resp.json() as Promise<T>;
}

export const api = {
  getStats: () => request<DashboardStats>("/api/stats"),

  listTasks: () => request<CollectTask[]>(ApiRoutes.collectTasks),

  createTask: (input: Pick<CollectTask, "topic" | "total" | "sort" | "includeComments">) =>
    request<CollectTask>(ApiRoutes.collectTasks, {
      method: "POST",
      body: JSON.stringify(input),
    }),

  getTask: (id: string) => request<CollectTask>(ApiRoutes.collectTask(id)),

  listNotes: (taskId?: string) =>
    request<Note[]>(taskId ? `${ApiRoutes.notes}?taskId=${encodeURIComponent(taskId)}` : ApiRoutes.notes),

  getNote: (id: string) => request<Note>(ApiRoutes.note(id)),

  analysis: (taskId = "all") =>
    request<{ keywords: Keyword[]; ranking: RankingItem[] }>(ApiRoutes.analysis(taskId)),

  keywords: async (): Promise<Keyword[]> => (await api.analysis()).keywords,

  ranking: async (): Promise<RankingItem[]> => (await api.analysis()).ranking,

  breakdown: (noteId: string) =>
    request<Breakdown>(ApiRoutes.analysisBreakdown, {
      method: "POST",
      body: JSON.stringify({ noteId }),
    }),

  compose: (input: { topic: string; refNoteId?: string; style?: string; length?: string }) =>
    request<ComposeResult>(ApiRoutes.compose, {
      method: "POST",
      body: JSON.stringify(input),
    }),

  getSettings: () => request<Settings>(ApiRoutes.settings),

  saveSettings: (s: Settings) =>
    request<Settings>(ApiRoutes.settings, { method: "PUT", body: JSON.stringify(s) }),

  testLLM: () =>
    request<{ ok: boolean; message: string }>(`${ApiRoutes.settings}/test-llm`, { method: "POST" }),

  loginQrcode: () =>
    request<{ qrcode: string; note: string; loggedIn: boolean }>(ApiRoutes.authLoginQrcode, {
      method: "POST",
    }),

  logout: () =>
    request<{ loggedIn: boolean }>(ApiRoutes.authLogout, {
      method: "POST",
    }),

  authStatus: () =>
    request<{ loggedIn: boolean; status: string; error: string | null }>(ApiRoutes.authStatus),
};
