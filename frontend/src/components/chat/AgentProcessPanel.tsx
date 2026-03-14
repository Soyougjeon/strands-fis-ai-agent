import type { AgentProcess, TotalMetrics } from "../../types";

interface Props {
  process: Partial<AgentProcess>;
  total: TotalMetrics | null;
  isStreaming: boolean;
}

function StepRow({
  label,
  active,
  done,
  children,
}: {
  label: string;
  active: boolean;
  done: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="border-b border-gray-100 py-2 px-3">
      <div className="flex items-center gap-2 text-xs font-medium text-gray-600">
        {done ? (
          <span className="text-green-500">&#10003;</span>
        ) : active ? (
          <span className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin inline-block" />
        ) : (
          <span className="text-gray-300">&#9679;</span>
        )}
        {label}
      </div>
      {done && <div className="mt-1 text-xs text-gray-500">{children}</div>}
    </div>
  );
}

function MetricLine({
  latency,
  tokensIn,
  tokensOut,
  cost,
}: {
  latency: number;
  tokensIn: number;
  tokensOut: number;
  cost: number;
}) {
  return (
    <span>
      {latency.toFixed(3)}s &middot; {tokensIn.toLocaleString()}+
      {tokensOut.toLocaleString()} tok &middot; $
      {cost.toFixed(6)}
    </span>
  );
}

export default function AgentProcessPanel({
  process,
  total,
  isStreaming,
}: Props) {
  const intent = process.intent_detection;
  const tool = process.tool_selection;
  const query = process.query_generation;
  const exec = process.query_execution;
  const resp = process.response_generation;

  return (
    <div className="h-full overflow-y-auto bg-gray-50 border-l border-gray-200">
      <div className="px-3 py-2 border-b bg-white">
        <h3 className="text-sm font-semibold text-gray-700">Agent Process</h3>
      </div>

      <StepRow label="Intent Detection" done={!!intent} active={isStreaming && !intent}>
        {intent && (
          <>
            <span className="inline-block bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-medium mr-1">
              {(intent as Record<string, unknown>).intent as string}
            </span>
            <span className="text-gray-400">
              ({((intent as Record<string, unknown>).confidence as number)?.toFixed(2)})
            </span>
            <br />
            <MetricLine
              latency={intent.latency}
              tokensIn={intent.tokens_in}
              tokensOut={intent.tokens_out}
              cost={intent.cost}
            />
          </>
        )}
      </StepRow>

      <StepRow label="Tool Selection" done={!!tool} active={isStreaming && !!intent && !tool}>
        {tool && (
          <>
            <span className="inline-block bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs font-medium mr-1">
              {(tool as Record<string, unknown>).tool as string}
            </span>
            <br />
            <span className="text-gray-400">
              {(tool as Record<string, unknown>).rationale as string}
            </span>
            <br />
            <MetricLine
              latency={tool.latency}
              tokensIn={tool.tokens_in}
              tokensOut={tool.tokens_out}
              cost={tool.cost}
            />
          </>
        )}
      </StepRow>

      <StepRow label="Query Generated" done={!!query} active={isStreaming && !!tool && !query}>
        {query && (
          <>
            <span className="text-gray-400">{query.query_type}</span>
            <br />
            <MetricLine
              latency={query.latency}
              tokensIn={query.tokens_in}
              tokensOut={query.tokens_out}
              cost={query.cost}
            />
          </>
        )}
      </StepRow>

      <StepRow label="Query Executed" done={!!exec} active={isStreaming && !!query && !exec}>
        {exec && (
          <>
            <span>{exec.result_summary}</span>
            <br />
            <span>{exec.latency.toFixed(3)}s</span>
          </>
        )}
      </StepRow>

      <StepRow
        label="Response Generation"
        done={!!resp}
        active={isStreaming && !!exec && !resp}
      >
        {resp && (
          <MetricLine
            latency={resp.latency}
            tokensIn={resp.tokens_in}
            tokensOut={resp.tokens_out}
            cost={resp.cost}
          />
        )}
      </StepRow>

      {total && (
        <div className="px-3 py-2 bg-white border-t mt-auto">
          <div className="text-xs font-semibold text-gray-700">
            Total: {total.latency.toFixed(3)}s &middot; $
            {total.cost.toFixed(6)}
          </div>
          <div className="text-xs text-gray-400">
            {total.tokens_in.toLocaleString()} in +{" "}
            {total.tokens_out.toLocaleString()} out
          </div>
        </div>
      )}
    </div>
  );
}
