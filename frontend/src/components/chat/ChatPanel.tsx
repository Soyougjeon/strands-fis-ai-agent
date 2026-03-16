import { useRef, useEffect, useState } from "react";
import type { ChatMessage, AgentProcess, TotalMetrics, ExampleQueries, GraphData } from "../../types";
import MarkdownRenderer from "../common/MarkdownRenderer";
import DynamicChart from "../visualization/DynamicChart";

interface Props {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSend: (message: string) => void;
  examples: ExampleQueries | null;
  currentProcess: Partial<AgentProcess>;
  currentTotal: TotalMetrics | null;
  showProcess: boolean;
  onToggleProcess: () => void;
  onViewGraph?: (graphData: GraphData, label: string) => void;
  onViewLexicalGraph?: (lexicalGraphData: GraphData, label: string) => void;
}

const WELCOME_QUESTIONS = [
  { label: "SQL", q: "TIGER ETF 중 AUM이 가장 큰 상위 5개를 알려줘" },
  { label: "RAG", q: "ETF 투자 전략에 대해 자세히 설명해줘" },
  { label: "GraphRAG", q: "TIGER 나스닥100과 글로벌리츠의 투자 특성의 공통점과 차이를 분석해줘" },
  { label: "openCypher", q: "TIGER 반도체와 보유 종목이 겹치는 ETF를 찾아줘" },
];

export default function ChatPanel({
  messages,
  isStreaming,
  onSend,
  examples,
  showProcess,
  onToggleProcess,
  onViewGraph,
  onViewLexicalGraph,
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

  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = async (text: string, msgId: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 1500);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center mt-16 px-4">
            <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center mb-4">
              <span className="text-2xl text-orange-600">A</span>
            </div>
            <h2 className="text-lg font-semibold text-gray-800 mb-1">
              A Securities
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              금융 데이터 AI Agent입니다. 무엇이든 질문하세요.
            </p>
            <div className="grid grid-cols-2 gap-2 max-w-2xl w-full">
              {WELCOME_QUESTIONS.map((item, i) => (
                <button
                  key={i}
                  onClick={() => onSend(item.q)}
                  className="text-left px-3 py-2.5 border border-gray-200 rounded-lg text-xs text-gray-600 hover:bg-orange-50 hover:border-orange-300 hover:text-orange-700 transition-colors"
                >
                  <span className="inline-block px-1.5 py-0.5 rounded bg-gray-100 text-[10px] font-medium text-gray-500 mr-1.5">{item.label}</span>
                  {item.q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id}>
            {msg.role === "user" ? (
              /* User message: right-aligned with label */
              <div className="flex flex-col items-end gap-1">
                <span className="text-[10px] text-gray-400 mr-1">Q</span>
                <div className="bg-orange-50 border border-orange-200 text-gray-900 rounded-lg px-4 py-2.5 max-w-[75%]">
                  <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                </div>
              </div>
            ) : (
              /* Assistant message: full width with label and background */
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between px-1">
                  <div className="flex items-center gap-1.5">
                    <div className="w-5 h-5 rounded-full bg-orange-500 flex items-center justify-center">
                      <span className="text-[10px] font-bold text-white">A</span>
                    </div>
                    <span className="text-[10px] text-gray-400">AI Agent</span>
                  </div>
                  <button
                    onClick={() => handleCopy(msg.content, msg.id)}
                    className="p-1 text-gray-300 hover:text-gray-500 transition-colors"
                    title="답변 복사"
                  >
                    {copiedId === msg.id ? (
                      <svg className="w-3.5 h-3.5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    )}
                  </button>
                </div>
                <div className="ml-6 bg-gray-50 border border-gray-100 rounded-lg px-4 py-3">
                  <div className="prose prose-sm max-w-none">
                    <MarkdownRenderer content={msg.content} />
                    {msg.chartData && <DynamicChart data={msg.chartData} />}
                  </div>
                  {/* Graph links - below the answer */}
                  {((msg.graphData && msg.graphData.nodes.length > 0) || (msg.lexicalGraphData && msg.lexicalGraphData.nodes.length > 0)) && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {/* Entity Graph link */}
                      {msg.graphData && msg.graphData.nodes.length > 0 && onViewGraph && (
                        <button
                          onClick={() => onViewGraph(msg.graphData!, msg.content.slice(0, 30))}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-orange-50 border border-orange-200 rounded-lg text-xs text-orange-700 hover:bg-orange-100 transition-colors"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <circle cx="6" cy="6" r="2.5" strokeWidth="1.5"/>
                            <circle cx="18" cy="6" r="2.5" strokeWidth="1.5"/>
                            <circle cx="12" cy="18" r="2.5" strokeWidth="1.5"/>
                            <path d="M8 7.5L10.5 16M16 7.5L13.5 16" strokeWidth="1.5"/>
                          </svg>
                          Entity Graph 보기
                          <span className="text-orange-400">
                            ({msg.graphData.nodes.length}개 노드, {msg.graphData.edges.length}개 관계)
                          </span>
                        </button>
                      )}
                      {/* Lexical Graph link - independent of entity graph */}
                      {msg.lexicalGraphData && msg.lexicalGraphData.nodes.length > 0 && onViewLexicalGraph && (() => {
                        const sources = msg.lexicalGraphData!.nodes.filter(n => n.type === "Source").length;
                        const statements = msg.lexicalGraphData!.nodes.filter(n => n.type === "Statement").length;
                        return (
                          <button
                            onClick={() => onViewLexicalGraph(msg.lexicalGraphData!, msg.content.slice(0, 30))}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-50 border border-purple-200 rounded-lg text-xs text-purple-700 hover:bg-purple-100 transition-colors"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"/>
                            </svg>
                            Lexical Graph 보기
                            <span className="text-purple-400">
                              ({sources}개 문서 / {statements}개 statements)
                            </span>
                          </button>
                        );
                      })()}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Processing indicator */}
        {isStreaming && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg px-4 py-2.5 flex items-center gap-2">
              <span className="inline-block w-3.5 h-3.5 border-2 border-orange-400 border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-gray-500">답변 준비 중</span>
              <span className="flex items-center gap-0.5">
                <span className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </span>
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
                ? "bg-orange-100 text-orange-700"
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
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-orange-400"
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isStreaming}
            className="bg-orange-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            전송
          </button>
        </div>
      </div>
    </div>
  );
}
