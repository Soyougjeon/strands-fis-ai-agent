import { useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { AgentProcess, TotalMetrics } from "../../types";
import DataTable from "../common/DataTable";

interface Props {
  process: Partial<AgentProcess>;
  total: TotalMetrics | null;
  isStreaming: boolean;
}

function Toggle({
  label,
  children,
  defaultOpen = false,
}: {
  label: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="mt-1">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-gray-700"
      >
        <span className="text-[10px]">{open ? "▾" : "▸"}</span>
        {label}
      </button>
      {open && <div className="mt-1 ml-3">{children}</div>}
    </div>
  );
}

function Spinner() {
  return (
    <span className="inline-block w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
  );
}

export default function InlineAgentProcess({ process, total, isStreaming }: Props) {
  const intent = process.intent_detection;
  const tool = process.tool_selection;
  const query = process.query_generation;
  const exec = process.query_execution;
  const resp = process.response_generation;

  const selectedTool = (tool as Record<string, unknown>)?.tool as string | undefined;

  const hasAnyStep = intent || tool || query || exec || resp;
  if (!hasAnyStep && !isStreaming) return null;

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs max-w-[85%]">
      {/* Steps - dynamically generated */}
      <div className="space-y-1.5">
        {/* Intent Detection */}
        {intent && (
          <div className="flex items-center gap-2">
            <span className="text-green-500 text-[10px]">&#10003;</span>
            <span className="text-gray-600">Intent:</span>
            <span className="bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-[11px] font-medium">
              {(intent as Record<string, unknown>).intent as string}
            </span>
            <span className="text-gray-400">
              ({((intent as Record<string, unknown>).confidence as number)?.toFixed(2)})
            </span>
            <span className="text-gray-400 ml-auto">{intent.latency.toFixed(1)}s</span>
          </div>
        )}
        {isStreaming && !intent && (
          <div className="flex items-center gap-2 text-gray-500">
            <Spinner /> Intent 감지 중...
          </div>
        )}

        {/* Tool Selection */}
        {tool && (
          <div className="flex items-center gap-2">
            <span className="text-green-500 text-[10px]">&#10003;</span>
            <span className="text-gray-600">Tool:</span>
            <span className="bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded text-[11px] font-medium">
              {(tool as Record<string, unknown>).tool as string}
            </span>
            <span className="text-gray-400 ml-auto">{tool.latency.toFixed(1)}s</span>
          </div>
        )}
        {isStreaming && intent && !tool && (
          <div className="flex items-center gap-2 text-gray-500">
            <Spinner /> Tool 선택 중...
          </div>
        )}

        {/* Query Generation - with toggle for SQL/Cypher */}
        {query && (
          <div>
            <div className="flex items-center gap-2">
              <span className="text-green-500 text-[10px]">&#10003;</span>
              <span className="text-gray-600">
                {query.query_type === "sql" ? "SQL 생성" :
                 query.query_type === "opencypher" ? "Cypher 생성" :
                 query.query_type === "vector_search" ? "벡터 검색" : "쿼리 생성"}
              </span>
              <span className="text-gray-400 ml-auto">{query.latency.toFixed(1)}s</span>
            </div>
            {query.query && (query.query_type === "sql" || query.query_type === "opencypher") && (
              <Toggle label={query.query_type === "sql" ? "SQL 보기" : "Cypher 보기"}>
                <SyntaxHighlighter
                  language={query.query_type === "sql" ? "sql" : "cypher"}
                  style={oneLight}
                  className="rounded text-[11px] !p-2 !m-0"
                  customStyle={{ fontSize: "11px" }}
                >
                  {query.query}
                </SyntaxHighlighter>
              </Toggle>
            )}
          </div>
        )}
        {isStreaming && tool && !query && (
          <div className="flex items-center gap-2 text-gray-500">
            <Spinner /> 쿼리 생성 중...
          </div>
        )}

        {/* Query Execution - with toggle for results */}
        {exec && (
          <div>
            <div className="flex items-center gap-2">
              <span className="text-green-500 text-[10px]">&#10003;</span>
              <span className="text-gray-600">실행 완료</span>
              <span className="text-gray-400">{exec.result_summary}</span>
              <span className="text-gray-400 ml-auto">{exec.latency.toFixed(1)}s</span>
            </div>
            {exec.raw_data && Array.isArray(exec.raw_data) && exec.raw_data.length > 0 && (
              <Toggle label={`결과 데이터 (${exec.raw_data.length}건)`}>
                <div className="max-h-48 overflow-auto">
                  <DataTable data={exec.raw_data as Record<string, unknown>[]} maxRows={20} />
                </div>
              </Toggle>
            )}
          </div>
        )}
        {isStreaming && query && !exec && (
          <div className="flex items-center gap-2 text-gray-500">
            <Spinner /> 쿼리 실행 중...
          </div>
        )}

        {/* Response Generation */}
        {resp && (
          <div className="flex items-center gap-2">
            <span className="text-green-500 text-[10px]">&#10003;</span>
            <span className="text-gray-600">응답 생성 완료</span>
            <span className="text-gray-400 ml-auto">{resp.latency.toFixed(1)}s</span>
          </div>
        )}
        {isStreaming && exec && !resp && (
          <div className="flex items-center gap-2 text-gray-500">
            <Spinner /> 응답 생성 중...
          </div>
        )}
      </div>

      {/* Total summary */}
      {total && (
        <div className="mt-2 pt-1.5 border-t border-gray-200 text-[11px] text-gray-500">
          종합: {total.latency.toFixed(1)}s &middot;{" "}
          {(total.tokens_in + total.tokens_out).toLocaleString()} 토큰 &middot;{" "}
          ${total.cost.toFixed(4)}
        </div>
      )}
    </div>
  );
}
