"use client";
import { useState, useCallback } from "react";
import Header from "@/components/Header";
import EditorPanel from "@/components/EditorPanel";
import PipelinePanel from "@/components/PipelinePanel";
import CfgPanel from "@/components/CfgPanel";
import AnalysisPanel from "@/components/AnalysisPanel";
import BlockExplorer from "@/components/BlockExplorer";

const DEFAULT_CODE = `int main() {
    int a = 10;
    int b = 20;
    int x = a + b; // Constant Folding: x = 30

    int i = 0;
    int total = 0;

    while (i < 5) {
        int j = 0;
        int inner_invariant = x * 2; // LICM: hoisted out
        while (j < 5) {
            total = total + inner_invariant;
            j = j + 1;
        }
        i = i + 1;
    }

    int dead_var = total + 99; // DCE: removed

    if (x > 100) {
        int unreachable = 999; // Unreachable: pruned
    }

    return total;
}`;

export type PipelineResult = {
  dot_before: string;
  dot_after: string;
  blocks: Block[];
  stats: Stats;
  analysis: Analysis;
  loops: Loop[];
  errors: string[];
};

export type Block = {
  id: number;
  label: string;
  instructions: Instr[];
  before_instructions: string[];
  edges: Edge[];
  edges_before: Edge[];
  optimizations: Instr[];
  lv_in: string[];
  lv_out: string[];
};

export type Instr = { text: string; original: string; type: string | null };
export type Edge = { to?: number; from?: number; kind: string };

export type Stats = {
  block_count: number;
  edge_count: number;
  folded: number;
  propagated: number;
  dead_removed: number;
  nops_removed: number;
  unreachable: number;
  elapsed_ms: number;
};

export type Analysis = {
  uninitialized: { block: number; var: string }[];
  dead_assignments: { block: number; instr: string; var: string }[];
};

export type Loop = {
  header: number;
  body: number[];
  back_edge: number[];
  licm_count: number;
  licm: string[];
};

const PASS_OPTIONS = [
  { id: "fold", label: "Constant Folding", color: "text-amber-400", badge: "FOLD" },
  { id: "prop", label: "Constant Propagation", color: "text-emerald-400", badge: "PROP" },
  { id: "dce", label: "Dead Code Elimination", color: "text-red-400", badge: "DCE" },
  { id: "unreachable", label: "Unreachable Removal", color: "text-sky-400", badge: "UCR" },
  { id: "licm", label: "Loop Invariant CM", color: "text-purple-400", badge: "LICM" },
];

const DEFAULT_SEQUENCE = ["fold", "prop", "fold", "dce", "unreachable", "dce", "licm"];

export default function Home() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [sequence, setSequence] = useState<string[]>(DEFAULT_SEQUENCE);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedBlock, setSelectedBlock] = useState<Block | null>(null);
  const [cfgView, setCfgView] = useState<"before" | "after">("after");

  const runPipeline = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSelectedBlock(null);
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, options: { sequence } }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Pipeline failed");
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [code, sequence]);

  return (
    <div className="flex flex-col h-screen bg-bg-primary overflow-hidden">
      <Header stats={result?.stats} loading={loading} />

      {/* Main 3-column layout */}
      <div className="flex flex-1 min-h-0 gap-4 p-4 bg-bg-primary">
        {/* LEFT: Code Editor + Pipeline */}
        <div className="flex flex-col w-[360px] min-w-[300px] gap-4">
          <div className="flex-1 min-h-0 bg-bg-secondary rounded-xl border border-white/5 overflow-hidden shadow-lg flex flex-col">
            <EditorPanel code={code} onChange={setCode} />
          </div>
          <div className="h-[280px] bg-bg-secondary rounded-xl border border-white/5 overflow-hidden shadow-lg flex flex-col">
            <PipelinePanel
              sequence={sequence}
              setSequence={setSequence}
              passOptions={PASS_OPTIONS}
              onRun={runPipeline}
              loading={loading}
            />
          </div>
        </div>

        {/* CENTER: CFG Visualizer */}
        <div className="flex-1 min-w-0 bg-bg-secondary rounded-xl border border-white/5 overflow-hidden shadow-lg flex flex-col relative">
          <CfgPanel
            result={result}
            cfgView={cfgView}
            setCfgView={setCfgView}
            onBlockClick={setSelectedBlock}
            error={error}
            loading={loading}
          />
        </div>

        {/* RIGHT: Analysis + Block Explorer */}
        <div className="flex flex-col w-[340px] min-w-[280px] bg-bg-secondary rounded-xl border border-white/5 overflow-hidden shadow-lg">
          {selectedBlock ? (
            <BlockExplorer
              block={selectedBlock}
              onClose={() => setSelectedBlock(null)}
              passOptions={PASS_OPTIONS}
            />
          ) : (
            <AnalysisPanel result={result} />
          )}
        </div>
      </div>
    </div>
  );
}
