import CytoscapeComponent from "react-cytoscapejs";
import type { GraphData } from "../../types";

interface Props {
  data: GraphData;
  onNodeClick?: (nodeId: string) => void;
}

const NODE_COLORS: Record<string, string> = {
  ETF: "#3B82F6",
  Fund: "#3B82F6",
  Bond: "#3B82F6",
  Index: "#10B981",
  Benchmark: "#10B981",
  Holding: "#F59E0B",
  Sector: "#F59E0B",
  RiskFactor: "#EF4444",
  AssetManager: "#8B5CF6",
  ManagementCompany: "#8B5CF6",
  Issuer: "#8B5CF6",
  CreditRating: "#EC4899",
  Market: "#06B6D4",
};

function getColor(type: string): string {
  return NODE_COLORS[type] || "#6B7280";
}

export default function GraphNetwork({ data, onNodeClick }: Props) {
  if (!data || (!data.nodes.length && !data.edges.length)) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        그래프 데이터가 없습니다
      </div>
    );
  }

  const elements = [
    ...data.nodes.map((n) => ({
      data: {
        id: n.id,
        label: n.label,
        type: n.type,
        ...n.properties,
      },
    })),
    ...data.edges.map((e, i) => ({
      data: {
        id: `edge-${i}`,
        source: e.source,
        target: e.target,
        label: e.label,
      },
    })),
  ];

  const stylesheet = [
    {
      selector: "node",
      style: {
        label: "data(label)",
        "background-color": (el: { data: (key: string) => string }) =>
          getColor(el.data("type")),
        width: 30,
        height: 30,
        "font-size": "10px",
        "text-valign": "bottom" as const,
        "text-margin-y": 5,
        color: "#374151",
      },
    },
    {
      selector: "edge",
      style: {
        label: "data(label)",
        "line-color": "#94A3B8",
        "target-arrow-color": "#94A3B8",
        "target-arrow-shape": "triangle" as const,
        "curve-style": "bezier" as const,
        "font-size": "8px",
        color: "#94A3B8",
        width: 1.5,
      },
    },
    {
      selector: "node:selected",
      style: {
        "border-width": 3,
        "border-color": "#1D4ED8",
      },
    },
  ];

  return (
    <CytoscapeComponent
      elements={elements}
      stylesheet={stylesheet}
      layout={{ name: "cose-bilkent", animate: true } as unknown as cytoscape.LayoutOptions}
      style={{ width: "100%", height: "100%" }}
      minZoom={0.3}
      maxZoom={3}
      cy={(cy) => {
        cy.on("tap", "node", (evt) => {
          onNodeClick?.(evt.target.id());
        });
      }}
    />
  );
}
