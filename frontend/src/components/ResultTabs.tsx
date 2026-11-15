import React, { useState } from "react";
import { PipelineResult } from "@/api/client";
import { FileViewer } from "./FileViewer";

interface ResultTabsProps {
  result: PipelineResult;
}

type TabType = "intent" | "plan" | "architecture" | "files" | "review" | "execution";

export const ResultTabs: React.FC<ResultTabsProps> = ({ result }) => {
  const [activeTab, setActiveTab] = useState<TabType>("files");

  const files = result.project || result.files || {};
  const issues = result.review?.issues || [];
  const exec = result.execution;

  const tabs: Array<{ id: TabType; label: string; badge?: string | number }> = [
    { id: "intent", label: "Intent" },
    { id: "plan", label: "Plan" },
    { id: "architecture", label: "Architecture" },
    { id: "files", label: "Files", badge: Object.keys(files).length },
    { id: "review", label: "Review Issues", badge: issues.length },
    {
      id: "execution",
      label: "Execution Output",
      badge: exec ? (exec.success ? "Pass" : "Fail") : undefined,
    },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      {/* Tab Navigation */}
      <div className="flex border-b border-slate-800 bg-slate-900/80 px-3 pt-2 overflow-x-auto gap-1">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 rounded-t-lg text-xs font-medium transition-all whitespace-nowrap flex items-center gap-2 border-t-2 ${
                isActive
                  ? "bg-slate-950 text-cyan-300 border-cyan-400 font-semibold"
                  : "text-slate-400 hover:text-slate-200 border-transparent hover:bg-slate-800/40"
              }`}
            >
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                    tab.id === "execution"
                      ? tab.badge === "Pass"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-red-500/20 text-red-400"
                      : "bg-slate-800 text-slate-300"
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content Panes */}
      <div className="p-6">
        {/* INTENT TAB */}
        {activeTab === "intent" && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-slate-200">Structured User Intent</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg space-y-2">
                <div className="text-xs text-slate-500 font-medium uppercase">Application Type</div>
                <div className="text-base font-semibold text-cyan-300">
                  {result.intent?.app_type?.toUpperCase() || "WEB"}
                </div>
                <div className="text-xs text-slate-400 mt-2">
                  Backend Required:{" "}
                  <span className="font-semibold text-slate-200">
                    {result.intent?.backend_required ? "Yes" : "No"}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  Frontend Required:{" "}
                  <span className="font-semibold text-slate-200">
                    {result.intent?.frontend_required ? "Yes" : "No"}
                  </span>
                </div>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg space-y-2">
                <div className="text-xs text-slate-500 font-medium uppercase">Extracted Features</div>
                <ul className="text-xs space-y-1.5 text-slate-300">
                  {(result.intent?.features || []).map((f: string, i: number) => (
                    <li key={i} className="flex items-center gap-2">
                      <span className="text-cyan-400 font-bold">•</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <pre className="bg-slate-950 border border-slate-800 p-4 rounded-lg text-xs font-mono text-slate-300 overflow-auto max-h-60">
              {JSON.stringify(result.intent, null, 2)}
            </pre>
          </div>
        )}

        {/* PLAN TAB */}
        {activeTab === "plan" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-slate-200">
                Ordered Execution Plan: {result.plan?.project_name || "CodeForge Project"}
              </h4>
            </div>
            <div className="space-y-2.5">
              {(result.plan?.steps || []).map((step: string, idx: number) => (
                <div
                  key={idx}
                  className="bg-slate-950 border border-slate-800/80 p-3.5 rounded-lg flex items-start gap-3"
                >
                  <span className="w-6 h-6 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <div className="text-xs text-slate-200 leading-relaxed pt-0.5">
                    {step}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ARCHITECTURE TAB */}
        {activeTab === "architecture" && (
          <div className="space-y-5">
            <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg space-y-1.5">
              <div className="text-xs text-slate-500 font-medium uppercase">System Overview</div>
              <p className="text-sm text-slate-200 leading-relaxed">
                {result.architecture?.system_overview || "No overview provided"}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg space-y-2">
                <div className="text-xs text-slate-500 font-medium uppercase">Components</div>
                <div className="space-y-1">
                  {(result.architecture?.backend_components || []).map((c: string, i: number) => (
                    <div key={i} className="text-xs text-slate-300 flex items-center gap-2">
                      <span className="text-blue-400">⚙</span>
                      <span>{c}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg space-y-2">
                <div className="text-xs text-slate-500 font-medium uppercase">Data Models</div>
                <div className="space-y-1">
                  {(result.architecture?.data_models || []).map((m: string, i: number) => (
                    <div key={i} className="text-xs text-slate-300 flex items-center gap-2">
                      <span className="text-emerald-400">📦</span>
                      <span>{m}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* FILES TAB */}
        {activeTab === "files" && (
          <FileViewer
            files={files}
            entrypoint={result.manifest?.entrypoint || "main.py"}
          />
        )}

        {/* REVIEW ISSUES TAB */}
        {activeTab === "review" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-slate-200">
                Code Review Summary: {result.review?.summary || "Review complete"}
              </h4>
              <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300">
                Total Issues: {issues.length}
              </span>
            </div>

            {issues.length === 0 ? (
              <div className="p-8 text-center bg-slate-950 border border-emerald-500/30 rounded-xl space-y-2">
                <span className="text-3xl">🎉</span>
                <p className="text-sm font-semibold text-emerald-300">
                  Clean Code Review Passed
                </p>
                <p className="text-xs text-slate-400">
                  Reviewer reported no syntax, logical, or architectural blocking issues.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {issues.map((issue, idx) => {
                  const sev = issue.severity?.toLowerCase();
                  const badgeColor =
                    sev === "critical"
                      ? "bg-red-500/20 text-red-400 border-red-500/30"
                      : sev === "major"
                      ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                      : "bg-blue-500/20 text-blue-400 border-blue-500/30";

                  return (
                    <div
                      key={idx}
                      className="bg-slate-950 border border-slate-800 p-4 rounded-lg space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${badgeColor}`}
                        >
                          {issue.severity}
                        </span>
                        <span className="text-xs font-mono text-slate-500">
                          {issue.location || "global"}
                        </span>
                      </div>
                      <p className="text-xs text-slate-200">{issue.description}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* EXECUTION OUTPUT TAB */}
        {activeTab === "execution" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-slate-200">
                Sandboxed Subprocess Execution Output
              </h4>
              {exec && (
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs px-2.5 py-1 rounded font-bold border ${
                      exec.success
                        ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                        : "bg-red-500/20 text-red-400 border-red-500/30"
                    }`}
                  >
                    {exec.success ? "Exit Code 0 (Success)" : `Exit Code ${exec.exit_code || 1} (Failed)`}
                  </span>
                  {exec.duration !== undefined && (
                    <span className="text-xs text-slate-500 font-mono">
                      {exec.duration}s
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-xs overflow-auto max-h-96 space-y-3">
              {exec ? (
                <>
                  <div>
                    <span className="text-slate-500 select-none">$ stdout:</span>
                    <pre className="text-emerald-300 mt-1 whitespace-pre-wrap">
                      {exec.output || "(No standard output generated)"}
                    </pre>
                  </div>
                  {exec.stderr && (
                    <div>
                      <span className="text-red-400 select-none">$ stderr:</span>
                      <pre className="text-red-300 mt-1 whitespace-pre-wrap">
                        {exec.stderr}
                      </pre>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-slate-500">
                  Execution was skipped or has not run yet.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
