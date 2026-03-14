import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import type { ConversationSummary, TokenUsageStats } from "../../types";
import { useApi } from "../../hooks/useApi";

export default function AdminDashboard() {
  const api = useApi();
  const [stats, setStats] = useState<TokenUsageStats | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [period, setPeriod] = useState<"daily" | "weekly" | "monthly">("daily");
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    api.getTokenUsage(period).then(setStats);
    api.getAdminConversations().then(setConversations);
  }, [period]);

  const handleDelete = async (sessionId: string) => {
    if (!confirm("이 대화를 삭제하시겠습니까?")) return;
    setDeleting(sessionId);
    try {
      await api.deleteConversation(sessionId);
      setConversations((prev) =>
        prev.filter((c) => c.session_id !== sessionId)
      );
    } finally {
      setDeleting(null);
    }
  };

  const chartOption = stats
    ? {
        tooltip: { trigger: "axis" },
        legend: { data: ["입력 토큰", "출력 토큰", "비용 ($)"] },
        xAxis: {
          type: "category",
          data: stats.data.map((d) => d.period_key),
        },
        yAxis: [
          { type: "value", name: "Tokens" },
          { type: "value", name: "Cost ($)", position: "right" },
        ],
        series: [
          {
            name: "입력 토큰",
            type: "line",
            data: stats.data.map((d) => d.tokens_in),
            itemStyle: { color: "#3B82F6" },
          },
          {
            name: "출력 토큰",
            type: "line",
            data: stats.data.map((d) => d.tokens_out),
            itemStyle: { color: "#F59E0B" },
          },
          {
            name: "비용 ($)",
            type: "line",
            yAxisIndex: 1,
            data: stats.data.map((d) => d.cost),
            itemStyle: { color: "#10B981" },
          },
        ],
        grid: { left: 60, right: 60, bottom: 40, top: 60 },
      }
    : null;

  return (
    <div className="p-6 overflow-y-auto h-full">
      {/* Token Usage */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">
            토큰 사용량
          </h2>
          <select
            value={period}
            onChange={(e) =>
              setPeriod(e.target.value as "daily" | "weekly" | "monthly")
            }
            className="border rounded px-2 py-1 text-sm"
          >
            <option value="daily">일별</option>
            <option value="weekly">주별</option>
            <option value="monthly">월별</option>
          </select>
        </div>

        {chartOption && (
          <ReactECharts option={chartOption} style={{ height: 300 }} />
        )}

        {stats && (
          <div className="grid grid-cols-4 gap-3 mt-4">
            <Card
              label="입력 토큰"
              value={stats.totals.tokens_in.toLocaleString()}
            />
            <Card
              label="출력 토큰"
              value={stats.totals.tokens_out.toLocaleString()}
            />
            <Card label="총 비용" value={`$${stats.totals.cost.toFixed(6)}`} />
            <Card
              label="요청 수"
              value={stats.totals.request_count.toLocaleString()}
            />
          </div>
        )}
      </div>

      {/* Conversation Management */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          대화 이력 관리
        </h2>
        <table className="w-full text-sm border">
          <thead>
            <tr className="bg-gray-50">
              <th className="text-left px-3 py-2 border-b">제목</th>
              <th className="text-center px-3 py-2 border-b w-16">턴수</th>
              <th className="text-center px-3 py-2 border-b w-24">Intent</th>
              <th className="text-center px-3 py-2 border-b w-32">시간</th>
              <th className="text-center px-3 py-2 border-b w-16">삭제</th>
            </tr>
          </thead>
          <tbody>
            {conversations.map((conv) => (
              <tr key={conv.session_id} className="hover:bg-gray-50">
                <td className="px-3 py-2 border-b truncate max-w-[200px]">
                  {conv.title || "제목 없음"}
                </td>
                <td className="px-3 py-2 border-b text-center">
                  {conv.turn_count}
                </td>
                <td className="px-3 py-2 border-b text-center">
                  <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">
                    {conv.last_intent}
                  </span>
                </td>
                <td className="px-3 py-2 border-b text-center text-gray-500 text-xs">
                  {conv.updated_at}
                </td>
                <td className="px-3 py-2 border-b text-center">
                  <button
                    onClick={() => handleDelete(conv.session_id)}
                    disabled={deleting === conv.session_id}
                    className="text-red-500 hover:text-red-700 text-xs disabled:opacity-50"
                  >
                    삭제
                  </button>
                </td>
              </tr>
            ))}
            {conversations.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-8 text-center text-gray-400">
                  대화 이력이 없습니다
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white border rounded-lg p-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-semibold text-gray-800">{value}</p>
    </div>
  );
}
