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
}

export default function Sidebar({
  open,
  onToggle,
  conversations,
  currentSessionId,
  examples,
  onSelectConversation,
  onNewConversation,
  onSelectExample,
}: Props) {
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null);

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

  return (
    <div className="w-[250px] bg-gray-50 border-r flex flex-col h-full">
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

      {/* New conversation */}
      <button
        onClick={onNewConversation}
        className="mx-3 mt-2 px-3 py-2 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
      >
        + 새 대화
      </button>

      {/* Conversation history */}
      <div className="flex-1 overflow-y-auto mt-3">
        <p className="px-3 text-xs font-medium text-gray-500 mb-1">
          대화 이력
        </p>
        {conversations.length === 0 && (
          <p className="px-3 text-xs text-gray-400">대화 이력이 없습니다</p>
        )}
        {conversations.map((conv) => (
          <button
            key={conv.session_id}
            onClick={() => onSelectConversation(conv.session_id)}
            className={`w-full text-left px-3 py-2 text-xs truncate hover:bg-gray-100 ${
              conv.session_id === currentSessionId
                ? "bg-blue-50 font-semibold text-blue-700"
                : "text-gray-600"
            }`}
          >
            {conv.title || "제목 없음"}
            <span className="block text-gray-400 text-[10px]">
              {conv.turn_count}턴 &middot; {conv.last_intent}
            </span>
          </button>
        ))}

        {/* Example queries */}
        {examples && Object.keys(examples.domains).length > 0 && (
          <>
            <div className="border-t my-2" />
            <p className="px-3 text-xs font-medium text-gray-500 mb-1">
              예시 쿼리
            </p>
            {Object.entries(examples.domains).map(([domain, tools]) => (
              <div key={domain}>
                <button
                  onClick={() =>
                    setExpandedDomain(
                      expandedDomain === domain ? null : domain
                    )
                  }
                  className="w-full text-left px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100"
                >
                  {expandedDomain === domain ? "▾" : "▸"} {domain}
                </button>
                {expandedDomain === domain &&
                  Object.entries(tools).map(([tool, queries]) => (
                    <div key={tool} className="pl-5">
                      <p className="text-[10px] text-gray-400 mt-1">{tool}</p>
                      {queries.map((q, i) => (
                        <button
                          key={i}
                          onClick={() => onSelectExample(q.question)}
                          className="w-full text-left px-2 py-1 text-xs text-gray-600 hover:bg-blue-50 hover:text-blue-600 truncate"
                          title={q.question}
                        >
                          {q.question}
                        </button>
                      ))}
                    </div>
                  ))}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
