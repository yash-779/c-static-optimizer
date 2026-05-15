"use client";
import { useState } from "react";
import { AlertTriangle, Skull, Activity, BarChart3, RefreshCw } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import type { PipelineResult, Loop } from "@/app/page";

type Props = { result: PipelineResult | null };

type Tab = "analysis" | "loops" | "stats";

const TAB_ICONS: Record<Tab, React.ElementType> = {
  analysis: AlertTriangle,
  loops: RefreshCw,
  stats: BarChart3,
};

export default function AnalysisPanel({ result }: Props) {
  const [tab, setTab] = useState<Tab>("analysis");

  const tabs: Tab[] = ["analysis", "loops", "stats"];

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Tabs */}
      <div className="flex px-2 pt-2 bg-[#1f2937] shrink-0 border-b border-white/5">
        {tabs.map((t) => {
          const Icon = TAB_ICONS[t];
          return (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex items-center gap-1.5 px-4 py-2 text-[11px] font-bold capitalize transition-all border-b-2 ${
                tab === t
                  ? "border-purple-500 text-purple-300"
                  : "border-transparent text-slate-500 hover:text-slate-300"
              }`}
            >
              <Icon size={12} />
              {t}
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-y-auto min-h-0 p-3 space-y-3">
        {tab === "analysis" && <AnalysisTab result={result} />}
        {tab === "loops" && <LoopsTab loops={result?.loops} />}
        {tab === "stats" && <StatsTab result={result} />}
      </div>
    </div>
  );
}

function AnalysisTab({ result }: { result: PipelineResult | null }) {
  const uninit = result?.analysis.uninitialized ?? [];
  const dead = result?.analysis.dead_assignments ?? [];

  return (
    <>
      {/* Uninitialized */}
      <Section
        icon={AlertTriangle}
        title="Uninitialized Variables"
        count={uninit.length}
        countColor={uninit.length > 0 ? "text-amber-400" : "text-emerald-400"}
      >
        {uninit.length === 0 ? (
          <div className="text-[11px] text-emerald-400 font-mono">✓ No uninitialized variables detected</div>
        ) : (
          uninit.map((u, i) => (
            <div key={i} className="flex items-center gap-2 py-1 border-b border-border-dim last:border-0">
              <span className="text-[10px] text-slate-500 font-mono">B{u.block}</span>
              <span className="text-[11px] text-amber-300 font-mono font-semibold">{u.var}</span>
              <span className="text-[10px] text-slate-500">used before definition</span>
            </div>
          ))
        )}
      </Section>

      {/* Dead Assignments */}
      <Section
        icon={Skull}
        title="Dead Assignments"
        count={dead.length}
        countColor={dead.length > 0 ? "text-red-400" : "text-emerald-400"}
      >
        {dead.length === 0 ? (
          <div className="text-[11px] text-emerald-400 font-mono">✓ No dead assignments</div>
        ) : (
          dead.map((d, i) => (
            <div key={i} className="py-1 border-b border-border-dim last:border-0">
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-500 font-mono">B{d.block}</span>
                <span className="text-[11px] text-red-300 font-mono font-semibold">{d.var}</span>
                <span className="text-[10px] text-slate-500">assigned but never used</span>
              </div>
              <div className="text-[10px] text-slate-600 font-mono ml-8 mt-0.5 truncate">{d.instr}</div>
            </div>
          ))
        )}
      </Section>

      {/* Live Variable Legend */}
      <Section icon={Activity} title="Liveness Color Guide" count={undefined} countColor="">
        <div className="space-y-1.5">
          {[
            { color: "bg-emerald-500", label: "Live-In: variable needed when block starts" },
            { color: "bg-sky-500", label: "Live-Out: variable needed after block ends" },
            { color: "bg-red-500", label: "DCE: definition removed (not live)" },
            { color: "bg-purple-500", label: "LICM: instruction hoisted to preheader" },
          ].map((e, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${e.color} shrink-0`} />
              <span className="text-[10px] text-slate-400">{e.label}</span>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}

function LoopsTab({ loops }: { loops?: Loop[] }) {
  if (!loops || loops.length === 0) {
    return (
      <div className="text-[11px] text-slate-500 text-center py-8 font-mono">
        No loops detected
      </div>
    );
  }
  return (
    <div className="space-y-2">
      {loops.map((lp, i) => (
        <div key={i} className="bg-bg-card border border-purple-800/40 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[12px] font-bold text-purple-300">Loop {i + 1} — Header: Block {lp.header}</span>
            <span className="text-[10px] font-mono text-slate-500">back-edge: {lp.back_edge[0]}→{lp.back_edge[1]}</span>
          </div>
          <div className="text-[11px] text-slate-400 mb-2">
            Body: {"{"}  {lp.body.join(", ")}  {"}"}
          </div>
          {lp.licm.length > 0 ? (
            <div className="space-y-1">
              <div className="text-[10px] text-purple-400 font-semibold uppercase tracking-wider mb-1">LICM Candidates</div>
              {lp.licm.map((l, j) => (
                <div key={j} className="text-[10px] font-mono text-purple-200 bg-purple-950/40 px-2 py-1 rounded border border-purple-800/30">
                  {l}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-[11px] text-slate-600 italic">No loop-invariant code found.</div>
          )}
        </div>
      ))}
    </div>
  );
}

const CHART_COLORS = ["#f59e0b", "#10b981", "#ef4444", "#22d3ee", "#a855f7"];

function StatsTab({ result }: { result: PipelineResult | null }) {
  if (!result) {
    return <div className="text-[11px] text-slate-500 text-center py-8 font-mono">Run pipeline to see stats</div>;
  }
  const { stats } = result;

  const barData = [
    { name: "Fold", value: stats.folded, color: "#f59e0b" },
    { name: "Prop", value: stats.propagated, color: "#10b981" },
    { name: "DCE", value: stats.dead_removed, color: "#ef4444" },
    { name: "UCR", value: stats.unreachable, color: "#22d3ee" },
  ];

  const pieData = barData.filter((d) => d.value > 0);

  return (
    <div className="space-y-4">
      {/* Stat grid */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: "Active Nodes", value: stats.block_count, color: "text-cyan-400", sub: "Basic Blocks" },
          { label: "Total Edges", value: stats.edge_count, color: "text-slate-300", sub: "Control Flow" },
          { label: "Comp. Time", value: stats.elapsed_ms, color: "text-purple-400", sub: "Latency (ms)" },
          { label: "Cleanup", value: stats.nops_removed, color: "text-red-400", sub: "NOPs pruned" },
        ].map((s) => (
          <div key={s.label} className="bg-[#0f172a]/50 border border-white/5 rounded-xl p-3 shadow-inner">
            <div className={`text-xl font-black font-mono ${s.color} tracking-tighter`}>{s.value}</div>
            <div className="text-[10px] text-slate-300 font-bold uppercase mt-1">{s.label}</div>
            <div className="text-[9px] text-slate-600 font-mono italic">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Bar chart - Simulation Style */}
      <div className="bg-[#0f172a]/50 border border-white/5 rounded-xl p-4">
        <div className="text-[10px] text-slate-400 font-bold mb-4 uppercase tracking-[0.2em] flex items-center gap-2">
          <Activity size={10} className="text-indigo-400" />
          Optimization Impact Metrics
        </div>
        <ResponsiveContainer width="100%" height={140}>
          <BarChart data={barData} margin={{ top: 0, right: 0, bottom: 0, left: -30 }}>
            <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#475569", fontWeight: 700 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 9, fill: "#475569" }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: "#080b12", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, fontSize: 11, boxShadow: "0 10px 15px -3px rgba(0,0,0,0.5)" }}
              cursor={{ fill: "rgba(255,255,255,0.05)" }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {barData.map((entry, i) => (
                <Cell key={i} fill={entry.color} fillOpacity={0.8} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Pie chart - Budget Breakdown Style */}
      {pieData.length > 0 && (
        <div className="bg-[#0f172a]/50 border border-white/5 rounded-xl p-4">
          <div className="text-[10px] text-slate-400 font-bold mb-1 uppercase tracking-[0.2em] flex items-center gap-2">
            <BarChart3 size={10} className="text-pink-400" />
            Reduction Breakdown
          </div>
          <div className="text-[9px] text-slate-600 font-mono mb-4 italic">Weighted impact per optimization pass</div>
          <div className="flex items-center">
            <ResponsiveContainer width="50%" height={120}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={45} innerRadius={30} paddingAngle={5} stroke="none">
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#080b12", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 10 }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="w-[50%] space-y-2">
              {pieData.map((d, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full" style={{ background: d.color }} />
                    <span className="text-[10px] text-slate-400 font-bold">{d.name}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Section({ icon: Icon, title, count, countColor, children }: {
  icon: React.ElementType;
  title: string;
  count: number | undefined;
  countColor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-bg-card border border-border-dim rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border-dim">
        <div className="flex items-center gap-2">
          <Icon size={12} className="text-slate-400" />
          <span className="text-[11px] font-semibold text-slate-300">{title}</span>
        </div>
        {count !== undefined && (
          <span className={`text-[12px] font-bold font-mono ${countColor}`}>{count}</span>
        )}
      </div>
      <div className="p-3 space-y-1 text-[11px]">{children}</div>
    </div>
  );
}
