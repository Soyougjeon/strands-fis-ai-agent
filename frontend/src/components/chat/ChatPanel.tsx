import { useRef, useEffect, useState } from "react";
import type { ChatMessage, AgentProcess, TotalMetrics, ExampleQueries } from "../../types";
import MarkdownRenderer from "../common/MarkdownRenderer";
import DynamicChart from "../visualization/DynamicChart";
import InlineAgentProcess from "./InlineAgentProcess";

interface Props {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSend: (message: string) => void;
  examples: ExampleQueries | null;
  currentProcess: Partial<AgentProcess>;
  currentTotal: TotalMetrics | null;
  showProcess: boolean;
  onToggleProcess: () => void;
}

const WELCOME_QUESTIONS = [
  "TIGER ETF 중 AUM이 가장 큰 상위 5개는?",
  "반도체 ETF 보유종목 비교해줘",
  "AAA 등급 채권 목록 보여줘",
  "주식형 펀드 수익률 상위 10개는?",
  "ETF 투자 전략에 대해 설명해줘",
  "채권 금리와 가격의 관계는?",
];

export default function ChatPanel({
  messages,
  isStreaming,
  onSend,
  examples,
  currentProcess,
  currentTotal,
  showProcess,
  onToggleProcess,
}: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Gather some example questions from the API or fallback
  const exampleQuestions: string[] = [];
  if (examples?.domains) {
    for (const tools of Object.values(examples.domains)) {
      for (const queries of Object.values(tools)) {
        for (const q of queries) {
          if (exampleQuestions.length < 6) exampleQuestions.push(q.question);
        }
      }
    }
  }
  if (exampleQuestions.length === 0) {
    exampleQuestions.push(...WELCOME_QUESTIONS);
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center mt-16 px-4">
            <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center mb-4">
              <span className="text-2xl text-orange-600">M</span>
            </div>
            <h2 className="text-lg font-semibold text-gray-800 mb-1">
              미래에셋증권
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              금융 데이터 AI Agent입니다. 무엇이든 질문하세요.
            </p>
            <div className="grid grid-cols-2 gap-2 max-w-lg w-full">
              {exampleQuestions.slice(0, 6).map((q, i) => (
                <button
                  key={i}
                  onClick={() => onSend(q)}
                  className="text-left px-3 py-2.5 border border-gray-200 rounded-lg text-xs text-gray-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={msg.id}>
            <div
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-blue-500 text-white"
                    : "bg-white border border-gray-200"
                }`}
              >
                {msg.role === "user" ? (
                  <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                ) : (
                  <div className="prose prose-sm max-w-none">
                    <MarkdownRenderer content={msg.content} />
                    {msg.chartData && <DynamicChart data={msg.chartData} />}
                  </div>
                )}
              </div>
            </div>
            {/* Inline agent process for completed messages */}
            {msg.role === "assistant" && msg.agentProcess && showProcess && (
              <div className="ml-0 mt-1 mb-2">
                <InlineAgentProcess
                  process={msg.agentProcess}
                  total={msg.total || null}
                  isStreaming={false}
                />
              </div>
            )}
          </div>
        ))}

        {/* Streaming agent process for current message */}
        {isStreaming && showProcess && Object.keys(currentProcess).length > 0 && (
          <div className="ml-0 mt-1 mb-2">
            <InlineAgentProcess
              process={currentProcess}
              total={currentTotal}
              isStreaming={isStreaming}
            />
          </div>
        )}

        {/* Typing indicator */}
        {isStreaming && messages.length > 0 && !messages[messages.length - 1]?.content && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg px-4 py-3 flex items-center gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t bg-white p-3">
        <div className="flex items-center gap-2">
          <button
            onClick={onToggleProcess}
            className={`px-2 py-2 rounded text-xs font-medium transition-colors ${
              showProcess
                ? "bg-blue-100 text-blue-700"
                : "bg-gray-100 text-gray-500"
            }`}
            title={showProcess ? "Agent Process 숨기기" : "Agent Process 보기"}
          >
            AP
          </button>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="메시지를 입력하세요..."
            rows={1}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isStreaming}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            전송
          </button>
        </div>
      </div>
    </div>
  );
}
