import React, { useState } from "react";

interface PromptInputProps {
  onGenerate: (prompt: string) => void;
  isLoading: boolean;
}

export const PromptInput: React.FC<PromptInputProps> = ({ onGenerate, isLoading }) => {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    onGenerate(prompt.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const samplePrompts = [
    "Build a Task Manager CLI with CRUD, priorities, and JSON persistence.",
    "Build a URL Shortener service with hash encode/decode and stats.",
    "Build an Inventory Management API with stock tracking and valuation.",
    "Build a scientific Calculator with history log and power functions.",
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-semibold text-slate-300">
              Application Specification
            </label>
            <span className="text-xs text-slate-500">
              Press Ctrl+Enter or Cmd+Enter to run
            </span>
          </div>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe the application you want CodeForge to architect, generate, review, and execute..."
            rows={4}
            disabled={isLoading}
            className="w-full bg-slate-950 border border-slate-700/80 rounded-lg p-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all disabled:opacity-50"
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
            <span className="font-medium text-slate-500 mr-1">Try:</span>
            {samplePrompts.map((sp, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setPrompt(sp)}
                disabled={isLoading}
                className="px-2.5 py-1 bg-slate-800/80 hover:bg-slate-800 text-slate-300 rounded border border-slate-700/60 transition-colors"
              >
                {sp.split(" ")[1]} {sp.split(" ")[2]}
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={isLoading || !prompt.trim()}
            className="px-6 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium text-sm rounded-lg shadow-md hover:shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                <span>Generating Pipeline...</span>
              </>
            ) : (
              <>
                <span>Generate Project</span>
                <span className="text-cyan-200">→</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
