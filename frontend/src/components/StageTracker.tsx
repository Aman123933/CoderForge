import React from "react";

export type PipelineStage = "idle" | "intent" | "plan" | "architecture" | "code" | "review" | "run" | "completed";

interface StageTrackerProps {
  currentStage: PipelineStage;
  activeAttempt?: number;
  maxAttempts?: number;
}

const STAGES: Array<{ id: PipelineStage; label: string; agent: string }> = [
  { id: "intent", label: "Intent", agent: "IntentAgent" },
  { id: "plan", label: "Plan", agent: "PlannerAgent" },
  { id: "architecture", label: "Architecture", agent: "ArchitectAgent" },
  { id: "code", label: "Code", agent: "CoderAgent" },
  { id: "review", label: "Review", agent: "ReviewerAgent" },
  { id: "run", label: "Run", agent: "SafeExecutor" },
];

export const StageTracker: React.FC<StageTrackerProps> = ({
  currentStage,
  activeAttempt = 1,
  maxAttempts = 3,
}) => {
  const getStageStatus = (stageId: PipelineStage) => {
    const stageOrder: PipelineStage[] = ["intent", "plan", "architecture", "code", "review", "run", "completed"];
    const currentIndex = stageOrder.indexOf(currentStage);
    const thisIndex = stageOrder.indexOf(stageId);

    if (currentStage === "completed") return "completed";
    if (thisIndex < currentIndex) return "completed";
    if (thisIndex === currentIndex) return "active";
    return "pending";
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400" />
          Multi-Agent Pipeline Progression
        </h3>
        {activeAttempt > 1 && (
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
            Self-Correction Attempt {activeAttempt} of {maxAttempts}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-6 gap-2 relative">
        {STAGES.map((s, idx) => {
          const status = getStageStatus(s.id);
          const isActive = status === "active";
          const isCompleted = status === "completed";

          return (
            <div
              key={s.id}
              className={`p-3 rounded-lg border transition-all flex flex-col justify-between ${
                isActive
                  ? "bg-cyan-950/40 border-cyan-500/80 shadow-md shadow-cyan-500/10 ring-1 ring-cyan-500/30"
                  : isCompleted
                  ? "bg-slate-950 border-emerald-500/40 text-slate-300"
                  : "bg-slate-950/60 border-slate-800 text-slate-500"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-mono font-bold text-slate-500">
                  0{idx + 1}
                </span>
                {isCompleted ? (
                  <span className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs font-bold">
                    ✓
                  </span>
                ) : isActive ? (
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500"></span>
                  </span>
                ) : (
                  <span className="w-2 h-2 rounded-full bg-slate-700" />
                )}
              </div>

              <div>
                <div
                  className={`text-sm font-semibold ${
                    isActive ? "text-cyan-300" : isCompleted ? "text-slate-100" : "text-slate-400"
                  }`}
                >
                  {s.label}
                </div>
                <div className="text-[11px] text-slate-500 truncate mt-0.5">
                  {s.agent}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
