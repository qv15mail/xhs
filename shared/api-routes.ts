// 前后端共享的 API 路径常量，避免前后端不一致（架构契约要求）
export const API_BASE = "/api";

export const ApiRoutes = {
  collectTasks: `${API_BASE}/collect/tasks`,
  collectTask: (id: string) => `${API_BASE}/collect/tasks/${id}`,
  collectTaskEvents: (id: string) => `${API_BASE}/collect/tasks/${id}/events`,
  authLoginQrcode: `${API_BASE}/auth/login/qrcode`,
  authLogout: `${API_BASE}/auth/logout`,
  authStatus: `${API_BASE}/auth/status`,
  notes: `${API_BASE}/notes`,
  note: (id: string) => `${API_BASE}/notes/${id}`,
  analysis: (taskId: string) => `${API_BASE}/analysis/${taskId}`,
  analysisBreakdown: `${API_BASE}/analysis/breakdown`,
  compose: `${API_BASE}/compose`,
  settings: `${API_BASE}/settings`,
} as const;
