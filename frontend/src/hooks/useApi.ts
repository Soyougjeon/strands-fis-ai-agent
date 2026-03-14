import { useCallback, useState } from "react";
import type {
  ConversationDetail,
  ConversationSummary,
  ExampleQueries,
  TokenUsageStats,
} from "../types";

const BASE = "/api";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export function useApi() {
  const [loading, setLoading] = useState(false);

  const getConversations = useCallback(async (): Promise<
    ConversationSummary[]
  > => {
    const data = await fetchJson<{ conversations: ConversationSummary[] }>(
      `${BASE}/conversations`
    );
    return data.conversations;
  }, []);

  const getConversation = useCallback(
    async (sessionId: string): Promise<ConversationDetail> => {
      return fetchJson<ConversationDetail>(
        `${BASE}/conversations/${sessionId}`
      );
    },
    []
  );

  const deleteConversation = useCallback(
    async (sessionId: string): Promise<void> => {
      await fetchJson(`${BASE}/conversations/${sessionId}`, {
        method: "DELETE",
      });
    },
    []
  );

  const getExamples = useCallback(async (): Promise<ExampleQueries> => {
    return fetchJson<ExampleQueries>(`${BASE}/examples`);
  }, []);

  const getTokenUsage = useCallback(
    async (
      period: string = "daily",
      startDate?: string,
      endDate?: string
    ): Promise<TokenUsageStats> => {
      const params = new URLSearchParams({ period });
      if (startDate) params.set("start_date", startDate);
      if (endDate) params.set("end_date", endDate);
      return fetchJson<TokenUsageStats>(
        `${BASE}/admin/token-usage?${params}`
      );
    },
    []
  );

  const getAdminConversations = useCallback(async (): Promise<
    ConversationSummary[]
  > => {
    const data = await fetchJson<{
      conversations: ConversationSummary[];
      total_count: number;
    }>(`${BASE}/admin/conversations`);
    return data.conversations;
  }, []);

  return {
    loading,
    setLoading,
    getConversations,
    getConversation,
    deleteConversation,
    getExamples,
    getTokenUsage,
    getAdminConversations,
  };
}
