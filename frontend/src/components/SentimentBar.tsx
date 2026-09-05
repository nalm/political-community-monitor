import React from 'react';

interface Props {
  score: number; // -1.0 to 1.0
  label?: string;
}

export const SentimentBar: React.FC<Props> = ({ score, label }) => {
  // -1.0 -> 0%, 0.0 -> 50%, 1.0 -> 100%
  const percentage = Math.min(100, Math.max(0, ((score + 1) / 2) * 100));

  let colorClass = 'bg-slate-400';
  let textClass = 'text-slate-300';
  let desc = '중립/혼재';

  if (score <= -0.5) {
    colorClass = 'bg-rose-500';
    textClass = 'text-rose-400';
    desc = '강한 비판/반발';
  } else if (score < -0.15) {
    colorClass = 'bg-orange-400';
    textClass = 'text-orange-300';
    desc = '부정/우려';
  } else if (score >= 0.5) {
    colorClass = 'bg-emerald-500';
    textClass = 'text-emerald-400';
    desc = '적극 지지/환영';
  } else if (score > 0.15) {
    colorClass = 'bg-teal-400';
    textClass = 'text-teal-300';
    desc = '긍정/호의';
  }

  return (
    <div className="w-full">
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-slate-400 font-medium">여론 감성 지수:</span>
        <span className={`font-semibold ${textClass}`}>
          {label || desc} ({score > 0 ? `+${score.toFixed(2)}` : score.toFixed(2)})
        </span>
      </div>
      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden relative">
        {/* Center line (neutral) */}
        <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-slate-600 z-10"></div>
        <div
          className={`h-full transition-all duration-500 rounded-full ${colorClass}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
        <span>비판·반발(-1.0)</span>
        <span>중립(0.0)</span>
        <span>지지·호응(+1.0)</span>
      </div>
    </div>
  );
};
