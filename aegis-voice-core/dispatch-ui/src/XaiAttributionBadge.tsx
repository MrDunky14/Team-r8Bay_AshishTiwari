import React from "react";

interface XaiProps {
  urgencyScore: number;
  badge: string;
  threatKeywords: string[];
  shockParalysis: boolean;
  coercionDetected: boolean;
  onOverride: (action: string) => void;
}

export const XaiAttributionBadge: React.FC<XaiProps> = ({
  urgencyScore,
  badge,
  threatKeywords,
  shockParalysis,
  coercionDetected,
  onOverride,
}) => {
  return (
    <div className="bg-[#080C17] border border-slate-800 rounded-lg p-3">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-bold text-slate-300">XAI ATTRIBUTION RATIONALE</span>
        <span className="text-[10px] font-mono text-cyan-400">Score: {urgencyScore.toFixed(2)}</span>
      </div>

      <div className="text-xs text-slate-300 mt-2">
        <strong>Badge:</strong> <span className="text-rose-400 font-bold">{badge}</span>
      </div>

      {shockParalysis && (
        <div className="mt-1 text-[11px] text-amber-300 font-semibold">
          ⚡ Triggered via Semantic Floor: Monotone affect (F0 &lt; 8Hz) overridden by high-value fraud intent.
        </div>
      )}

      {coercionDetected && (
        <div className="mt-1 text-[11px] text-red-400 font-semibold">
          ⚠️ Secondary Transducer Coercion (&lt;280Hz roll-off + coaching micro-pause).
        </div>
      )}

      <div className="flex flex-wrap gap-1 mt-2">
        {threatKeywords.map((kw) => (
          <span
            key={kw}
            className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800"
          >
            {kw}
          </span>
        ))}
      </div>

      <div className="flex gap-2 mt-3 pt-2 border-t border-slate-800 text-[10px]">
        <button
          onClick={() => onOverride("DOWNGRADE_ACOUSTIC_SPIKE")}
          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-semibold"
        >
          Downgrade: Acoustic Spike
        </button>
        <button
          onClick={() => onOverride("DOWNGRADE_ROUTINE")}
          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-semibold"
        >
          Downgrade: Routine
        </button>
      </div>
    </div>
  );
};
