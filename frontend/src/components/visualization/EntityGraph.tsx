import { useRef, useEffect, useMemo, useState, useCallback } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import type { GraphData } from "../../types";

interface Props {
  data: GraphData;
  onNodeClick?: (nodeId: string) => void;
}

const NODE_COLORS: Record<string, string> = {
  ETF: "#3B82F6",
  Fund: "#3B82F6",
  Bond: "#2563EB",
  Index: "#10B981",
  Benchmark: "#10B981",
  Holding: "#F59E0B",
  Sector: "#8B5CF6",
  Category: "#A78BFA",
  AssetManager: "#EF4444",
  ManagementCompany: "#EF4444",
  Issuer: "#EC4899",
  CreditRating: "#F472B6",
  IssuerType: "#D946EF",
  CouponType: "#06B6D4",
  Market: "#06B6D4",
  FundType: "#8B5CF6",
  RiskGrade: "#F97316",
  // graphrag-toolkit Knowledge Graph node types (matching toolkit formatting_config)
  Source: "#336699",
  Chunk: "#336699",
  Topic: "#669900",
  Statement: "#99cc00",
  Fact: "#99cc00",
  Entity: "#ff9900",
  "Financial Instrument": "#ff9900",
  Service: "#ff9900",
  Event: "#ff9900",
  Product: "#ff9900",
  Company: "#ff9900",
  Location: "#ff9900",
};

const EDGE_COLORS: Record<string, string> = {
  HOLDS: "#F97316",
  TRACKS: "#10B981",
  MANAGED_BY: "#EF4444",
  CATEGORY: "#A78BFA",
  SECTOR: "#8B5CF6",
  BENCHMARKS: "#10B981",
  ISSUED_BY: "#EC4899",
  RATED: "#F472B6",
  SAME_BENCHMARK: "#C4B5FD",
  SHARES_HOLDING: "#CBD5E1",
  SAME_ISSUER: "#FBCFE8",
  SAME_COMPANY: "#FBCFE8",
  TYPE_OF: "#D946EF",
  RISK_GRADE: "#F97316",
  HAS_COUPON: "#06B6D4",
  TRADED_IN: "#06B6D4",
  SUB_TYPE: "#8B5CF6",
};

const DASHED_EDGES = new Set([
  "SHARES_HOLDING", "SAME_BENCHMARK", "SAME_ISSUER", "SAME_COMPANY",
]);

const TARGET_TYPE_MAP: Record<string, string> = {
  HOLDS: "Holding",
  TRACKS: "Index",
  MANAGED_BY: "AssetManager",
  CATEGORY: "Category",
  SECTOR: "Sector",
  BENCHMARKS: "Benchmark",
  ISSUED_BY: "Issuer",
  RATED: "CreditRating",
  TYPE_OF: "FundType",
  RISK_GRADE: "RiskGrade",
  HAS_COUPON: "CouponType",
  TRADED_IN: "Market",
  SUB_TYPE: "FundType",
};

const SOURCE_TYPE_MAP: Record<string, string> = {
  HOLDS: "ETF",
  TRACKS: "ETF",
  MANAGED_BY: "ETF",
  CATEGORY: "ETF",
  SECTOR: "ETF",
  BENCHMARKS: "Fund",
  ISSUED_BY: "Bond",
  RATED: "Bond",
};

function inferNodeTypes(data: GraphData): GraphData {
  const needsInference = data.nodes.some(
    (n) => !n.type || n.type === "Entity" || n.type === ""
  );
  if (!needsInference) return data;

  const typeMap: Record<string, string> = {};
  for (const e of data.edges) {
    if (TARGET_TYPE_MAP[e.label] && !typeMap[e.target]) typeMap[e.target] = TARGET_TYPE_MAP[e.label];
    if (SOURCE_TYPE_MAP[e.label] && !typeMap[e.source]) typeMap[e.source] = SOURCE_TYPE_MAP[e.label];
  }
  for (const e of data.edges) {
    if (e.label === "SAME_BENCHMARK" || e.label === "SHARES_HOLDING") {
      if (!typeMap[e.source]) typeMap[e.source] = "ETF";
      if (!typeMap[e.target]) typeMap[e.target] = "ETF";
    }
    if (e.label === "SAME_ISSUER" || e.label === "SAME_COMPANY") {
      if (!typeMap[e.source]) typeMap[e.source] = "Bond";
      if (!typeMap[e.target]) typeMap[e.target] = "Bond";
    }
  }
  return {
    ...data,
    nodes: data.nodes.map((n) => {
      if (n.type && n.type !== "Entity" && n.type !== "") return n;
      return typeMap[n.id] ? { ...n, type: typeMap[n.id] } : n;
    }),
  };
}

