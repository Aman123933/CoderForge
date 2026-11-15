import React, { useEffect, useState } from "react";
import { fetchRuns, fetchRunById, RunRecord, PipelineResult } from "@/api/client";

interface RunHistoryProps {
  onSelectRun: (result: PipelineResult) => void;
  refreshTrigger?: number;
}

export const RunHistory: React.FC<RunHistoryProps> = ({ onSelectRun, refreshTrigger = 0 }) => {
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const loadRuns = async () => {
    setLoading(true);
    try {
      const data = await fetchRuns();
      setRuns(data);
    } catch (e) {
      // Backend may be offline during initial render
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRuns();
  }, [refreshTrigger]);

  const handleSelect = async (runId: string) => {
    setSelectedId(runId);
    try {
      const runData = await fetchRunById(runId);
      if (runData && runData.data) {
        onSelectRun({
          ...runData.data,
          metrics: runData.metrics || runData.data.metrics,
        });
      }
    } catch (err) {
      console.error("Failed to load run", err);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-purple-400" />
          Recent Execution History ({runs.length})
        </h3>
        <button
          onClick={loadRuns}
          disabled={loading}
          className="text-xs text-slate-400 hover:text-cyan-400 transition-colors disabled:opacity-50"
        >
          {loading ? "Refreshing..." : "↻ Refresh"}
        </button>
      </div>

      {runs.length === 0 ? (
        <div className="p-6 text-center text-xs text-slate-500">
          No past runs found in the database. Run your first prompt above!
        </div>
      ) : (
        <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
          {runs.map((r) => {
            const isSelected = r.id === selectedId;
            const timeStr = new Date(r.created_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            });

            return (
              <button
                key={r.id}
                onClick={() => handleSelect(r.id)}
                className={`w-full text-left p-3 rounded-lg border text-xs transition-all flex items-center justify-between group ${
                  isSelected
                    ? "bg-slate-800 border-cyan-500/50 text-cyan-200"
                    : "bg-slate-950/80 border-slate-800/80 hover:bg-slate-800/40 text-slate-300"
                }`}
              >
                <div className="flex-1 truncate mr-3">
                  <div className="font-medium text-slate-200 truncate group-hover:text-cyan-300 transition-colors">
                    {r.prompt}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5 flex items-center gap-2">
                    <span>{timeStr}</span>
                    <span>•</span>
                    <span>{r.files_count || 1} files</span>
                    <span>•</span>
                    <span>{r.retries_used} retries</span>
                  </div>
                </div>

                <div className="shrink-0 flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      r.execution_success
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-amber-500/20 text-amber-400"
                    }`}
                  >
                    {r.execution_success ? "PASSED" : "FAILED"}
                  </span>
                  <span className="font-mono text-slate-500 text-[11px]">
                    {r.total_latency_ms ? `${(r.total_latency_ms / 1000).toFixed(1)}s` : "-"}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
