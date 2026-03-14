import ReactECharts from "echarts-for-react";
import type { ChartData } from "../../types";

interface Props {
  data: ChartData;
}

export default function DynamicChart({ data }: Props) {
  const option = buildOption(data);
  if (!option) return null;

  return (
    <div className="my-3">
      <ReactECharts option={option} style={{ height: 300 }} />
    </div>
  );
}

function buildOption(chart: ChartData): Record<string, unknown> | null {
  if (!chart.data || chart.data.length === 0) return null;

  const xValues = chart.data.map((d) => String(d[chart.x_axis] ?? ""));
  const yValues = chart.data.map((d) => Number(d[chart.y_axis] ?? 0));

  if (chart.chart_type === "bar") {
    return {
      title: chart.title ? { text: chart.title, left: "center", textStyle: { fontSize: 14 } } : undefined,
      tooltip: { trigger: "axis" },
      xAxis: { type: "category", data: xValues, axisLabel: { rotate: 30, fontSize: 11 } },
      yAxis: { type: "value" },
      series: [{ type: "bar", data: yValues, itemStyle: { color: "#3B82F6" } }],
      grid: { left: 60, right: 20, bottom: 60, top: 40 },
    };
  }

  if (chart.chart_type === "line") {
    return {
      title: chart.title ? { text: chart.title, left: "center", textStyle: { fontSize: 14 } } : undefined,
      tooltip: { trigger: "axis" },
      xAxis: { type: "category", data: xValues },
      yAxis: { type: "value" },
      series: [{ type: "line", data: yValues, smooth: true, itemStyle: { color: "#3B82F6" } }],
      grid: { left: 60, right: 20, bottom: 40, top: 40 },
    };
  }

  if (chart.chart_type === "pie") {
    const pieData = chart.data.map((d) => ({
      name: String(d[chart.x_axis] ?? ""),
      value: Number(d[chart.y_axis] ?? 0),
    }));
    return {
      title: chart.title ? { text: chart.title, left: "center", textStyle: { fontSize: 14 } } : undefined,
      tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
      series: [{ type: "pie", radius: "60%", data: pieData }],
    };
  }

  return null;
}
