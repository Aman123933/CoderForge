import React, { useState } from "react";
import Head from "next/head";
import { PromptInput } from "@/components/PromptInput";
import { StageTracker, PipelineStage } from "@/components/StageTracker";
import { ResultTabs } from "@/components/ResultTabs";
import { runPrompt, PipelineResult } from "@/api/client";

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [stage, setStage] = useState<PipelineStage>("idle");
  const [error, setError] = useState<string | null>(null);
  const [currentResult, setCurrentResult] = useState<PipelineResult | null>(null);

  const handleGenerate = async (prompt: string) => {
    setIsLoading(true);
    setError(null);
    setStage("intent");

    // Simulated progress stage transitions while backend processes
    const timer1 = setTimeout(() => setStage("plan"), 1200);
    const timer2 = setTimeout(() => setStage("architecture"), 2500);
    const timer3 = setTimeout(() => setStage("code"), 4000);
    const timer4 = setTimeout(() => setStage("review"), 6000);
    const timer5 = setTimeout(() => setStage("run"), 7500);

    try {
      const data = await runPrompt(prompt);
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
      clearTimeout(timer5);

      setCurrentResult(data.result);
      setStage("completed");
    } catch (err: any) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
      clearTimeout(timer5);

      setError(err.message || "An unexpected error occurred");
      setStage("idle");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Head>
        <title>CodeForge - Multi-Agent Autonomous Code Generation</title>
        <meta name="description" content="Autonomous multi-agent code generation pipeline" />
      </Head>

      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-white shadow-md shadow-cyan-500/20">
              CF
            </div>
            <div>
              <h1 className="font-bold text-lg text-slate-100 tracking-tight">CodeForge</h1>
              <p className="text-xs text-slate-400">Multi-Agent Code Generation Pipeline</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Backend Connected
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <PromptInput onGenerate={handleGenerate} isLoading={isLoading} />

        {stage !== "idle" && (
          <StageTracker
            currentStage={stage}
            activeAttempt={currentResult?.attempts?.length || 1}
            maxAttempts={3}
          />
        )}

        {error && (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/80 text-red-300 text-sm flex items-start gap-3">
            <span className="text-lg">⚠️</span>
            <div>
              <p className="font-semibold">Execution Error</p>
              <p className="text-red-400 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {currentResult && (
          <ResultTabs result={currentResult} />
        )}
      </main>
    </div>
  );
}

