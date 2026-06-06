export type TaskStatus = "pending" | "running" | "success" | "failed";

export interface CollectTask {
  id: string;
  topic: string;
  total: number;
  progress: number;
  status: TaskStatus;
  sort: "comprehensive" | "latest" | "hottest";
  includeComments: boolean;
  error?: string;
  createdAt: string;
}

export interface Note {
  id: string;
  taskId: string;
  title: string;
  content: string;
  author: string;
  likes: number;
  collects: number;
  comments: number;
  shares: number;
  publishTime: string;
  url: string;
  cover: string;
  tags: string[];
  createdAt: string;
}

export interface Keyword {
  word: string;
  count: number;
}

export interface RankingItem {
  noteId: string;
  title: string;
  author: string;
  score: number;
  likes: number;
  reasons: string[];
}

export interface Breakdown {
  noteId: string;
  titleFormula: string;
  hook: string;
  skeleton: string[];
  tagStrategy: string;
}

export interface ComposeResult {
  titles: string[];
  body: string;
  hashtags: string[];
  imageSuggestions: string[];
}

export interface LLMSettings {
  baseUrl: string;
  apiKey: string;
  model: string;
  temperature: number;
}

export interface CollectSettings {
  defaultCount: number;
  rateLevel: "conservative" | "standard";
  concurrency: number;
  includeComments: boolean;
}

export interface Settings {
  llm: LLMSettings;
  collect: CollectSettings;
}

export interface DashboardStats {
  totalNotes: number;
  totalTasks: number;
  avgEngagement: number;
  lastTaskStatus: TaskStatus | "none";
  trend: { date: string; count: number }[];
}
