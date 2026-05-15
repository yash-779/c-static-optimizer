"use client";
import { X, ArrowRight, Tag, Activity } from "lucide-react";
import type { Block } from "@/app/page";

type PassOption = { id: string; label: string; color: string; badge: string };

type Props = {
  block: Block;
  onClose: () => void;
  passOptions: PassOption[];
};

const OPT_STYLES: Record<string, { bg: string; text: string; badge: string }> = {
  Folded:     { bg: "bg-amber-900/40",   text: "text-amber-300",   badge: "⚡ FOLD" },
  Propagated: { bg: "bg-emerald-900/40", text: "text-emerald-300", badge: "→ PROP" },
  Removed:    { bg: "bg-red-900/40",     text: "text-red-300",     badge: "✂ DCE"  },
  Moved:      { bg: "bg-purple-900/40",  text: "text-purple-300",  badge: "⬆ LICM" },
};

export default function BlockExplorer({ block, onClose }: Props) {
  return (
    <div className="flex flex-col flex-1 min-h-0 slide-in">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-border-dim bg-bg-secondary shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-purple-800/60 border border-purple-600/50 flex items-center justify-center">
            <span className="text-[9px] font-bold text-purple-300">{block.id}</span>
          </div>
          <div>
            <div className="text-[12px] font-bold text-white">Block {block.id}</div>
            <div className="text-[10px] text-purple-400 font-mono">[{block.label}]</div>
          </div>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-bg-card rounded text-slate-500 hover:text-white transition-all">
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto min-h-0 p-3 space-y-3">
        {/* Before Instructions */}
        {block.before_instructions.length > 0 && (
          <InstrSection title="Before Optimization" color="text-slate-400" borderColor="border-slate-700">
            {block.before_instructions.map((instr, i) => (
              <div key={i} className="font-mono text-[11px] text-slate-400 py-0.5">{instr}</div>
            ))}
          </InstrSection>
        )}

        {/* Transformations */}
        {block.optimizations.length > 0 && (
          <InstrSection title="Transformations Applied" color="text-amber-400" borderColor="border-amber-800/50">
            {block.optimizations.map((opt, i) => {
              const style = OPT_STYLES[opt.type || ""] || { bg: "bg-slate-800/40", text: "text-slate-300", badge: opt.type };
              return (
                <div key={i} className={`flex items-start gap-2 py-1 px-2 rounded ${style.bg} border border-transparent mb-1`}>
                  <span className={`text-[9px] font-bold shrink-0 mt-0.5 ${style.text}`}>{style.badge}</span>
                  <div className="min-w-0">
                    {opt.original && (
                      <div className="text-[10px] text-slate-500 font-mono line-through truncate">{opt.original}</div>
                    )}
                    <div className={`text-[11px] font-mono ${style.text}`}>{opt.text}</div>
                  </div>
                </div>
              );
            })}
          </InstrSection>
        )}

        {/* After Instructions */}
        <InstrSection title="Optimized Code" color="text-emerald-400" borderColor="border-emerald-800/50">
          {block.instructions.length === 0 ? (
            <div className="text-[11px] text-slate-600 italic font-mono">(empty — block removed)</div>
          ) : (
            block.instructions.map((instr, i) => {
              const style = instr.type ? (OPT_STYLES[instr.type] || {}) : {};
              return (
                <div key={i} className={`flex items-center gap-2 py-0.5 ${instr.type ? (style as {bg?: string}).bg || "" : ""}`}>
                  {instr.type && (
                    <span className={`text-[9px] font-bold shrink-0 ${(style as {text?: string}).text || "text-slate-400"}`}>
                      {(style as {badge?: string}).badge || instr.type}
                    </span>
                  )}
                  <span className={`font-mono text-[11px] ${instr.type ? (style as {text?: string}).text || "text-slate-300" : "text-sky-200"}`}>
                    {instr.text}
                  </span>
                </div>
              );
            })
          )}
        </InstrSection>

        {/* CFG Edges */}
        <InstrSection title="CFG Edges" color="text-cyan-400" borderColor="border-cyan-800/50">
          <div className="space-y-1">
            {block.edges.filter(e => e.to !== undefined).map((edge, i) => (
              <EdgePill key={i} direction="to" blockId={edge.to!} kind={edge.kind} />
            ))}
            {block.edges.filter(e => e.from !== undefined).map((edge, i) => (
              <EdgePill key={`f${i}`} direction="from" blockId={edge.from!} kind={edge.kind} />
            ))}
            {block.edges.length === 0 && (
              <div className="text-[11px] text-slate-600 italic font-mono">No edges</div>
            )}
          </div>
        </InstrSection>

        {/* Live Variables */}
        <InstrSection title="Live Variables" color="text-purple-400" borderColor="border-purple-800/50">
          <div className="space-y-2">
            <div>
              <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                <Tag size={9} /> Live-In
              </div>
              <div className="flex flex-wrap gap-1">
                {block.lv_in.length === 0
                  ? <span className="text-[10px] text-slate-600 italic">∅ (empty)</span>
                  : block.lv_in.map((v, i) => (
                    <span key={i} className="text-[10px] font-mono bg-emerald-900/40 text-emerald-300 border border-emerald-700/40 px-1.5 py-0.5 rounded">{v}</span>
                  ))
                }
              </div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                <Activity size={9} /> Live-Out
              </div>
              <div className="flex flex-wrap gap-1">
                {block.lv_out.length === 0
                  ? <span className="text-[10px] text-slate-600 italic">∅ (empty)</span>
                  : block.lv_out.map((v, i) => (
                    <span key={i} className="text-[10px] font-mono bg-sky-900/40 text-sky-300 border border-sky-700/40 px-1.5 py-0.5 rounded">{v}</span>
                  ))
                }
              </div>
            </div>
          </div>
        </InstrSection>
      </div>
    </div>
  );
}

const EDGE_COLORS: Record<string, string> = {
  true: "text-emerald-400 border-emerald-700/50 bg-emerald-900/30",
  false: "text-red-400 border-red-700/50 bg-red-900/30",
  back: "text-purple-400 border-purple-700/50 bg-purple-900/30",
  fall: "text-slate-400 border-slate-700/50 bg-slate-800/30",
  return: "text-amber-400 border-amber-700/50 bg-amber-900/30",
};

function EdgePill({ direction, blockId, kind }: { direction: "to" | "from"; blockId: number; kind: string }) {
  const cls = EDGE_COLORS[kind] || "text-slate-400 border-slate-700/50 bg-slate-800/30";
  return (
    <div className={`flex items-center gap-1.5 text-[10px] font-mono px-2 py-1 rounded border ${cls}`}>
      {direction === "from" && <span className="text-slate-500">←</span>}
      <ArrowRight size={10} className={direction === "to" ? "" : "rotate-180"} />
      <span>Block {blockId}</span>
      <span className="opacity-60">[{kind}]</span>
    </div>
  );
}

function InstrSection({ title, color, borderColor, children }: {
  title: string;
  color: string;
  borderColor: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`bg-bg-card border ${borderColor} rounded-lg overflow-hidden`}>
      <div className={`px-3 py-1.5 border-b ${borderColor} text-[10px] font-semibold uppercase tracking-wider ${color}`}>
        {title}
      </div>
      <div className="p-3">{children}</div>
    </div>
  );
}
