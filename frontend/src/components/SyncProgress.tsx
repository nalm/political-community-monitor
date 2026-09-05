import React from 'react';
import { SyncJob } from '../types';
import { Check, Loader2, AlertTriangle, Circle, Sparkles } from 'lucide-react';

interface Props {
  job: SyncJob;
}

const STATUS_TEXT: Record<string, string> = {
  pending: '대기 중',
  collecting: '수집 중',
  ok: '수집 완료',
  error: '실패',
};

export const SyncProgress: React.FC<Props> = ({ job }) => {
  const isAnalyzing = job.phase === 'analyzing';
  const done = job.communities.filter((c) => c.status === 'ok' || c.status === 'error').length;

  return (
    <div className="max-w-2xl mx-auto py-16 space-y-8">
      <div className="text-center space-y-2">
        <Loader2 className="w-9 h-9 text-indigo-400 animate-spin mx-auto" />
        <h2 className="text-2xl font-bold text-white">
          {isAnalyzing ? '핫이슈 분석 중' : '커뮤니티 수집 중'}
        </h2>
        <p className="text-sm text-slate-400">
          {isAnalyzing
            ? `수집된 ${job.total_posts}개 게시물에서 핵심 현안을 뽑고 있습니다.`
            : `${done}/${job.communities.length}개 커뮤니티 완료 · 현재까지 ${job.total_posts}개 수집`}
        </p>
      </div>

      {/* 커뮤니티별 진행 상황 */}
      <div className="space-y-2">
        {job.communities.map((c) => (
          <div
            key={c.community_id}
            className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-slate-900/70 border border-slate-800"
          >
            <div className="flex items-center gap-3 min-w-0">
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
              <span className="text-sm font-semibold text-slate-100">{c.name}</span>
              {c.error && (
                <span className="text-[11px] text-rose-400 truncate" title={c.error}>
                  {c.error}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {c.status === 'ok' && <span className="text-xs text-slate-400">{c.count}개</span>}
              <span
                className={`flex items-center gap-1.5 text-xs font-medium ${
                  c.status === 'ok'
                    ? 'text-emerald-400'
                    : c.status === 'error'
                    ? 'text-rose-400'
                    : c.status === 'collecting'
                    ? 'text-indigo-300'
                    : 'text-slate-500'
                }`}
              >
                {c.status === 'ok' && <Check className="w-3.5 h-3.5" />}
                {c.status === 'error' && <AlertTriangle className="w-3.5 h-3.5" />}
                {c.status === 'collecting' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                {c.status === 'pending' && <Circle className="w-3 h-3" />}
                {STATUS_TEXT[c.status]}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* 분석 단계 표시 */}
      <div
        className={`flex items-center gap-2.5 px-4 py-3 rounded-xl border text-sm ${
          isAnalyzing
            ? 'bg-indigo-950/50 border-indigo-800/70 text-indigo-200'
            : 'bg-slate-900/40 border-slate-800 text-slate-500'
        }`}
      >
        {isAnalyzing ? (
          <Loader2 className="w-4 h-4 animate-spin shrink-0" />
        ) : (
          <Sparkles className="w-4 h-4 shrink-0" />
        )}
        <span>
          {isAnalyzing ? '현안별 커뮤니티 반응을 분석하고 있습니다…' : '수집이 끝나면 분석을 시작합니다.'}
        </span>
      </div>
    </div>
  );
};
