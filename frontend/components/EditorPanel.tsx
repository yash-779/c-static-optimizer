"use client";
import dynamic from "next/dynamic";
import { Code2 } from "lucide-react";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

type Props = { code: string; onChange: (v: string) => void };

export default function EditorPanel({ code, onChange }: Props) {
  return (
    <div className="flex flex-col flex-1 min-h-0 border-b border-border-dim">
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#1f2937] shrink-0">
        <span className="text-[12px] font-bold text-white tracking-wide">C Input</span>
        <div className="flex gap-2">
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border border-blue-500/50 text-blue-400 bg-transparent">O1 Pass</span>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border border-pink-500/50 text-pink-400 bg-transparent">Analyze</span>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 min-h-0">
        <MonacoEditor
          height="100%"
          language="c"
          value={code}
          onChange={(v) => onChange(v || "")}
          theme="vs-dark"
          options={{
            fontSize: 12,
            fontFamily: "'JetBrains Mono', Consolas, monospace",
            fontLigatures: true,
            minimap: { enabled: false },
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            padding: { top: 8, bottom: 8 },
            renderLineHighlight: "line",
            smoothScrolling: true,
            cursorBlinking: "smooth",
            wordWrap: "on",
            overviewRulerLanes: 0,
            hideCursorInOverviewRuler: true,
            scrollbar: { verticalScrollbarSize: 4, horizontalScrollbarSize: 4 },
            glyphMargin: false,
            folding: true,
            lineDecorationsWidth: 8,
          }}
        />
      </div>
    </div>
  );
}
