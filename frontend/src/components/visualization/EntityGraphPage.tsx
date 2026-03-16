import { useCallback, useEffect, useState } from "react";
import type { GraphData, GraphNode as GNode } from "../../types";
import { useApi } from "../../hooks/useApi";
import EntityGraph from "./EntityGraph";

const TENANTS = [
  { key: "ETF", label: "ETF", desc: "ETF 전체 중 200개 관계 샘플링" },
  { key: "Bond", label: "채권", desc: "채권 전체 중 200개 관계 샘플링" },
  { key: "Fund", label: "펀드", desc: "펀드 전체 중 200개 관계 샘플링" },
] as const;

interface Props {
  chatGraphData?: { data: GraphData; label: string } | null;
}

export default function EntityGraphPage({ chatGraphData }: Props) {
  const api = useApi();
  const [activeTenant, setActiveTenant] = useState<string>(
    chatGraphData ? "__chat__" : "ETF"
  );
  const [selectedNode, setSelectedNode] = useState<GNode | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [graphDataMap, setGraphDataMap] = useState<Record<string, GraphData | null>>({
    ETF: null, Bond: null, Fund: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (chatGraphData) {
      setActiveTenant("__chat__");
      setSelectedNode(null);
      setSearchQuery("");
      setActiveSearch("");
    }
  }, [chatGraphData]);

  useEffect(() => {
    if (!chatGraphData && activeTenant === "__chat__") {
      setActiveTenant("ETF");
    }
  }, [chatGraphData, activeTenant]);

  // Load graph on mount or tenant change
  useEffect(() => {
    if (activeTenant === "__chat__") return;
    // Skip if already loaded
    if (graphDataMap[activeTenant]) return;

    let cancelled = false;
    setLoading(true);
    setError(null);
    api.getEntityGraph(activeTenant).then((data) => {
      if (!cancelled) {
        setGraphDataMap((prev) => ({ ...prev, [activeTenant]: data }));
        setLoading(false);
      }
    }).catch((e) => {
      if (!cancelled) {
        setError(`그래프 데이터 로드 실패: ${e instanceof Error ? e.message : String(e)}`);
        setLoading(false);
      }
    });
    return () => { cancelled = true; };
  }, [activeTenant, graphDataMap[activeTenant], api]);

  // Neptune search
  const handleSearch = useCallback(async () => {
    const q = searchQuery.trim();
    if (!q || activeTenant === "__chat__") return;
    setLoading(true);
    setError(null);
    setActiveSearch(q);
    try {
      const data = await api.getEntityGraph(activeTenant, q);
      if (!data.nodes || data.nodes.length === 0) {
        setError(`"${q}" 관련 엔티티를 찾을 수 없습니다.`);
        setActiveSearch("");
        return;
      }
      const key = `${activeTenant}__search`;
      setGraphDataMap((prev) => ({ ...prev, [key]: data }));
    } catch (e) {
      setError(`검색 실패: ${e instanceof Error ? e.message : String(e)}`);
      setActiveSearch("");
    } finally {
      setLoading(false);
    }
  }, [searchQuery, activeTenant, api]);

  const handleClearSearch = () => {
    setSearchQuery("");
    setActiveSearch("");
  };

  const handleRefresh = () => {
    if (activeTenant !== "__chat__") {
      // Setting to null triggers the useEffect to reload
      setGraphDataMap((prev) => ({ ...prev, [activeTenant]: null }));
    }
  };

  const searchKey = `${activeTenant}__search`;
  const currentData: GraphData | null =
    activeTenant === "__chat__"
      ? chatGraphData?.data ?? null
      : activeSearch && graphDataMap[searchKey]
        ? graphDataMap[searchKey]
        : graphDataMap[activeTenant];

  const handleNodeClick = (nodeId: string) => {
    const node = currentData?.nodes.find((n) => n.id === nodeId);
    setSelectedNode(node || null);
  };

  const chatLabel = chatGraphData?.label
    ? chatGraphData.label.length > 15
      ? chatGraphData.label.slice(0, 15) + "..."
      : chatGraphData.label
    : "챗봇 결과";

  const activeTenantInfo = TENANTS.find((t) => t.key === activeTenant);
  const tabDescription =
    activeTenant === "__chat__"
      ? `질의 결과: ${chatLabel}`
      : activeSearch
        ? `"${activeSearch}" 검색 결과 (최대 200개 관계 조회)`
        : activeTenantInfo?.desc || "";

  return (
    <div className="flex flex-col h-full">
      {/* Top bar */}
      <div className="flex items-center justify-between border-b bg-white px-4 py-2">
        <div className="flex items-center gap-3">
          <div className="flex gap-1">
            {TENANTS.map((t) => (
              <button
                key={t.key}
                onClick={() => {
                  setActiveTenant(t.key);
                  setSelectedNode(null);
                  setSearchQuery("");
                  setActiveSearch("");
                }}
                className={`px-3 py-1 text-sm rounded ${
                  activeTenant === t.key && !activeSearch
                    ? "bg-orange-500 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {t.label}
              </button>
            ))}
            {chatGraphData && (
              <button
                onClick={() => {
                  setActiveTenant("__chat__");
                  setSelectedNode(null);
                  setSearchQuery("");
                  setActiveSearch("");
                }}
                className={`px-3 py-1 text-sm rounded flex items-center gap-1 ${
                  activeTenant === "__chat__"
                    ? "bg-orange-500 text-white"
                    : "bg-orange-50 text-orange-700 border border-orange-200 hover:bg-orange-100"
                }`}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
                {chatLabel}
              </button>
            )}
            {/* Active search indicator as a tab-like pill */}
            {activeSearch && (
              <span className="px-3 py-1 text-sm rounded bg-orange-500 text-white flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                "{activeSearch}"
                <button
                  onClick={handleClearSearch}
                  className="ml-1 hover:bg-orange-600 rounded-full p-0.5"
                  title="검색 해제"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </span>
            )}
          </div>
          <span className="text-xs text-gray-400 hidden sm:inline">
            {tabDescription}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {currentData && (
            <span className="text-xs text-gray-400">
              {currentData.nodes.length}개 노드, {currentData.edges.length}개 관계
            </span>
          )}
          {activeTenant !== "__chat__" && !activeSearch && (
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
              title="그래프 새로고침"
            >
              <svg className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          )}
          {activeTenant !== "__chat__" && (
            <div className="relative flex items-center">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearch();
                }}
                placeholder="엔티티 검색 (Enter로 조회)"
                className="border rounded-l px-2 py-1 text-sm w-52"
              />
              <button
                onClick={handleSearch}
                disabled={!searchQuery.trim() || loading}
                className="px-2 py-1 bg-orange-500 text-white text-sm rounded-r hover:bg-orange-600 disabled:opacity-30 disabled:cursor-not-allowed"
                title="Neptune에서 검색"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Graph area */}
      <div className="flex-1 relative">
        {loading && (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <span className="inline-block w-6 h-6 border-2 border-orange-400 border-t-transparent rounded-full animate-spin mb-2" />
              <p className="text-sm">
                {activeSearch ? `"${searchQuery.trim()}" Neptune 검색 중...` : "그래프 데이터를 로드 중입니다..."}
              </p>
            </div>
          </div>
        )}
        {error && (
          <div className="flex items-center justify-center h-full text-red-500">
            <div className="text-center">
              <p className="text-sm">{error}</p>
              <button
                onClick={activeSearch ? handleClearSearch : handleRefresh}
                className="mt-2 px-3 py-1 bg-orange-500 text-white rounded text-sm"
              >
                {activeSearch ? "전체 그래프로 돌아가기" : "다시 시도"}
              </button>
            </div>
          </div>
        )}
        {!loading && !error && currentData && currentData.nodes.length > 0 && (
          <>
            <EntityGraph
              data={currentData}
              onNodeClick={handleNodeClick}
            />
            {/* Legend */}
            <div className="absolute bottom-3 left-3 bg-white/90 backdrop-blur-sm rounded-lg shadow-sm border px-3 py-2 text-[10px]">
              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {[
                  ["#3B82F6", "ETF/Fund"],
                  ["#F59E0B", "종목"],
                  ["#10B981", "지수"],
                  ["#8B5CF6", "분류"],
                  ["#EF4444", "운용사"],
                  ["#EC4899", "발행사"],
                  ["#F97316", "등급"],
                ].map(([color, label]) => (
                  <span key={label} className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: color }} />
                    {label}
                  </span>
                ))}
              </div>
            </div>
          </>
        )}
        {!loading && !error && currentData && currentData.nodes.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p className="text-sm">이 도메인에 그래프 데이터가 없습니다.</p>
          </div>
        )}
        {!loading && !error && !currentData && activeTenant !== "__chat__" && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p className="text-sm">그래프를 로드하려면 위 도메인 탭을 클릭하세요.</p>
          </div>
        )}
        {!loading && !error && !currentData && activeTenant === "__chat__" && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p className="text-sm">챗봇에서 그래프 결과가 있는 질문을 해보세요.</p>
          </div>
        )}

        {/* Node details panel */}
        {selectedNode && (
          <div className="absolute top-2 right-14 bg-white shadow-lg rounded-lg p-3 w-64 border text-xs">
            <div className="flex justify-between items-center mb-2">
              <span className="font-semibold text-gray-700">
                {selectedNode.label}
              </span>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                &#10005;
              </button>
            </div>
            <p className="text-gray-500 mb-1">Type: {selectedNode.type}</p>
            {Object.entries(selectedNode.properties).map(([k, v]) => (
              <p key={k} className="text-gray-500">
                {k}: {String(v)}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
