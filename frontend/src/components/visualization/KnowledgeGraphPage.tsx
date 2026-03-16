import { useState, useEffect } from "react";
import { useApi } from "../../hooks/useApi";
import EntityGraph from "./EntityGraph";
import type { GraphData } from "../../types";

const TENANTS = [
  { key: "etfgrag", label: "ETF", desc: "ETF Lexical Graph" },
  { key: "bondgrag", label: "채권", desc: "Bond Lexical Graph" },
  { key: "fundgrag", label: "펀드", desc: "Fund Lexical Graph" },
] as const;

type Mode = "sources" | "schema";

const MODES: { key: Mode; label: string }[] = [
  { key: "sources", label: "소스 문서 체인" },
  { key: "schema", label: "스키마" },
];

interface Props {
  chatLexicalGraphData?: { data: GraphData; label: string } | null;
}

export default function KnowledgeGraphPage({ chatLexicalGraphData }: Props) {
  const api = useApi();
  const [activeTenant, setActiveTenant] = useState<string>(
    chatLexicalGraphData ? "__chat__" : "etfgrag"
  );
  const [mode, setMode] = useState<Mode>("sources");
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Switch to chat tab when new chat data arrives
  useEffect(() => {
    if (chatLexicalGraphData) {
      setActiveTenant("__chat__");
    }
  }, [chatLexicalGraphData]);

  const handleQuery = async (tenant?: string, queryMode?: Mode) => {
    if ((tenant || activeTenant) === "__chat__") return;
    const t = tenant || activeTenant;
    const m = queryMode || mode;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ tenant: t, mode: m });
      const data = await api.getKnowledgeGraph(params.toString());
      if (!data.nodes || data.nodes.length === 0) {
        setError("결과가 없습니다.");
        setLoading(false);
        return;
      }
      setGraphData(data);
    } catch (e) {
      setError(`조회 실패: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  };

  // Auto-query on first mount (only if no chat data)
  useEffect(() => {
    if (!chatLexicalGraphData) {
      handleQuery("etfgrag", "sources");
    }
  }, []);

  const currentData = activeTenant === "__chat__" ? chatLexicalGraphData?.data ?? null : graphData;
  const chatLabel = chatLexicalGraphData?.label
    ? chatLexicalGraphData.label.length > 20
      ? chatLexicalGraphData.label.slice(0, 20) + "..."
      : chatLexicalGraphData.label
    : "검색 결과";

  return (
    <div className="flex flex-col h-full">
      {/* Top bar */}
      <div className="flex items-center justify-between border-b bg-white px-4 py-2">
        <div className="flex items-center gap-3">
          <div className="flex gap-1">
            {TENANTS.map((t) => (
              <button
                key={t.key}
                onClick={() => { setActiveTenant(t.key); setGraphData(null); setError(null); }}
                className={`px-3 py-1 text-sm rounded ${
                  activeTenant === t.key ? "bg-purple-500 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {t.label}
              </button>
            ))}
            {chatLexicalGraphData && (
              <button
                onClick={() => setActiveTenant("__chat__")}
                className={`px-3 py-1 text-sm rounded flex items-center gap-1 ${
                  activeTenant === "__chat__"
                    ? "bg-purple-500 text-white"
                    : "bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100"
                }`}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
                {chatLabel}
              </button>
            )}
          </div>

          {activeTenant !== "__chat__" && (
            <>
              <div className="w-px h-6 bg-gray-200" />
              <div className="flex gap-1">
                {MODES.map((m) => (
                  <button
                    key={m.key}
                    onClick={() => { setMode(m.key); setGraphData(null); setError(null); }}
                    className={`px-2 py-1 text-xs rounded ${
                      mode === m.key ? "bg-purple-100 text-purple-700 font-semibold" : "text-gray-500 hover:bg-gray-100"
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          {activeTenant !== "__chat__" && (
            <button
              onClick={() => handleQuery()}
              disabled={loading}
              className="px-3 py-1 bg-purple-500 text-white text-sm rounded hover:bg-purple-600 disabled:opacity-30"
            >
              {loading ? "조회 중..." : "조회"}
            </button>
          )}
          {currentData && (
            <span className="text-xs text-gray-400">
              {currentData.nodes.length}개 노드, {currentData.edges.length}개 관계
            </span>
          )}
        </div>
      </div>

      {/* Graph area */}
      <div className="flex-1 relative">
        {loading && (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <span className="inline-block w-6 h-6 border-2 border-purple-400 border-t-transparent rounded-full animate-spin mb-2" />
              <p className="text-sm">Lexical Graph 조회 중...</p>
            </div>
          </div>
        )}
        {error && (
          <div className="flex items-center justify-center h-full text-red-500">
            <p className="text-sm">{error}</p>
          </div>
        )}
        {!loading && !error && currentData && currentData.nodes.length > 0 && (
          <>
            <EntityGraph data={currentData} />
            <div className="absolute bottom-3 left-3 bg-white/90 backdrop-blur-sm rounded-lg shadow-sm border px-3 py-2 text-[10px]">
              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {[
                  ["#336699", "Source", "rect"],
                  ["#336699", "Chunk", "rect"],
                  ["#669900", "Topic", "rect"],
                  ["#99cc00", "Statement", "rect"],
                  ["#99cc00", "Fact", "diamond"],
                  ["#ff9900", "Entity", "circle"],
                ].map(([color, label, shape]) => (
                  <span key={label} className="flex items-center gap-1">
                    <span
                      className={`w-2.5 h-2.5 inline-block ${shape === "circle" ? "rounded-full" : shape === "diamond" ? "rounded-sm rotate-45 scale-75" : "rounded-sm"}`}
                      style={{ backgroundColor: color }}
                    />
                    {label}
                  </span>
                ))}
              </div>
            </div>
          </>
        )}
        {!loading && !error && !currentData && activeTenant !== "__chat__" && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <p className="text-sm">모드를 선택하고 조회 버튼을 클릭하세요.</p>
              <p className="text-xs mt-1 text-gray-300">
                graphrag-toolkit이 인덱싱한 Lexical Graph를 탐색합니다.
              </p>
            </div>
          </div>
        )}
        {!loading && !error && !currentData && activeTenant === "__chat__" && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p className="text-sm">GraphRAG 질의 결과의 Lexical Graph 데이터를 불러오는 중...</p>
          </div>
        )}
      </div>
    </div>
  );
}
