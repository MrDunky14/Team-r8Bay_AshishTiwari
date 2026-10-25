import React from "react";

export interface CallStreamItem {
  stream_id: string;
  caller_name: string;
  phone_number: string;
  wait_time_sec: number;
  loss_amount: string;
  detected_rail: string;
  urgency_score: number;
  badge: string;
  spoof_prob: number;
}

interface LiveQueueBoardProps {
  queue: CallStreamItem[];
  selectedId: string;
  onSelect: (streamId: string) => void;
  onTriggerStressTest: () => void;
}

export const LiveQueueBoard: React.FC<LiveQueueBoardProps> = ({
  queue,
  selectedId,
  onSelect,
  onTriggerStressTest,
}) => {
  return (
    <div className="bg-[#0B101D] border border-slate-800 rounded-xl p-4 flex flex-col h-full shadow-2xl">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
          <h2 className="text-xs font-black tracking-wider text-slate-100 uppercase">
            1930 Live Queue Re-Ranker
          </h2>
        </div>
        <button
          onClick={onTriggerStressTest}
          className="px-2.5 py-1 text-[10px] font-bold rounded bg-rose-600 hover:bg-rose-500 text-white"
        >
          Inject Stress Test
        </button>
      </div>

      <div className="space-y-2 mt-3 flex-1 overflow-y-auto">
        {queue.map((call) => {
          const isSelected = call.stream_id === selectedId;
          const isCritical = call.urgency_score >= 0.72;
          const isSpoof = call.spoof_prob > 0.7;

          return (
            <div
              key={call.stream_id}
              onClick={() => onSelect(call.stream_id)}
              className={`p-3 rounded-lg border cursor-pointer transition-all ${
                isSelected
                  ? isCritical
                    ? "border-red-500 bg-red-950/40"
                    : "border-cyan-500 bg-cyan-950/30"
                  : "border-slate-800 bg-slate-900/40 hover:bg-slate-900"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-200">
                  #{call.stream_id} • {call.caller_name}
                </span>
                <span
                  className={`text-[11px] font-mono px-2 py-0.5 rounded font-black ${
                    isCritical
                      ? "bg-red-900 text-red-200 border border-red-700"
                      : isSpoof
                      ? "bg-amber-950 text-amber-300"
                      : "bg-slate-800 text-slate-300"
                  }`}
                >
                  U(t): {call.urgency_score.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-[11px] text-slate-400 mt-1">
                <span>{call.phone_number}</span>
                <span className="font-semibold text-slate-300">{call.loss_amount}</span>
              </div>
              <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-1">
                <span>{call.badge}</span>
                <span>Wait: {call.wait_time_sec}s</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
