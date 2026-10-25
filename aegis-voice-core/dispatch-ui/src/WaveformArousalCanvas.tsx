import React, { useEffect, useRef } from "react";

interface WaveformCanvasProps {
  arousal: number;
  valence: number;
  dominance: number;
  f0Hz: number;
  jitterPct: number;
  coercionDetected: boolean;
}

export const WaveformArousalCanvas: React.FC<WaveformCanvasProps> = ({
  arousal,
  valence,
  dominance,
  f0Hz,
  jitterPct,
  coercionDetected,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let phase = 0;
    let animId: number;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const width = canvas.width;
      const height = canvas.height;
      const centerY = height / 2;

      phase += 0.05;

      // Primary Waveform
      ctx.beginPath();
      ctx.strokeStyle = arousal > 0.7 ? "rgba(239, 68, 68, 0.85)" : "rgba(34, 211, 238, 0.85)";
      ctx.lineWidth = 2;

      for (let x = 0; x < width; x += 3) {
        const y = centerY + Math.sin(x * 0.02 + phase) * (arousal * 35.0 + 8.0);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Coercion Secondary Transducer Waveform (<280Hz roll-off)
      if (coercionDetected) {
        ctx.beginPath();
        ctx.strokeStyle = "rgba(245, 158, 11, 0.7)";
        ctx.setLineDash([4, 4]);
        for (let x = 0; x < width; x += 3) {
          const y = centerY + Math.sin(x * 0.07 + phase * 1.6) * 12.0;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.setLineDash([]);
      }

      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, [arousal, coercionDetected]);

  return (
    <div className="relative w-full h-36 bg-[#04060A] rounded-lg overflow-hidden border border-slate-800">
      <canvas ref={canvasRef} width={600} height={150} className="w-full h-full block" />
      <div className="absolute top-2 right-2 text-[10px] font-mono text-slate-300 bg-slate-900/90 px-2 py-0.5 rounded border border-slate-800">
        F0: <span className="text-cyan-400 font-bold">{f0Hz} Hz</span> | Jitter:{" "}
        <span className="text-amber-400">{jitterPct}%</span>
      </div>
    </div>
  );
};
