import { useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { AgentProcess } from "../../types";
import DataTable from "../common/DataTable";

interface Props {
  process: Partial<AgentProcess>;
}

const TABS = [
  { key: "sql", label: "SQL", tool: "text2sql" },
  { key: "search", label: "Search", tool: "rag" },
  { key: "graphrag", label: "GraphRAG", tool: "graphrag" },
  { key: "cypher", label: "OpenCypher", tool: "opencypher" },
  { key: "result", label: "결과", tool: null },
] as const;

type TabKey = (typeof TABS)[number]["key"];

export default function DetailTabs({ process }: Props) {
  const selectedTool = (process.tool_selection as Record<string, unknown>)
    ?.tool as string | undefined;
  const defaultTab =
    TABS.find((t) => t.tool === selectedTool)?.key || "result";
  const [activeTab, setActiveTab] = useState<TabKey>(defaultTab);

  const query = process.query_generation;
  const exec = process.query_execution;

  return (
    <div className="border-t border-gray-200 bg-white">
      {/* Tab bar */}
      <div className="flex border-b text-xs">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-3 py-2 font-medium ${
              activeTab === tab.key
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-3 max-h-48 overflow-y-auto text-xs">
        {activeTab === "sql" && (
          <>
            {query?.query_type === "sql" && query.query ? (
              <SyntaxHighlighter language="sql" style={oneLight} className="rounded text-xs">
                {query.query}
              </SyntaxHighlighter>
            ) : (
              <p className="text-gray-400">해당 데이터가 없습니다</p>
            )}
            {exec?.raw_data && Array.isArray(exec.raw_data) && (
              <DataTable data={exec.raw_data as Record<string, unknown>[]} maxRows={20} />
            )}
          </>
        )}

        {activeTab === "search" && (
          <>
            {query?.query_type === "vector_search" ? (
              <div>
                <p className="font-medium mb-1">{query.query}</p>
                {exec?.raw_data && Array.isArray(exec.raw_data) && (
                  <div className="space-y-2">
                    {(exec.raw_data as Array<Record<string, unknown>>).map(
                      (chunk, i) => (
                        <div
                          key={i}
                          className="border rounded p-2 bg-gray-50"
                        >
                          <p className="text-gray-600">
                            {String(chunk.text).slice(0, 300)}
                          </p>
                          <p className="text-gray-400 mt-1">
                            score: {Number(chunk.score).toFixed(4)}
                          </p>
                        </div>
                      )
                    )}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-400">해당 데이터가 없습니다</p>
            )}
          </>
        )}

        {activeTab === "graphrag" && (
          <>
            {exec?.result_summary &&
            selectedTool === "graphrag" ? (
              <div>
                <p className="whitespace-pre-wrap">{exec.result_summary}</p>
              </div>
            ) : (
              <p className="text-gray-400">해당 데이터가 없습니다</p>
            )}
          </>
        )}

        {activeTab === "cypher" && (
          <>
            {query?.query_type === "opencypher" && query.query ? (
              <SyntaxHighlighter language="cypher" style={oneLight} className="rounded text-xs">
                {query.query}
              </SyntaxHighlighter>
            ) : (
              <p className="text-gray-400">해당 데이터가 없습니다</p>
            )}
          </>
        )}

        {activeTab === "result" && (
          <>
            {exec ? (
              <div>
                <p className="font-medium mb-1">{exec.result_summary}</p>
                <pre className="bg-gray-50 rounded p-2 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(exec.raw_data, null, 2)?.slice(0, 2000)}
                </pre>
              </div>
            ) : (
              <p className="text-gray-400">해당 데이터가 없습니다</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
