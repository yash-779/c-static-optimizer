"use client";
import { ArrowUp, ArrowDown, X, Plus, Play, RotateCcw, Settings2 } from "lucide-react";

type PassOption = { id: string; label: string; color: string; badge: string };

type Props = {
  sequence: string[];
  setSequence: (s: string[]) => void;
  passOptions: PassOption[];
  onRun: () => void;
  loading: boolean;
};

const BADGE_COLORS: Record<string, string> = {
  fold: "bg-amber-900/60 text-amber-300 border-amber-700/50",
  prop: "bg-emerald-900/60 text-emerald-300 border-emerald-700/50",
  dce: "bg-red-900/60 text-red-300 border-red-700/50",
  unreachable: "bg-sky-900/60 text-sky-300 border-sky-700/50",
  licm: "bg-purple-900/60 text-purple-300 border-purple-700/50",
};

const PASS_LABELS: Record<string, string> = {
  fold: "Const. Folding",
  prop: "Const. Propagation",
  dce: "Dead Code Elim.",
  unreachable: "Unreachable Rem.",
  licm: "Loop Inv. CM",
};

export default function PipelinePanel({ sequence, setSequence, passOptions, onRun, loading }: Props) {
  const move = (idx: number, dir: -1 | 1) => {
    const s = [...sequence];
    const ni = idx + dir;
    if (ni < 0 || ni >= s.length) return;
    [s[idx], s[ni]] = [s[ni], s[idx]];
    setSequence(s);
  };

  const remove = (idx: number) => setSequence(sequence.filter((_, i) => i !== idx));

  const add = (id: string) => setSequence([...sequence, id]);

  const reset = () => setSequence(["fold", "prop", "fold", "dce", "unreachable", "dce", "licm"]);

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-[#1f2937]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-[#1f2937]">
        <div className="flex items-center gap-2">
          <Settings2 size={13} className="text-purple-400" />
          <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-widest">Pipeline Sequence</span>
        </div>
        <button onClick={reset} className="text-slate-500 hover:text-slate-300 transition-colors">
          <RotateCcw size={12} />
        </button>
      </div>

      {/* Sequence list */}
      <div className="flex-1 overflow-y-auto px-2 py-1.5 space-y-1 min-h-0">
        {sequence.map((pass, i) => (
          <div
            key={`${pass}-${i}`}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded-md bg-bg-card border border-border-dim hover:border-border-bright transition-all group"
          >
            <span className="text-[10px] text-slate-600 font-mono w-4 text-center">{i + 1}.</span>
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${BADGE_COLORS[pass] || "bg-slate-800 text-slate-400 border-slate-700"}`}>
              {pass.toUpperCase()}
            </span>
            <span className="flex-1 text-[11px] text-slate-300 truncate">{PASS_LABELS[pass] || pass}</span>
            <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <button onClick={() => move(i, -1)} className="p-0.5 hover:text-white text-slate-500 transition-colors">
                <ArrowUp size={11} />
              </button>
              <button onClick={() => move(i, 1)} className="p-0.5 hover:text-white text-slate-500 transition-colors">
                <ArrowDown size={11} />
              </button>
              <button onClick={() => remove(i)} className="p-0.5 hover:text-red-400 text-slate-500 transition-colors">
                <X size={11} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add pass */}
      <div className="px-2 py-1.5 border-t border-border-dim">
        <div className="flex gap-1.5">
          <select
            id="pass-select"
            className="flex-1 bg-bg-card border border-border-dim rounded text-[11px] text-slate-300 px-2 py-1 focus:outline-none focus:border-purple-500 transition-colors"
            defaultValue=""
            onChange={(e) => { if (e.target.value) { add(e.target.value); e.target.value = ""; } }}
          >
            <option value="" disabled>Add pass...</option>
            {passOptions.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
          <button
            onClick={() => {}}
            className="px-2 py-1 bg-purple-900/40 border border-purple-700/50 rounded text-purple-300 hover:bg-purple-800/50 transition-colors"
          >
            <Plus size={13} />
          </button>
        </div>
      </div>

      <div className="p-3 border-t border-white/5 bg-[#1f2937]">
        <button
          id="run-pipeline-btn"
          onClick={onRun}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-full font-bold text-sm bg-[#8b5cf6] hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white shadow-lg transition-all"
        >
          <Play size={16} fill="currentColor" />
          {loading ? "Analyzing..." : "Run Pipeline"}
        </button>
      </div>
    </div>
  );
}
