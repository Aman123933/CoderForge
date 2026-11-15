import React, { useState } from "react";

interface FileViewerProps {
  files: Record<string, string>;
  entrypoint?: string;
}

export const FileViewer: React.FC<FileViewerProps> = ({ files, entrypoint = "main.py" }) => {
  const filePaths = Object.keys(files);
  const [selectedFile, setSelectedFile] = useState<string>(
    filePaths.includes(entrypoint) ? entrypoint : filePaths[0] || ""
  );
  const [copied, setCopied] = useState(false);

  if (filePaths.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500">
        No generated project files available yet.
      </div>
    );
  }

  const currentContent = files[selectedFile] || "";

  const handleCopy = () => {
    navigator.clipboard.writeText(currentContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col md:flex-row border border-slate-800 rounded-xl overflow-hidden bg-slate-950 min-h-[460px]">
      {/* File Tree Left Sidebar */}
      <div className="w-full md:w-64 border-b md:border-b-0 md:border-r border-slate-800 bg-slate-900/70 p-3 flex flex-col">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 px-2 py-1.5 mb-1 flex items-center justify-between">
          <span>Project Files ({filePaths.length})</span>
        </div>
        <div className="space-y-0.5 overflow-y-auto flex-1">
          {filePaths.map((path) => {
            const isSelected = path === selectedFile;
            const isEntry = path === entrypoint;

            return (
              <button
                key={path}
                onClick={() => setSelectedFile(path)}
                className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs font-mono transition-colors flex items-center justify-between group ${
                  isSelected
                    ? "bg-cyan-500/15 text-cyan-300 font-semibold border border-cyan-500/30"
                    : "text-slate-300 hover:bg-slate-800/60"
                }`}
              >
                <span className="truncate flex items-center gap-1.5">
                  <span className="text-slate-500 group-hover:text-slate-400">📄</span>
                  {path}
                </span>
                {isEntry && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                    main
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Code Display Area */}
      <div className="flex-1 flex flex-col bg-slate-950">
        <div className="px-4 py-2.5 border-b border-slate-800/80 bg-slate-900/40 flex items-center justify-between text-xs">
          <span className="font-mono text-slate-300 font-medium">
            {selectedFile}
          </span>
          <button
            onClick={handleCopy}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex items-center gap-1.5"
          >
            {copied ? "✓ Copied" : "Copy Code"}
          </button>
        </div>

        <div className="flex-1 p-4 overflow-auto font-mono text-xs text-slate-200 leading-relaxed">
          <pre>
            <code>
              {currentContent.split("\n").map((line, idx) => (
                <div key={idx} className="table-row">
                  <span className="table-cell pr-4 select-none text-slate-600 text-right w-8">
                    {idx + 1}
                  </span>
                  <span className="table-cell">{line}</span>
                </div>
              ))}
            </code>
          </pre>
        </div>
      </div>
    </div>
  );
};
