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
import EntityGraphPage from "./components/visualization/EntityGraphPage";
import KnowledgeGraphPage from "./components/visualization/KnowledgeGraphPage";
import AdminDashboard from "./components/admin/AdminDashboard";

type Tab = "chat" | "graph" | "knowledge" | "admin";

function ResizablePanel({ children }: { children: React.ReactNode }) {
  const [width, setWidth] = useState(360);
  const dragging = useRef(false);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    dragging.current = true;
    const startX = e.clientX;
    const startW = width;
    const onMove = (ev: MouseEvent) => {
      if (!dragging.current) return;
      const diff = startX - ev.clientX;
      setWidth(Math.max(280, Math.min(700, startW + diff)));
    };
    const onUp = () => {
      dragging.current = false;
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }, [width]);

  return (
    <div className="relative flex border-l overflow-hidden" style={{ width, minWidth: 280 }}>
      <div
        onMouseDown={onMouseDown}
        className="absolute left-0 top-0 bottom-0 w-1.5 cursor-col-resize hover:bg-orange-300 z-10"
      />
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}

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
  const [showProcess, setShowProcess] = useState(false);

  // Graph state from chat (passed to EntityGraphPage / KnowledgeGraphPage)
  const [chatGraphData, setChatGraphData] = useState<{ data: GraphData; label: string } | null>(null);
  const [chatLexicalGraphData, setChatLexicalGraphData] = useState<{ data: GraphData; label: string } | null>(null);

  // Refs for streaming message assembly
  const streamingMsgRef = useRef<string>("");
  const streamingChartRef = useRef<ChartData | undefined>(undefined);
  const streamingRawRef = useRef<unknown>(undefined);
  const streamingGraphRef = useRef<GraphData | undefined>(undefined);
  const streamingLexicalGraphRef = useRef<GraphData | undefined>(undefined);
  // Ref to avoid stale closure in handleEvent
  const currentProcessRef = useRef<Partial<AgentProcess>>({});

  // Keep ref in sync with state
  useEffect(() => {
    currentProcessRef.current = currentProcess;
  }, [currentProcess]);

  // Load initial data
  useEffect(() => {
    api.getConversations().then(setConversations);
    api.getExamples().then(setExamples);
  }, []);

  // WebSocket event handler - NO dependency on currentProcess (uses ref)
  const handleEvent = useCallback((event: AgentEvent) => {
    switch (event.type) {
      case "intent_detected": {
        const d = event.data as unknown as IntentDetectedData;
        setCurrentProcess((prev) => ({
          ...prev,
          intent_detection: { ...d, intent: d.intent, confidence: d.confidence },
        }));
        // Auto-show Agent Process when streaming starts
        setShowProcess(true);
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
        if (d.graph_data && d.graph_data.nodes && d.graph_data.nodes.length > 0) {
          streamingGraphRef.current = d.graph_data;
        }
        if (d.lexical_graph_data && d.lexical_graph_data.nodes && d.lexical_graph_data.nodes.length > 0) {
          streamingLexicalGraphRef.current = d.lexical_graph_data;
        }
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
        const respStep = { latency: d.resp_latency || d.total_latency, tokens_in: d.resp_tokens_in || 0, tokens_out: d.resp_tokens_out || 0, cost: d.resp_cost || 0, estimated: (d as Record<string, unknown>).resp_estimated || false };
        setCurrentProcess((prev) => ({
          ...prev,
          response_generation: respStep,
        }));
        // Use ref to get the latest process state (avoids stale closure)
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === "assistant") {
            return [
              ...prev.slice(0, -1),
              {
                ...last,
                total,
                agentProcess: { ...currentProcessRef.current, response_generation: respStep } as AgentProcess,
                chartData: streamingChartRef.current,
                rawData: streamingRawRef.current,
                graphData: streamingGraphRef.current,
                lexicalGraphData: streamingLexicalGraphRef.current,
              },
            ];
          }
          return prev;
        });
        setIsStreaming(false);
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
    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
      },
    ]);
    streamingMsgRef.current = "";
    streamingChartRef.current = undefined;
    streamingRawRef.current = undefined;
    streamingGraphRef.current = undefined;
    streamingLexicalGraphRef.current = undefined;
    setCurrentProcess({});
    currentProcessRef.current = {};
    setCurrentTotal(null);
    setIsStreaming(true);
    sendMessage(currentSessionId, message);
  };

  const handleSelectConversation = async (sessionId: string) => {
    const detail = await api.getConversation(sessionId);
    setCurrentSessionId(sessionId);
    setMessages(
      detail.turns
        .map((t) => [
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
        ])
        .flat()
    );
    setActiveTab("chat");
  };

  const handleDeleteConversation = async (sessionId: string) => {
    await api.deleteConversation(sessionId);
    setConversations((prev) => prev.filter((c) => c.session_id !== sessionId));
    if (currentSessionId === sessionId) {
      setCurrentSessionId(null);
      setMessages([]);
    }
  };

  const handleNewConversation = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setCurrentProcess({});
    currentProcessRef.current = {};
    setCurrentTotal(null);
    setChatGraphData(null);
    setChatLexicalGraphData(null);
    setActiveTab("chat");
  };

  const handleViewGraph = (graphData: GraphData, label: string) => {
    setChatGraphData({ data: graphData, label });
    setActiveTab("graph");
  };

  const handleViewLexicalGraph = (lexicalGraphData: GraphData, label: string) => {
    setChatLexicalGraphData({ data: lexicalGraphData, label });
    setActiveTab("knowledge");
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Top nav */}
      <header className="bg-orange-500 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-sm font-bold text-white">A Securities</h1>
          <nav className="flex gap-1">
            {(["chat", "graph", "knowledge", "admin"] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab);
                  if (tab === "chat") setSidebarOpen(true);
                }}
                className={`px-3 py-1 text-sm rounded ${
                  activeTab === tab
                    ? "bg-white text-orange-600 font-semibold"
                    : "text-orange-100 hover:bg-orange-400"
                }`}
              >
                {tab === "chat" ? "Chat" : tab === "graph" ? "Entity Graph" : tab === "knowledge" ? "Lexical Graph" : "Admin"}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-2 text-xs text-orange-100">
          <span
            className={`w-2 h-2 rounded-full ${connected ? "bg-green-300" : "bg-red-300"}`}
          />
          {connected ? "연결됨" : "연결 끊김"}
        </div>
      </header>

      {/* Main area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - only visible on chat tab */}
        {activeTab === "chat" && (
          <Sidebar
            open={sidebarOpen}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            conversations={conversations}
            currentSessionId={currentSessionId}
            examples={examples}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
            onSelectExample={handleSend}
            onDeleteConversation={handleDeleteConversation}
          />
        )}

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 min-w-0 overflow-hidden">
            {activeTab === "chat" && (
              <ChatPanel
                messages={messages}
                isStreaming={isStreaming}
                onSend={handleSend}
                examples={examples}
                currentProcess={currentProcess}
                currentTotal={currentTotal}
                showProcess={showProcess}
                onToggleProcess={() => setShowProcess(!showProcess)}
                onViewGraph={handleViewGraph}
                onViewLexicalGraph={handleViewLexicalGraph}
              />
            )}

            {activeTab === "graph" && (
              <EntityGraphPage chatGraphData={chatGraphData} />
            )}

            {activeTab === "knowledge" && (
              <KnowledgeGraphPage chatLexicalGraphData={chatLexicalGraphData} />
            )}

            {activeTab === "admin" && <AdminDashboard />}
          </div>

          {/* Right Panel - Agent Process (resizable) */}
          {activeTab === "chat" && showProcess && (
            <ResizablePanel>
              <AgentProcessPanel
                process={currentProcess}
                total={currentTotal}
                isStreaming={isStreaming}
              />
            </ResizablePanel>
          )}
        </div>
      </div>
    </div>
  );
}
