"use client";
import { Cpu, Zap, GitBranch, Trash2, AlertTriangle, Clock, Activity } from "lucide-react";
import type { Stats } from "@/app/page";

type Props = { stats?: Stats; loading: boolean };

const StatPill = ({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  color: string;
}) => (
  <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border bg-bg-card/50 border-white/5 shadow-sm`}>
    <Icon size={12} className={color} />
    <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-tighter">{label}</span>
    <span className={`text-[12px] font-bold font-mono ${color}`}>{value}</span>
  </div>
);

export default function Header({ stats, loading }: Props) {
  return (
    <div className="flex items-center justify-between px-6 py-3 border-b border-white/5 bg-[#080b12] shrink-0 z-50 shadow-xl">
      {/* Logo */}
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
          <Cpu size={20} className="text-white" />
        </div>
        <div>
          <div className="text-lg font-black text-white tracking-tight flex items-center gap-2">
            COMPILER <span className="text-indigo-400">OPTIMIZER</span>
          </div>
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.2em]">Static Analysis Pipeline v2.0</div>
        </div>
      </div>

      {/* Stats pills */}
      <div className="flex items-center gap-3">
        {stats ? (
          <>
            <StatPill icon={GitBranch} label="Blocks" value={stats.block_count} color="text-cyan-400" />
            <StatPill icon={Zap} label="Folded" value={stats.folded} color="text-amber-400" />
            <StatPill icon={Zap} label="Prop" value={stats.propagated} color="text-emerald-400" />
            <StatPill icon={Trash2} label="DCE" value={stats.dead_removed} color="text-red-400" />
            <StatPill icon={AlertTriangle} label="Unreach" value={stats.unreachable} color="text-sky-400" />
            <div className="h-8 w-[1px] bg-white/10 mx-2" />
            <div className="flex flex-col items-end">
              <div className="text-[10px] text-slate-500 font-bold uppercase">Latency</div>
              <div className="text-sm font-mono font-bold text-purple-400">{stats.elapsed_ms}ms</div>
            </div>
          </>
        ) : (
          <div className="flex items-center gap-2 text-slate-500 font-mono text-xs animate-pulse">
            <Activity size={14} className="animate-spin" />
            Awaiting Source Input...
          </div>
        )}
      </div>
    </div>
  );
}
