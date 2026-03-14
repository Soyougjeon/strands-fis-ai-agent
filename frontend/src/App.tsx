import { useCallback, useEffect, useRef, useState } from "react";
import type {
  AgentEvent,
  AgentProcess,
  ChatMessage,
  ConversationSummary,
  ExampleQueries,
  GraphData,
  TotalMetrics,
  IntentDetectedData,
  ToolSelectedData,
  QueryGeneratedData,
  QueryExecutedData,
  ResponseCompleteData,
  ChartData,
} from "./types";
import { useWebSocket } from "./hooks/useWebSocket";
import { useApi } from "./hooks/useApi";
import Sidebar from "./components/sidebar/Sidebar";
import ChatPanel from "./components/chat/ChatPanel";
import AgentProcessPanel from "./components/chat/AgentProcessPanel";
import DetailTabs from "./components/chat/DetailTabs";
import GraphNetworkPage from "./components/visualization/GraphNetworkPage";
import AdminDashboard from "./components/admin/AdminDashboard";

type Tab = "chat" | "graph" | "admin";

export default function App() {
  const api = useApi();

  // App state
  const [activeTab, setActiveTab] = useState<Tab>("chat");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [examples, setExamples] = useState<ExampleQueries | null>(null);

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentProcess, setCurrentProcess] = useState<Partial<AgentProcess>>({});
  const [currentTotal, setCurrentTotal] = useState<TotalMetrics | null>(null);

  // Graph state
  const [graphDataMap] = useState<Record<string, GraphData | null>>({
    ETF: null,
    Bond: null,
    Fund: null,
  });

  // Refs for streaming message assembly
  const streamingMsgRef = useRef<string>("");
  const streamingChartRef = useRef<ChartData | undefined>(undefined);
  const streamingRawRef = useRef<unknown>(undefined);
  const streamingGraphRef = useRef<GraphData | undefined>(undefined);

  // Load initial data
  useEffect(() => {
    api.getConversations().then(setConversations);
    api.getExamples().then(setExamples);
  }, []);

  // WebSocket event handler
  const handleEvent = useCallback((event: AgentEvent) => {
    switch (event.type) {
      case "intent_detected": {
        const d = event.data as unknown as IntentDetectedData;
        setCurrentProcess((prev) => ({
          ...prev,
          intent_detection: { ...d, intent: d.intent, confidence: d.confidence },
        }));
        break;
      }
      case "tool_selected": {
        const d = event.data as unknown as ToolSelectedData;
        setCurrentProcess((prev) => ({
          ...prev,
          tool_selection: { ...d, tool: d.tool, rationale: d.rationale },
        }));
        break;
      }
      case "query_generated": {
        const d = event.data as unknown as QueryGeneratedData;
        setCurrentProcess((prev) => ({
          ...prev,
          query_generation: d,
        }));
        break;
      }
      case "query_executed": {
        const d = event.data as unknown as QueryExecutedData;
        setCurrentProcess((prev) => ({
          ...prev,
          query_execution: d,
        }));
        if (d.chart_data) streamingChartRef.current = d.chart_data;
        if (d.raw_data) streamingRawRef.current = d.raw_data;
        if (d.graph_data) streamingGraphRef.current = d.graph_data;
        break;
      }
      case "text_chunk": {
        const text = (event.data as { text: string }).text;
        streamingMsgRef.current += text;
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === "assistant" && !last.total) {
            return [
              ...prev.slice(0, -1),
              { ...last, content: streamingMsgRef.current },
            ];
          }
          return [
            ...prev,
            {
              id: `msg-${Date.now()}`,
              role: "assistant",
              content: streamingMsgRef.current,
              timestamp: new Date().toISOString(),
            },
          ];
        });
        break;
      }
      case "response_complete": {
        const d = event.data as unknown as ResponseCompleteData;
        const total: TotalMetrics = {
          latency: d.total_latency,
          tokens_in: d.total_tokens_in,
          tokens_out: d.total_tokens_out,
          cost: d.total_cost,
        };
        setCurrentTotal(total);
        setCurrentProcess((prev) => ({
          ...prev,
          response_generation: {
            latency: d.total_latency,
            tokens_in: 0,
            tokens_out: 0,
            cost: 0,
          },
        }));
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === "assistant") {
            return [
              ...prev.slice(0, -1),
              {
                ...last,
                total,
                chartData: streamingChartRef.current,
                rawData: streamingRawRef.current,
                graphData: streamingGraphRef.current,
              },
            ];
          }
          return prev;
        });
        setIsStreaming(false);
        // Refresh conversation list
        api.getConversations().then(setConversations);
        break;
      }
      case "session_info": {
        const sid = (event.data as { session_id: string }).session_id;
        setCurrentSessionId(sid);
        break;
      }
      case "error": {
        const msg = (event.data as { message: string }).message;
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: "assistant",
            content: `오류: ${msg}`,
            timestamp: new Date().toISOString(),
          },
        ]);
        setIsStreaming(false);
        break;
      }
    }
  }, []);

  const { connected, sendMessage } = useWebSocket({ onEvent: handleEvent });

  const handleSend = (message: string) => {
    // Add user message
    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
      },
    ]);
    // Reset streaming state
    streamingMsgRef.current = "";
    streamingChartRef.current = undefined;
    streamingRawRef.current = undefined;
    streamingGraphRef.current = undefined;
    setCurrentProcess({});
    setCurrentTotal(null);
    setIsStreaming(true);
    sendMessage(currentSessionId, message);
  };

  const handleSelectConversation = async (sessionId: string) => {
    const detail = await api.getConversation(sessionId);
    setCurrentSessionId(sessionId);
    setMessages(
      detail.turns.map((t) => [
        {
          id: `q-${t.turn_id}`,
          role: "user" as const,
          content: t.question,
          timestamp: t.timestamp,
        },
        {
          id: `a-${t.turn_id}`,
          role: "assistant" as const,
          content: t.response,
          agentProcess: t.agent_process,
          total: t.total,
          timestamp: t.timestamp,
        },
      ]).flat()
    );
    setActiveTab("chat");
  };

  const handleNewConversation = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setCurrentProcess({});
    setCurrentTotal(null);
    setActiveTab("chat");
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Top nav */}
      <header className="bg-white border-b px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-sm font-bold text-gray-800">Strands FIS</h1>
          <nav className="flex gap-1">
            {(["chat", "graph", "admin"] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1 text-sm rounded ${
                  activeTab === tab
                    ? "bg-blue-500 text-white"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                {tab === "chat" ? "Chat" : tab === "graph" ? "Graph Network" : "Admin"}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className={`w-2 h-2 rounded-full ${connected ? "bg-green-400" : "bg-red-400"}`} />
          {connected ? "연결됨" : "연결 끊김"}
        </div>
      </header>

      {/* Main area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          open={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          conversations={conversations}
          currentSessionId={currentSessionId}
          examples={examples}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onSelectExample={handleSend}
        />

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === "chat" && (
            <div className="flex h-full">
              {/* Chat area ~55% */}
              <div className="flex-[55] min-w-0 border-r">
                <ChatPanel
                  messages={messages}
                  isStreaming={isStreaming}
                  onSend={handleSend}
                />
              </div>
              {/* Agent Process ~45% */}
              <div className="flex-[45] min-w-0 flex flex-col">
                <div className="flex-1 overflow-hidden">
                  <AgentProcessPanel
                    process={currentProcess}
                    total={currentTotal}
                    isStreaming={isStreaming}
                  />
                </div>
                <DetailTabs process={currentProcess} />
              </div>
            </div>
          )}

          {activeTab === "graph" && (
            <GraphNetworkPage graphDataMap={graphDataMap} />
          )}

          {activeTab === "admin" && <AdminDashboard />}
        </div>
      </div>
    </div>
  );
}
