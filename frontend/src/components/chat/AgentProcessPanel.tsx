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

function copyToClipboard(text: string): boolean {
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.cssText = "position:fixed;left:-9999px;top:-9999px";
    document.body.appendChild(ta);
    ta.select();
    ta.setSelectionRange(0, text.length);
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  } catch {
    return false;
  }
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    let ok = false;
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
      return;
    }
    ok = copyToClipboard(text);
    if (ok) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };
  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-0.5 text-[10px] text-gray-400 hover:text-orange-600 transition-colors"
      title="복사"
    >
      {copied ? (
        <>
          <svg className="w-3.5 h-3.5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-green-500 font-medium">Copied!</span>
        </>
      ) : (
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )}
    </button>
  );
}

function Toggle({
  label,
  children,
  defaultOpen = false,
  copyText,
}: {
  label: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  copyText?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="mt-1">
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-1 text-[11px] text-orange-600 hover:text-orange-800"
        >
          <span className="text-[10px]">{open ? "▾" : "▸"}</span>
          {label}
        </button>
        {copyText && <CopyButton text={copyText} />}
      </div>
      {open && <div className="mt-1 ml-2">{children}</div>}
    </div>
  );
}

function Spinner() {
  return (
    <span className="inline-block w-3 h-3 border-2 border-orange-400 border-t-transparent rounded-full animate-spin" />
  );
}

function TokenBadge({ tokensIn, tokensOut }: { tokensIn: number; tokensOut: number }) {
  if (tokensIn === 0 && tokensOut === 0) return null;
  return (
    <span className="text-[11px] text-orange-700 font-bold ml-1">
      {tokensIn.toLocaleString()}+{tokensOut.toLocaleString()} tok
    </span>
  );
}

function QueryBlock({ language, code }: { language: string; code: string }) {
  return (
    <SyntaxHighlighter
      language={language}
      style={oneLight}
      className="rounded text-[11px] !p-2 !m-0"
      customStyle={{ fontSize: "11px" }}
    >
      {code}
    </SyntaxHighlighter>
  );
}

