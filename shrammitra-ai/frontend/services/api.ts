/**
 * API client for the ShramMitra backend.
 * Reads NEXT_PUBLIC_API_URL at build time.
 */
import axios from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const client = axios.create({ baseURL: BASE_URL });

// Attach JWT token from localStorage on every request
client.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("shrammitra_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ─── Types ────────────────────────────────────────────────────────────────────
export interface Conversation {
  id: string;
  language: string;
  state: string;
  message_count: number;
  created_at: string;
  is_voice: boolean;
}

export interface Source {
  id: string;
  url: string;
  title: string;
  source_type: string;
  status: string;
  chunk_count: number | null;
  last_synced_at: string | null;
}

export interface Analytics {
  total_conversations: number;
  active_conversations: number;
  total_messages: number;
  voice_count: number;
  avg_confidence: number;
  avg_latency_ms: number;
  avg_rating: number | null;
  language_breakdown: Record<string, number>;
}

export interface ChatMessage {
  message: string;
  language?: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  language: string;
  session_id: string;
  confidence: number;
  latency_ms: number;
  sources: { title: string; url: string; excerpt: string; confidence: number }[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// ─── API methods ──────────────────────────────────────────────────────────────
export const api = {
  async login(apiKey: string): Promise<string> {
    const res = await client.post<{ access_token: string }>("/admin/login", {
      api_key: apiKey,
    });
    return res.data.access_token;
  },

  async getConversations(params: {
    skip?: number;
    limit?: number;
    language?: string;
  }): Promise<PaginatedResponse<Conversation>> {
    const res = await client.get("/admin/conversations", { params });
    return res.data;
  },

  async getSources(params: {
    skip?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Source>> {
    const res = await client.get("/admin/sources", { params });
    return res.data;
  },

  async getAnalytics(): Promise<Analytics> {
    const res = await client.get("/admin/analytics");
    return res.data;
  },

  async triggerReindex(): Promise<void> {
    await client.post("/admin/reindex");
  },

  async sendMessage(payload: ChatMessage): Promise<ChatResponse> {
    const res = await client.post<ChatResponse>("/chat/message", payload);
    return res.data;
  },
};
