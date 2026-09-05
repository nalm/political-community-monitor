import React, { useCallback, useEffect, useState } from 'react';
import { AnalyzeResult, Community, CommunityProgress, Issue, Phase, Post } from './types';
import { analyzePosts, collectCommunity, getCommunities } from './services/api';
import { Header } from './components/Header';
import { IssueComparisonCard } from './components/IssueComparisonCard';
import { CommunityFeedModal } from './components/CommunityFeedModal';
import { SyncProgress } from './components/SyncProgress';
import { AlertCircle, Flame, RefreshCw, Info } from 'lucide-react';

export const App: React.FC = () => {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [phase, setPhase] = useState<Phase>('idle');
  const [progress, setProgress] = useState<CommunityProgress[]>([]);
  const [feed, setFeed] = useState<Record<string, Post[]>>({});
  const [issues, setIssues] = useState<Issue[]>([]);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [startedAt, setStartedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedModalOpen, setFeedModalOpen] = useState(false);

  useEffect(() => {
    getCommunities().then(setCommunities).catch(() => setCommunities([]));
  }, []);

  const isRunning = phase === 'collecting' || phase === 'analyzing';

  const handleRefresh = useCallback(async () => {
    if (isRunning || communities.length === 0) return;

    setError(null);
    setIssues([]);
    setResult(null);
    setFeed({});
    setStartedAt(new Date());
    setPhase('collecting');
    setProgress(
      communities.map((c) => ({
        community_id: c.id,
        name: c.name,
        color: c.color,
        status: 'collecting',
        count: 0,
        error: null,
      }))
    );

    const mark = (id: string, patch: Partial<CommunityProgress>) =>
      setProgress((prev) => prev.map((p) => (p.community_id === id ? { ...p, ...patch } : p)));

    // 커뮤니티별로 독립 요청. 한 곳이 실패해도 나머지는 그대로 진행된다.
    const collected: Record<string, Post[]> = {};
    await Promise.all(
      communities.map(async (c) => {
        try {
          const res = await collectCommunity(c.id);
          collected[c.id] = res.posts;
          mark(c.id, { status: 'ok', count: res.count });
        } catch (err) {
          mark(c.id, {
            status: 'error',
            error: err instanceof Error ? err.message : '수집 실패',
          });
        }
      })
    );

    setFeed(collected);

    if (Object.keys(collected).length === 0) {
      setError('모든 커뮤니티에서 게시물을 수집하지 못했습니다.');
      setPhase('error');
      return;
    }

    setPhase('analyzing');
    try {
      const analyzed = await analyzePosts(collected);
      setResult(analyzed);
      setIssues(analyzed.issues);
      setPhase('report');
    } catch (err) {
      setError(err instanceof Error ? err.message : '분석에 실패했습니다.');
      setPhase('error');
    }
  }, [communities, isRunning]);

  const totalPosts = Object.values(feed).reduce((acc, posts) => acc + posts.length, 0);

  return (
    <div className="min-h-screen bg-[#0a0e17] text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      <Header
        onRefresh={handleRefresh}
        isSyncing={isRunning}
        onOpenFeedModal={() => setFeedModalOpen(true)}
        canOpenFeed={phase === 'report' && totalPosts > 0}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 1) 최초 진입: 타이틀만 */}
        {phase === 'idle' && (
          <section className="flex flex-col items-center justify-center text-center py-28 sm:py-40 space-y-10">
            <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight">
              무엇이 이슈인가?
            </h1>
            <button
              onClick={handleRefresh}
              className="flex items-center gap-2.5 px-7 py-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white text-sm font-bold shadow-lg shadow-indigo-600/30 transition"
            >
              <RefreshCw className="w-4 h-4" />
              인기글 실시간 새로고침
            </button>
          </section>
        )}

        {/* 2·3) 수집 중 / 분석 중 */}
        {isRunning && (
          <SyncProgress phase={phase} progress={progress} totalPosts={totalPosts} />
        )}

        {/* 실패 */}
        {phase === 'error' && (
          <div className="max-w-2xl mx-auto py-24 text-center space-y-4">
            <AlertCircle className="w-9 h-9 text-rose-500 mx-auto" />
            <h2 className="text-xl font-bold text-white">수집·분석에 실패했습니다</h2>
            <p className="text-sm text-slate-400">{error}</p>
            <button
              onClick={handleRefresh}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* 3) 리포트 */}
        {phase === 'report' && (
          <section className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Flame className="w-5 h-5 text-rose-500" />
                <h2 className="text-lg font-extrabold text-white">현안별 커뮤니티 반응 리포트</h2>
              </div>
              <span className="text-xs text-slate-400">
                {startedAt?.toLocaleString('ko-KR')} 기준 · 게시물 {totalPosts}개 · 현안{' '}
                {issues.length}건
              </span>
            </div>

            {/* 일부 커뮤니티가 실패했으면 숨기지 않고 알린다 */}
            {progress.some((p) => p.status === 'error') && (
              <div className="px-4 py-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  수집 실패:{' '}
                  {progress
                    .filter((p) => p.status === 'error')
                    .map((p) => p.name)
                    .join(', ')}
                  . 이 커뮤니티는 리포트에서 빠져 있습니다.
                </span>
              </div>
            )}

            {result?.analysis_method === 'heuristic' && (
              <div className="px-4 py-3 rounded-xl bg-amber-950/40 border border-amber-800/60 text-amber-200 text-xs flex items-start gap-2">
                <Info className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  AI 분석을 사용하지 못해 제목 빈도·반응 수치 기반 자동 집계로 대체했습니다.
                  {result.analysis_note ? ` (${result.analysis_note})` : ''}
                </span>
              </div>
            )}

            {issues.length === 0 ? (
              <div className="p-16 text-center bg-slate-900/60 rounded-2xl border border-slate-800 text-slate-400 text-sm">
                추출된 현안이 없습니다.
              </div>
            ) : (
              <div className="space-y-6">
                {issues.map((issue, idx) => (
                  <IssueComparisonCard key={`${issue.title}-${idx}`} issue={issue} />
                ))}
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="mt-16 border-t border-slate-800/80 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>정치·시사 커뮤니티 여론 모니터링 · 보배드림 · 더쿠 · 딴지일보</p>
      </footer>

      <CommunityFeedModal
        isOpen={feedModalOpen}
        onClose={() => setFeedModalOpen(false)}
        communities={communities}
        feed={feed}
      />
    </div>
  );
};
