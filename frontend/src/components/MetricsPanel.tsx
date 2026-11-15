import React from "react";

interface MetricsPanelProps {
  metrics?: {
    run_id: string;
    prompt: string;
    per_agent_latency_ms: Record<string, number>;
    total_latency_ms: number;
    llm_calls: number;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    retries_used: number;
    execution_success: boolean;
    files_generated: number;
  };
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ metrics }) => {
  if (!metrics) return null;

  const agentLatencies = metrics.per_agent_latency_ms || {};
  const agents = ["intent", "planner", "architect", "coder", "reviewer", "runner"];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-400" />
          Run Instrumentation & Telemetry
        </h3>
        <span className="text-xs font-mono text-slate-500 truncate max-w-xs">
          Run ID: {metrics.run_id}
        </span>
      </div>

      {/* Top stats summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg">
          <div className="text-[11px] text-slate-500 font-medium">Total Latency</div>
          <div className="text-lg font-bold text-cyan-300 mt-0.5">
            {metrics.total_latency_ms ? `${(metrics.total_latency_ms / 1000).toFixed(2)}s` : "0.0s"}
          </div>
          <div className="text-[10px] text-slate-500">{metrics.total_latency_ms} ms</div>
        </div>

        <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg">
          <div className="text-[11px] text-slate-500 font-medium">LLM Token Usage</div>
          <div className="text-lg font-bold text-blue-300 mt-0.5">
            {metrics.total_tokens?.toLocaleString() || 0}
          </div>
          <div className="text-[10px] text-slate-500">
            {metrics.input_tokens || 0} in / {metrics.output_tokens || 0} out
          </div>
        </div>

        <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg">
          <div className="text-[11px] text-slate-500 font-medium">Self-Correction Retries</div>
          <div className="text-lg font-bold text-amber-300 mt-0.5">
            {metrics.retries_used || 0}
          </div>
          <div className="text-[10px] text-slate-500">Max limit: 3</div>
        </div>

        <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg">
          <div className="text-[11px] text-slate-500 font-medium">Files Generated</div>
          <div className="text-lg font-bold text-purple-300 mt-0.5">
            {metrics.files_generated || 0}
          </div>
          <div className="text-[10px] text-slate-500">Modular structure</div>
        </div>

        <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg">
          <div className="text-[11px] text-slate-500 font-medium">Execution Status</div>
          <div
            className={`text-lg font-bold mt-0.5 ${
              metrics.execution_success ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            {metrics.execution_success ? "Success (0)" : "Non-zero / Skipped"}
          </div>
          <div className="text-[10px] text-slate-500">Subprocess sandbox</div>
        </div>
      </div>

      {/* Per-agent latency breakdown bars */}
      <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg space-y-2.5">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Per-Agent Latency Distribution
        </div>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          {agents.map((ag) => {
            const lat = agentLatencies[ag] || 0;
            return (
              <div key={ag} className="bg-slate-900/80 p-2.5 rounded border border-slate-800/80">
                <div className="text-[11px] text-slate-400 capitalize font-medium">{ag}</div>
                <div className="text-sm font-bold text-slate-200 mt-0.5">{lat} ms</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
