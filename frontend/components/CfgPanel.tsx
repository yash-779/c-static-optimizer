"use client";
import { useEffect, useRef, useState } from "react";
import { ZoomIn, ZoomOut, Home, GitBranch, Loader2 } from "lucide-react";
import type { PipelineResult, Block } from "@/app/page";

type Props = {
  result: PipelineResult | null;
  cfgView: "before" | "after";
  setCfgView: (v: "before" | "after") => void;
  onBlockClick: (b: Block) => void;
  error: string | null;
  loading: boolean;
};

export default function CfgPanel({ result, cfgView, setCfgView, onBlockClick, error, loading }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  const dot = cfgView === "before" ? result?.dot_before : result?.dot_after;

  // Inject SVG into the container
  useEffect(() => {
    if (!containerRef.current || !dot) return;
    // Use Graphviz via the backend's SVG output embedded in the DOT string response
    // We render through a hidden iframe/img approach using the dot string
    // Since we rely on the Flask backend for SVG, we request it
    (async () => {
      try {
        const resp = await fetch("/api/render_dot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dot }),
        });
        if (!resp.ok) return;
        const { svg } = await resp.json();
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
          const svgEl = containerRef.current.querySelector("svg");
          if (svgEl) {
            svgEl.style.width = "100%";
            svgEl.style.height = "100%";
            svgEl.removeAttribute("width");
            svgEl.removeAttribute("height");
            // Attach click handlers to nodes
            svgEl.querySelectorAll("[id^='node_']").forEach((node) => {
              const idStr = node.id.replace("node_", "");
              const bid = parseInt(idStr);
              const block = result?.blocks.find((b) => b.id === bid);
              if (block) {
                (node as SVGElement).style.cursor = "pointer";
                node.addEventListener("click", () => onBlockClick(block));
                node.addEventListener("mouseenter", () => {
                  (node as SVGElement).style.opacity = "0.8";
                });
                node.addEventListener("mouseleave", () => {
                  (node as SVGElement).style.opacity = "1";
                });
              }
            });
          }
        }
      } catch {
        // fallback: show raw SVG placeholder
      }
    })();
  }, [dot, result?.blocks, onBlockClick]);

  // Pan
  const onMouseDown = (e: React.MouseEvent) => {
    if ((e.target as Element).closest("[id^='node_']")) return;
    dragging.current = true;
    lastPos.current = { x: e.clientX, y: e.clientY };
  };
  const onMouseMove = (e: React.MouseEvent) => {
    if (!dragging.current) return;
    const dx = e.clientX - lastPos.current.x;
    const dy = e.clientY - lastPos.current.y;
    lastPos.current = { x: e.clientX, y: e.clientY };
    setTranslate((t) => ({ x: t.x + dx, y: t.y + dy }));
  };
  const onMouseUp = () => { dragging.current = false; };
  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setScale((s) => Math.max(0.2, Math.min(3, s - e.deltaY * 0.001)));
  };

  const resetView = () => { setScale(1); setTranslate({ x: 0, y: 0 }); };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#1f2937] shrink-0">
        <span className="text-[12px] font-bold text-white tracking-wide">Control Flow Graph</span>
        <div className="flex items-center gap-3">
          {/* Before / After toggle as pills */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCfgView("before")}
              className={`px-3 py-1 text-[10px] font-bold rounded-full transition-all border ${
                cfgView === "before"
                  ? "bg-slate-700/50 text-white border-slate-500"
                  : "bg-transparent text-slate-500 border-slate-700 hover:text-slate-300"
              }`}
            >
              Before Opt
            </button>
            <button
              onClick={() => setCfgView("after")}
              className={`px-3 py-1 text-[10px] font-bold rounded-full transition-all border ${
                cfgView === "after"
                  ? "bg-purple-900/40 text-purple-300 border-purple-500/50"
                  : "bg-transparent text-slate-500 border-slate-700 hover:text-slate-300"
              }`}
            >
              After Opt
            </button>
          </div>
          <div className="w-[1px] h-4 bg-white/10 mx-1" />
          {/* Zoom controls */}
          <div className="flex items-center gap-1">
            <button onClick={() => setScale((s) => Math.min(3, s + 0.2))} className="p-1 hover:bg-white/5 rounded text-slate-400 hover:text-white transition-all">
              <ZoomIn size={14} />
            </button>
            <button onClick={() => setScale((s) => Math.max(0.2, s - 0.2))} className="p-1 hover:bg-white/5 rounded text-slate-400 hover:text-white transition-all">
              <ZoomOut size={14} />
            </button>
            <button onClick={resetView} className="p-1 hover:bg-white/5 rounded text-slate-400 hover:text-white transition-all">
              <Home size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Canvas */}
      <div
        className="flex-1 min-h-0 overflow-hidden relative cursor-grab active:cursor-grabbing"
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onWheel={onWheel}
      >
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-bg-primary/80 z-10">
            <div className="flex flex-col items-center gap-3">
              <Loader2 size={32} className="text-purple-400 animate-spin" />
              <span className="text-sm text-slate-400 font-mono">Running optimization passes...</span>
            </div>
          </div>
        )}

        {error && !loading && (
          <div className="absolute inset-0 flex items-center justify-center z-10 p-8">
            <div className="bg-red-950/60 border border-red-700/50 rounded-lg p-4 max-w-md text-center">
              <div className="text-red-400 font-bold mb-2">Parse Error</div>
              <div className="text-red-300 text-sm font-mono whitespace-pre-wrap">{error}</div>
            </div>
          </div>
        )}

        {!result && !loading && !error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-8">
            <GitBranch size={48} className="text-slate-700 mb-4" />
            <div className="text-slate-500 text-sm">Paste your C code and click</div>
            <div className="text-purple-400 font-semibold mt-1">Run Pipeline</div>
            <div className="text-slate-600 text-xs mt-2 font-mono">to generate the Control Flow Graph</div>
          </div>
        )}

        <div
          className="w-full h-full cfg-svg-container"
          style={{ transform: `translate(${translate.x}px, ${translate.y}px) scale(${scale})`, transformOrigin: "center center", transition: dragging.current ? "none" : "transform 0.1s" }}
          ref={containerRef}
        />
      </div>
    </div>
  );
}
