import { useState } from "react";
import type { ConversationSummary, ExampleQueries } from "../../types";

interface Props {
  open: boolean;
  onToggle: () => void;
  conversations: ConversationSummary[];
  currentSessionId: string | null;
  examples: ExampleQueries | null;
  onSelectConversation: (sessionId: string) => void;
  onNewConversation: () => void;
  onSelectExample: (question: string) => void;
  onDeleteConversation: (sessionId: string) => void;
}

type SidebarTab = "history" | "ETF" | "Bond" | "Fund";

const DOMAIN_TABS: { key: SidebarTab; label: string }[] = [
  { key: "history", label: "대화 이력" },
  { key: "ETF", label: "ETF" },
  { key: "Bond", label: "채권" },
  { key: "Fund", label: "펀드" },
];

const TOOL_LABELS: Record<string, string> = {
  text2sql: "SQL",
  rag: "RAG",
  graphrag: "GraphRAG",
  opencypher: "OpenCypher",
};

export default function Sidebar({
  open,
  onToggle,
  conversations,
  currentSessionId,
  examples,
  onSelectConversation,
  onNewConversation,
  onSelectExample,
  onDeleteConversation,
}: Props) {
  const [activeTab, setActiveTab] = useState<SidebarTab>("history");

  if (!open) {
    return (
      <div className="w-10 bg-gray-50 border-r flex flex-col items-center py-2">
        <button
          onClick={onToggle}
          className="text-gray-500 hover:text-gray-700 text-lg"
          title="사이드바 열기"
        >
          &#9776;
        </button>
      </div>
    );
  }

  const domainExamples = examples?.domains || {};

  return (
    <div className="w-[260px] bg-gray-50 border-r flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b">
        <span className="text-sm font-semibold text-gray-700">메뉴</span>
        <button
          onClick={onToggle}
          className="text-gray-400 hover:text-gray-600 text-sm"
        >
          &#10005;
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b bg-white">
        {DOMAIN_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 px-1 py-2 text-[11px] font-medium transition-colors ${
              activeTab === tab.key
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "history" && (
          <div>
            {/* New conversation */}
            <button
              onClick={onNewConversation}
              className="w-full mx-0 mt-2 mb-1 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 font-medium text-left"
            >
              + 새 대화
            </button>
            <div className="border-t" />

            {conversations.length === 0 && (
              <p className="px-3 py-4 text-xs text-gray-400 text-center">
                대화 이력이 없습니다
              </p>
            )}
            {conversations.map((conv) => (
              <div
                key={conv.session_id}
                className={`group flex items-center hover:bg-gray-100 ${
                  conv.session_id === currentSessionId
                    ? "bg-blue-50"
                    : ""
                }`}
              >
                <button
                  onClick={() => onSelectConversation(conv.session_id)}
                  className={`flex-1 text-left px-3 py-2 text-xs truncate ${
                    conv.session_id === currentSessionId
                      ? "font-semibold text-blue-700"
                      : "text-gray-600"
                  }`}
                >
                  {conv.title || "제목 없음"}
                  <span className="block text-gray-400 text-[10px]">
                    {conv.turn_count}턴 &middot; {conv.last_intent}
                  </span>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(conv.session_id);
                  }}
                  className="hidden group-hover:block px-2 text-gray-400 hover:text-red-500 text-xs"
                  title="삭제"
                >
                  &#10005;
                </button>
              </div>
            ))}
          </div>
        )}

        {activeTab !== "history" && (
          <div className="py-2">
            {domainExamples[activeTab] ? (
              Object.entries(domainExamples[activeTab]).map(([tool, queries]) => (
                <div key={tool} className="mb-2">
                  <p className="px-3 py-1 text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                    {TOOL_LABELS[tool] || tool}
                  </p>
                  {queries.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => onSelectExample(q.question)}
                      className="w-full text-left px-3 py-1.5 text-xs text-gray-600 hover:bg-blue-50 hover:text-blue-600"
                      title={q.question}
                    >
                      <span className="line-clamp-2">{q.question}</span>
                      {q.description && (
                        <span className="block text-[10px] text-gray-400 mt-0.5 truncate">
                          {q.description}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              ))
            ) : (
              <p className="px-3 py-4 text-xs text-gray-400 text-center">
                예시 쿼리가 없습니다
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
