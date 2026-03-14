import { useState } from "react";
import type { GraphData, GraphNode as GNode } from "../../types";
import GraphNetwork from "./GraphNetwork";

interface Props {
  graphDataMap: Record<string, GraphData | null>;
}

const TENANTS = [
  { key: "ETF", label: "ETF" },
  { key: "Bond", label: "채권" },
  { key: "Fund", label: "펀드" },
] as const;

export default function GraphNetworkPage({ graphDataMap }: Props) {
  const [activeTenant, setActiveTenant] = useState<string>("ETF");
  const [selectedNode, setSelectedNode] = useState<GNode | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const currentData = graphDataMap[activeTenant];

  const filteredData: GraphData | null =
    currentData && searchQuery
      ? {
          nodes: currentData.nodes.filter((n) =>
            n.label.toLowerCase().includes(searchQuery.toLowerCase())
          ),
          edges: currentData.edges.filter(
            (e) =>
              currentData.nodes
                .filter((n) =>
                  n.label.toLowerCase().includes(searchQuery.toLowerCase())
                )
                .some((n) => n.id === e.source || n.id === e.target)
          ),
        }
      : currentData;

  const handleNodeClick = (nodeId: string) => {
    const node = currentData?.nodes.find((n) => n.id === nodeId);
    setSelectedNode(node || null);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Top bar */}
      <div className="flex items-center justify-between border-b bg-white px-4 py-2">
        <div className="flex gap-1">
          {TENANTS.map((t) => (
            <button
              key={t.key}
              onClick={() => {
                setActiveTenant(t.key);
                setSelectedNode(null);
              }}
              className={`px-3 py-1 text-sm rounded ${
                activeTenant === t.key
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="노드 검색..."
          className="border rounded px-2 py-1 text-sm w-48"
        />
      </div>

      {/* Graph area */}
      <div className="flex-1 relative">
        {filteredData ? (
          <GraphNetwork data={filteredData} onNodeClick={handleNodeClick} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>그래프 데이터를 로드 중입니다...</p>
          </div>
        )}

        {/* Node details panel */}
        {selectedNode && (
          <div className="absolute top-2 right-2 bg-white shadow-lg rounded-lg p-3 w-64 border text-xs">
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