// Toolkit Knowledge Graph: shapes matching toolkit FontAwesome icon mappings
const NODE_SHAPES: Record<string, string> = {
  Source: "round-rectangle",
  Chunk: "round-rectangle",
  Topic: "round-rectangle",
  Statement: "round-rectangle",
  Fact: "diamond",
};

// Toolkit Knowledge Graph: base sizes matching toolkit icon sizes
const NODE_BASE_SIZES: Record<string, number> = {
  Source: 40,       // toolkit: 100 (largest)
  Chunk: 24,        // toolkit: 60
  Topic: 36,        // toolkit: 100
  Statement: 22,    // toolkit: 60
  Fact: 18,         // toolkit: 50 (smallest)
  Entity: 30,       // toolkit: 80
};

function getColor(type: string): string {
  return NODE_COLORS[type] || "#6B7280";
}
function getShape(type: string): string {
  return NODE_SHAPES[type] || "ellipse";
}
function getEdgeColor(label: string): string {
  return EDGE_COLORS[label] || "#94A3B8";
}

export default function EntityGraph({ data, onNodeClick }: Props) {
  const cyRef = useRef<cytoscape.Core | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [boxSelectMode, setBoxSelectMode] = useState(false);
  const [selectedCount, setSelectedCount] = useState(0);
  const [isFocused, setIsFocused] = useState(false);

  const enrichedData = useMemo(() => inferNodeTypes(data), [data]);

  const degreeMap: Record<string, number> = {};
  for (const e of enrichedData.edges) {
    degreeMap[e.source] = (degreeMap[e.source] || 0) + 1;
    degreeMap[e.target] = (degreeMap[e.target] || 0) + 1;
  }
  const maxDegree = Math.max(...Object.values(degreeMap), 1);

  const elements = [
    ...enrichedData.nodes.map((n) => {
      const degree = degreeMap[n.id] || 0;
      const type = n.type || "Entity";
      const baseSize = NODE_BASE_SIZES[type];
      const size = baseSize
        ? baseSize + (degree / maxDegree) * 15
        : 20 + (degree / maxDegree) * 30;
      return {
        data: {
          id: n.id, label: n.label,
          type,
          nodeColor: getColor(type),
          nodeShape: getShape(type),
          nodeSize: size, degree,
          ...n.properties,
        },
      };
    }),
    ...enrichedData.edges.map((e, i) => ({
      data: {
        id: `edge-${i}`, source: e.source, target: e.target,
        label: e.label, edgeColor: getEdgeColor(e.label),
        isDashed: DASHED_EDGES.has(e.label),
      },
    })),
  ];

  const stylesheet: cytoscape.Stylesheet[] = [
    {
      selector: "node",
      style: {
        label: "data(label)",
        shape: "data(nodeShape)" as unknown as string,
        "background-color": "data(nodeColor)" as unknown as string,
        width: "data(nodeSize)" as unknown as number,
        height: "data(nodeSize)" as unknown as number,
        "font-size": "9px", "font-weight": 500,
        "text-valign": "bottom", "text-halign": "center", "text-margin-y": 4,
        color: "#1F2937",
        "text-outline-color": "#FFFFFF", "text-outline-width": 2,
        "border-width": 2, "border-color": "#FFFFFF",
        "text-max-width": "80px", "text-wrap": "ellipsis",
      } as unknown as cytoscape.Css.Node,
    },
    {
      selector: "node[degree >= 5]",
      style: {
        "font-size": "11px", "font-weight": 700,
        "border-width": 3, "border-color": "#FFFFFF", "text-outline-width": 2.5,
      } as unknown as cytoscape.Css.Node,
    },
    {
      selector: "edge",
      style: {
        label: "data(label)",
        "line-color": "data(edgeColor)" as unknown as string,
        "target-arrow-color": "data(edgeColor)" as unknown as string,
        "target-arrow-shape": "triangle", "arrow-scale": 0.8,
        "curve-style": "bezier",
        "font-size": "7px", color: "#9CA3AF",
        "text-rotation": "autorotate",
        "text-outline-color": "#FFFFFF", "text-outline-width": 1.5,
        width: 1.5, opacity: 0.7,
      } as unknown as cytoscape.Css.Edge,
    },
    {
      selector: "edge[isDashed]",
      style: {
        "line-style": "dashed", "line-dash-pattern": [6, 3],
        width: 1, opacity: 0.4, "font-size": "6px",
      } as unknown as cytoscape.Css.Edge,
    },
    {
      selector: 'edge[label = "HOLDS"]',
      style: { width: 2.5, opacity: 0.9 } as unknown as cytoscape.Css.Edge,
    },
    {
      selector: "node:selected",
      style: {
        "border-width": 4, "border-color": "#1D4ED8",
        color: "#1D4ED8", "font-weight": 700, "font-size": "11px",
      } as unknown as cytoscape.Css.Node,
    },
    {
      selector: "node:active",
      style: {
        "overlay-color": "#3B82F6", "overlay-padding": 6, "overlay-opacity": 0.15,
      } as unknown as cytoscape.Css.Node,
    },
    // Hover fade (temporary)
    {
      selector: ".hover-faded",
      style: { opacity: 0.08 } as unknown as cytoscape.Css.Node,
    },
    {
      selector: ".hover-highlight",
      style: { opacity: 1 } as unknown as cytoscape.Css.Node,
    },
    // Focus fade (selection actions)
    {
      selector: ".faded",
      style: { opacity: 0.08 } as unknown as cytoscape.Css.Node,
    },
    {
      selector: ".highlighted",
      style: { opacity: 1 } as unknown as cytoscape.Css.Node,
    },
  ];

  const dataKey = useMemo(() => {
    const ids = enrichedData.nodes.map((n) => n.id).sort().join(",");
    return `graph-${ids.length}-${ids.slice(0, 100)}`;
  }, [enrichedData]);

  // ResizeObserver
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0 && cyRef.current) {
          cyRef.current.resize();
          cyRef.current.fit(undefined, 40);
        }
      }
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, [dataKey]);

  // Box selection mode ref
  const boxSelectRef = useRef(boxSelectMode);
  useEffect(() => {
    boxSelectRef.current = boxSelectMode;
    if (cyRef.current) {
      cyRef.current.boxSelectionEnabled(boxSelectMode);
      cyRef.current.userPanningEnabled(!boxSelectMode);
      cyRef.current.autoungrabify(boxSelectMode);
    }
  }, [boxSelectMode]);

  const handleZoomIn = useCallback(() => {
    if (cyRef.current) cyRef.current.animate({ zoom: cyRef.current.zoom() * 1.3, duration: 200 });
  }, []);
  const handleZoomOut = useCallback(() => {
    if (cyRef.current) cyRef.current.animate({ zoom: cyRef.current.zoom() / 1.3, duration: 200 });
  }, []);
  const handleFit = useCallback(() => {
    if (cyRef.current) cyRef.current.animate({ fit: { eles: cyRef.current.elements(), padding: 40 }, duration: 300 });
  }, []);

  const handleZoomToSelected = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const selected = cy.nodes(":selected");
    if (selected.length) cy.animate({ fit: { eles: selected, padding: 60 }, duration: 300 });
  }, []);

  const handleFocusSelected = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const selected = cy.nodes(":selected");
    if (!selected.length) return;
    const focus = selected.union(selected.edgesWith(selected));
    cy.elements().not(focus).addClass("faded");
    focus.addClass("highlighted");
    setIsFocused(true);
  }, []);

  const handleClearSelection = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.nodes().unselect();
    cy.elements().removeClass("faded highlighted");
    setSelectedCount(0);
    setIsFocused(false);
  }, []);

  const handleResetView = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().removeClass("faded highlighted");
    setIsFocused(false);
  }, []);

  if (!data || (!data.nodes.length && !data.edges.length)) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        그래프 데이터가 없습니다
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative w-full h-full">
      <CytoscapeComponent
        key={dataKey}
        elements={elements}
        stylesheet={stylesheet}
        layout={{
          name: "cose-bilkent",
          animate: "end", animationDuration: 500,
          fit: true, padding: 40,
          nodeRepulsion: 8000, idealEdgeLength: 120,
          edgeElasticity: 0.1, nestingFactor: 0.1,
          gravity: 0.2, numIter: 2500,
          tile: true, tilingPaddingVertical: 20, tilingPaddingHorizontal: 20,
        } as unknown as cytoscape.LayoutOptions}
        style={{ width: "100%", height: "100%" }}
        minZoom={0.2}
        maxZoom={4}
        cy={(cy) => {
          cyRef.current = cy;
          cy.boxSelectionEnabled(boxSelectRef.current);
          cy.userPanningEnabled(!boxSelectRef.current);
          cy.autoungrabify(boxSelectRef.current);

          cy.on("tap", "node", (evt) => onNodeClick?.(evt.target.id()));

          cy.on("select unselect", "node", () => {
            setSelectedCount(cy.nodes(":selected").length);
          });

          // Hover: use separate classes (hover-faded / hover-highlight)
          // so they don't conflict with search classes
          cy.on("mouseover", "node", (evt) => {
            const node = evt.target;
            const neighborhood = node.neighborhood().add(node);
            cy.elements().not(neighborhood).addClass("hover-faded");
            neighborhood.addClass("hover-highlight");
          });
          cy.on("mouseout", "node", () => {
            // Remove hover classes only
            cy.elements().removeClass("hover-faded hover-highlight");
            // Re-apply search if active (search classes may have been visually overridden)
          });

          cy.on("layoutstop", () => {
            setTimeout(() => {
              cy.resize();
              cy.fit(undefined, 40);
            }, 100);
          });
        }}
      />

      {/* Selection action bar */}
      {selectedCount > 0 && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-white/95 backdrop-blur-sm shadow-lg border rounded-lg px-3 py-2 flex items-center gap-2 text-xs z-10">
          <span className="font-semibold text-gray-700">{selectedCount}개 노드 선택</span>
          <div className="w-px h-4 bg-gray-200" />
          <button onClick={handleZoomToSelected} className="px-2 py-1 rounded hover:bg-gray-100 text-gray-600 flex items-center gap-1" title="선택 영역 확대">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" /></svg>
            확대
          </button>
          <button onClick={handleFocusSelected} className={`px-2 py-1 rounded flex items-center gap-1 ${isFocused ? "bg-blue-100 text-blue-700" : "hover:bg-gray-100 text-gray-600"}`} title="선택 노드 간 관계만 보기">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
            관계 보기
          </button>
          {isFocused && (
            <button onClick={handleResetView} className="px-2 py-1 rounded hover:bg-gray-100 text-gray-600 flex items-center gap-1" title="전체 노드 다시 보기">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
              전체 보기
            </button>
          )}
          <div className="w-px h-4 bg-gray-200" />
          <button onClick={handleClearSelection} className="px-2 py-1 rounded hover:bg-red-50 text-gray-400 hover:text-red-500" title="선택 해제">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      )}

      {/* Zoom & selection controls */}
      <div className="absolute top-3 right-3 flex flex-col gap-1">
        <button onClick={handleZoomIn} className="w-8 h-8 bg-white shadow border rounded flex items-center justify-center text-gray-600 hover:bg-gray-50 hover:text-gray-900 text-lg font-bold" title="확대">+</button>
        <button onClick={handleZoomOut} className="w-8 h-8 bg-white shadow border rounded flex items-center justify-center text-gray-600 hover:bg-gray-50 hover:text-gray-900 text-lg font-bold" title="축소">-</button>
        <button onClick={handleFit} className="w-8 h-8 bg-white shadow border rounded flex items-center justify-center text-gray-500 hover:bg-gray-50 hover:text-gray-900" title="전체 보기">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
        </button>
        <div className="h-px bg-gray-200 my-0.5" />
        <button
          onClick={() => setBoxSelectMode(!boxSelectMode)}
          className={`w-8 h-8 shadow border rounded flex items-center justify-center text-sm ${boxSelectMode ? "bg-orange-500 text-white border-orange-500" : "bg-white text-gray-500 hover:bg-gray-50 hover:text-gray-900"}`}
          title={boxSelectMode ? "영역 선택 해제 (드래그로 이동)" : "영역 선택 (드래그로 노드 선택)"}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <rect x="3" y="3" width="18" height="18" rx="1" strokeWidth="2" strokeDasharray="4 2" />
            <circle cx="12" cy="12" r="2" fill="currentColor" stroke="none" />
          </svg>
        </button>
      </div>

      {/* Box select mode indicator */}
      {boxSelectMode && (
        <div className="absolute bottom-3 right-3 bg-orange-500 text-white text-[10px] px-2 py-1 rounded-full shadow">
          영역 선택 모드 - 드래그로 노드를 선택하세요
        </div>
      )}
    </div>
  );
}