export default function AgentProcessPanel({ process, total, isStreaming }: Props) {
  const intent = process.intent_detection;
  const tool = process.tool_selection;
  const query = process.query_generation;
  const exec = process.query_execution;
  const resp = process.response_generation;

  // Extra fields from query (toolkit_params / opensearch_query for GraphRAG)
  const qExtra = query as Record<string, unknown> | null;
  const execExtra = exec as Record<string, unknown> | null;

  // Detect raw_data shape for GraphRAG (object with opensearch_results/statements)
  const rawData = execExtra?.raw_data;
  const isGraphRAGData = rawData && typeof rawData === "object" && !Array.isArray(rawData) &&
    ("opensearch_results" in (rawData as Record<string, unknown>) || "statements" in (rawData as Record<string, unknown>));
  const graphRAGRaw = isGraphRAGData ? rawData as Record<string, unknown> : null;

  return (
    <div className="h-full flex flex-col overflow-hidden bg-white">
      <div className="px-3 py-2 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-800">Agent Process</h3>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
        {/* Intent Detection + Tool Selection (single LLM call) */}
        {intent && tool && (
          <div className="border-b border-gray-100 pb-2">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-green-500 font-bold">&#10003;</span>
              <span className="font-medium text-gray-800">Intent Detection + Tool Selection</span>
              <span className="text-gray-400 ml-auto">{intent.latency.toFixed(1)}s</span>
            </div>
            <div className="ml-5 mt-1.5 space-y-1.5 text-xs">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-gray-500 font-medium">Intent:</span>
                <span className="bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded font-semibold">
                  {(intent as Record<string, unknown>).intent as string}
                </span>
                <span className="text-orange-500 font-medium">
                  ({((intent as Record<string, unknown>).confidence as number)?.toFixed(2)} 확률)
                </span>
              </div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-gray-500 font-medium">Tool:</span>
                <span className={`px-1.5 py-0.5 rounded font-semibold ${
                  (tool as Record<string, unknown>).tool === "text2sql"
                    ? "bg-blue-100 text-blue-700"
                    : (tool as Record<string, unknown>).tool === "rag"
                    ? "bg-green-100 text-green-700"
                    : (tool as Record<string, unknown>).tool === "graphrag"
                    ? "bg-purple-100 text-purple-700"
                    : "bg-cyan-100 text-cyan-700"
                }`}>
                  {(tool as Record<string, unknown>).tool as string}
                </span>
                <TokenBadge tokensIn={intent.tokens_in + tool.tokens_in} tokensOut={intent.tokens_out + tool.tokens_out} />
              </div>
              <p className="text-gray-400">
                {(tool as Record<string, unknown>).rationale as string}
              </p>
            </div>
          </div>
        )}
        {intent && !tool && (
          <div className="border-b border-gray-100 pb-2">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-green-500 font-bold">&#10003;</span>
              <span className="font-medium text-gray-800">Intent Detection</span>
              <span className="text-gray-400 ml-auto">{intent.latency.toFixed(1)}s</span>
            </div>
            <div className="ml-5 mt-1 flex items-center gap-1.5 text-xs flex-wrap">
              <span className="bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded font-semibold">
                {(intent as Record<string, unknown>).intent as string}
              </span>
            </div>
          </div>
        )}
        {isStreaming && !intent && (
          <div className="flex items-center gap-2 text-xs text-orange-500 pb-2">
            <Spinner /> Intent + Tool 감지 중...
          </div>
        )}

        {/* Query Generation */}
        {query && (
          <div className="border-b border-gray-100 pb-2">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-green-500 font-bold">&#10003;</span>
              <span className="font-medium text-gray-800">
                {query.query_type === "sql" ? "SQL 생성" :
                 query.query_type === "opencypher" ? "Cypher 생성" :
                 query.query_type === "vector_search" ? "벡터 검색" :
                 query.query_type === "graph_search" ? "GraphRAG 검색" : "쿼리 생성"}
              </span>
              <span className="text-gray-400 ml-auto">{query.latency.toFixed(1)}s</span>
            </div>
            <div className="ml-5 mt-0.5 text-[10px] text-gray-400">
              <TokenBadge tokensIn={query.tokens_in} tokensOut={query.tokens_out} />
            </div>

            {/* SQL */}
            {query.query && query.query_type === "sql" && (
              <div className="ml-5">
                <Toggle label="SQL 보기" copyText={query.query}>
                  <QueryBlock language="sql" code={query.query} />
                </Toggle>
              </div>
            )}

            {/* OpenCypher */}
            {query.query && query.query_type === "opencypher" && (
              <div className="ml-5">
                <Toggle label="Cypher 보기" copyText={query.query}>
                  <QueryBlock language="cypher" code={query.query} />
                </Toggle>
              </div>
            )}

            {/* RAG - Vector Search */}
            {query.query && query.query_type === "vector_search" && (
              <div className="ml-5">
                <Toggle label="OpenSearch 쿼리 보기" copyText={query.query}>
                  <QueryBlock language="json" code={query.query} />
                </Toggle>
              </div>
            )}

            {/* GraphRAG - Toolkit Params */}
            {query.query_type === "graph_search" && (
              <div className="ml-5 space-y-0.5">
                {qExtra?.toolkit_params && (
                  <Toggle label="Toolkit Traversal 파라미터 보기" copyText={qExtra.toolkit_params as string}>
                    <QueryBlock language="json" code={qExtra.toolkit_params as string} />
                  </Toggle>
                )}
              </div>
            )}
          </div>
        )}
        {isStreaming && tool && !query && (
          <div className="flex items-center gap-2 text-xs text-orange-500 pb-2">
            <Spinner /> 쿼리 생성 중...
          </div>
        )}

        {/* Query Execution */}
        {exec && (
          <div className="border-b border-gray-100 pb-2">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-green-500 font-bold">&#10003;</span>
              <span className="font-medium text-gray-800">실행 완료</span>
              <span className="text-gray-400 ml-auto">{exec.latency.toFixed(1)}s</span>
            </div>
            <p className="ml-5 mt-1 text-xs text-gray-500">{exec.result_summary}</p>
            {/* Estimated token usage for GraphRAG toolkit LLM */}
            {execExtra?.est_tokens_in && (execExtra.est_tokens_in as number) > 0 && (
              <div className="ml-5 mt-0.5 text-[10px] text-gray-400">
                Toolkit LLM (추정): <span className="text-orange-600 font-medium">{(execExtra.est_tokens_in as number).toLocaleString()}+{(execExtra.est_tokens_out as number || 0).toLocaleString()} tok</span>
              </div>
            )}

            {/* GraphRAG: separate toggles for OpenSearch docs vs Neptune results */}
            {graphRAGRaw && (
              <div className="ml-5 space-y-0.5">
                {/* Toolkit Traversal results (statements from traversal search) */}
                {Array.isArray(graphRAGRaw.opensearch_results) && (graphRAGRaw.opensearch_results as Record<string, unknown>[]).length > 0 && (
                  <Toggle label={`Toolkit Traversal 결과 (${(graphRAGRaw.opensearch_results as Record<string, unknown>[]).length}건)`}>
                    <div className="max-h-48 overflow-auto text-[11px] text-gray-600 space-y-2">
                      {(graphRAGRaw.opensearch_results as Record<string, unknown>[]).map((doc, i) => (
                        <div key={i} className="border-l-2 border-green-300 pl-2">
                          <div className="text-[10px] text-green-600 font-medium mb-0.5">
                            문서 {i + 1} (score: {String(doc.score ?? "")})
                          </div>
                          <p className="text-gray-600 whitespace-pre-wrap">{String(doc.text ?? "").slice(0, 300)}{String(doc.text ?? "").length > 300 ? "..." : ""}</p>
                        </div>
                      ))}
                    </div>
                  </Toggle>
                )}
              </div>
            )}

            {/* Array raw_data (SQL/OpenCypher/RAG) */}
            {!graphRAGRaw && exec.raw_data && Array.isArray(exec.raw_data) && exec.raw_data.length > 0 && (
              <div className="ml-5">
                <Toggle label={`결과 데이터 (${exec.raw_data.length}건)`}>
                  <div className="max-h-60 overflow-auto">
                    <DataTable data={exec.raw_data as Record<string, unknown>[]} maxRows={20} />
                  </div>
                </Toggle>
              </div>
            )}
          </div>
        )}
        {isStreaming && query && !exec && (
          <div className="flex items-center gap-2 text-xs text-orange-500 pb-2">
            <Spinner /> 쿼리 실행 중...
          </div>
        )}

        {/* Response Generation */}
        {resp && (
          <div className="pb-2">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-green-500 font-bold">&#10003;</span>
              <span className="font-medium text-gray-800">응답 생성 완료</span>
              <TokenBadge tokensIn={resp.tokens_in} tokensOut={resp.tokens_out} />
              {(resp as Record<string, unknown>).estimated && (
                <span className="text-[10px] text-gray-400">(Toolkit Traversal 추정값)</span>
              )}
              <span className="text-gray-400 ml-auto">{resp.latency.toFixed(1)}s</span>
            </div>
          </div>
        )}
        {isStreaming && exec && !resp && (
          <div className="flex items-center gap-2 text-xs text-orange-500 pb-2">
            <Spinner /> 응답 생성 중...
          </div>
        )}
      </div>

      {/* Total summary */}
      {total && (
        <div className="px-3 py-2 border-t border-gray-200 text-xs">
          <div className="font-semibold text-gray-800">
            종합: {total.latency.toFixed(1)}s &middot;{" "}
            {(total.tokens_in + total.tokens_out).toLocaleString()} 토큰 &middot;{" "}
            ${total.cost.toFixed(4)}
          </div>
        </div>
      )}
    </div>
  );
}
