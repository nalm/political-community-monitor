import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Community, Issue, Post, SyncJob } from './types';
import {
  getCommunities,
  getCommunityFeed,
  getIssues,
  getSyncStatus,
  startSync,
} from './services/api';
import { Header } from './components/Header';
import { IssueComparisonCard } from './components/IssueComparisonCard';
import { CommunityFeedModal } from './components/CommunityFeedModal';
import { SyncProgress } from './components/SyncProgress';
import { AlertCircle, Flame, RefreshCw, Info } from 'lucide-react';

const POLL_INTERVAL_MS = 1500;

export const App: React.FC = () => {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [job, setJob] = useState<SyncJob | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [feed, setFeed] = useState<Record<string, Post[]>>({});
  const [feedModalOpen, setFeedModalOpen] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    getCommunities().then(setCommunities).catch(() => setCommunities([]));
    return () => {
      if (pollRef.current !== null) window.clearInterval(pollRef.current);
    };
  }, []);

  const isRunning = job?.phase === 'collecting' || job?.phase === 'analyzing';

  /** 분석까지 끝난 뒤 리포트와 원문 피드를 받아온다. */
  const loadResults = useCallback(async (runId: string) => {
    const [issueData, feedData] = await Promise.all([
      getIssues(runId),
      getCommunityFeed(runId),
    ]);
    setIssues(issueData.issues || []);
    setFeed(feedData.feed || {});
  }, []);

  const stopPolling = useCallback(() => {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const handleRefresh = useCallback(async () => {
    if (isRunning) return;

    setStartError(null);
    setIssues([]);
    setFeed({});

    let jobId: string;
    try {
      jobId = (await startSync()).job_id;
    } catch (err) {
      setStartError(err instanceof Error ? err.message : '수집을 시작하지 못했습니다.');
      return;
    }

    // 폴링 시작 전에 즉시 '수집 중' 상태로 전환해 버튼이 멈춰 보이지 않게 한다.
    setJob({
      job_id: jobId,
      run_id: jobId,
      phase: 'collecting',
      started_at: new Date().toISOString(),
      finished_at: null,
      error: null,
      issue_count: 0,
      total_posts: 0,
      analysis_method: null,
      analysis_note: null,
      communities: communities.map((c) => ({
        community_id: c.id,
        name: c.name,
        color: c.color,
        status: 'pending',
        count: 0,
        error: null,
      })),
    });

    stopPolling();
    pollRef.current = window.setInterval(async () => {
      try {
        const status = await getSyncStatus(jobId);
        setJob(status);
        if (status.phase === 'done') {
          stopPolling();
          await loadResults(status.run_id);
        } else if (status.phase === 'error') {
          stopPolling();
        }
      } catch (err) {
        stopPolling();
        setStartError(err instanceof Error ? err.message : '진행 상황을 가져오지 못했습니다.');
      }
    }, POLL_INTERVAL_MS);
  }, [communities, isRunning, loadResults, stopPolling]);

  const phase = job?.phase;

  return (
    <div className="min-h-screen bg-[#0a0e17] text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      <Header
        onRefresh={handleRefresh}
        isSyncing={!!isRunning}
        onOpenFeedModal={() => setFeedModalOpen(true)}
        canOpenFeed={phase === 'done' && Object.keys(feed).length > 0}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {startError && (
          <div className="mb-6 px-4 py-3 rounded-xl bg-rose-950/50 border border-rose-800/70 text-rose-200 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {startError}
          </div>
        )}

        {/* 1) 최초 진입: 타이틀만 */}
        {!job && (
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
        {(phase === 'collecting' || phase === 'analyzing') && job && <SyncProgress job={job} />}

        {/* 실패 */}
        {phase === 'error' && job && (
          <div className="max-w-2xl mx-auto py-24 text-center space-y-4">
            <AlertCircle className="w-9 h-9 text-rose-500 mx-auto" />
            <h2 className="text-xl font-bold text-white">수집·분석에 실패했습니다</h2>
            <p className="text-sm text-slate-400">{job.error}</p>
            <button
              onClick={handleRefresh}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* 3) 리포트 */}
        {phase === 'done' && job && (
          <section className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Flame className="w-5 h-5 text-rose-500" />
                <h2 className="text-lg font-extrabold text-white">현안별 커뮤니티 반응 리포트</h2>
              </div>
              <span className="text-xs text-slate-400">
                {new Date(job.started_at).toLocaleString('ko-KR')} 기준 · 게시물 {job.total_posts}개 ·
                현안 {issues.length}건
              </span>
            </div>

            {job.analysis_method === 'heuristic' && (
              <div className="px-4 py-3 rounded-xl bg-amber-950/40 border border-amber-800/60 text-amber-200 text-xs flex items-start gap-2">
                <Info className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  AI 분석을 사용하지 못해 제목 빈도·반응 수치 기반 자동 집계로 대체했습니다.
                  {job.analysis_note ? ` (${job.analysis_note})` : ''}
                </span>
              </div>
            )}

            {issues.length === 0 ? (
              <div className="p-16 text-center bg-slate-900/60 rounded-2xl border border-slate-800 text-slate-400 text-sm">
                추출된 현안이 없습니다.
              </div>
            ) : (
              <div className="space-y-6">
                {issues.map((issue) => (
                  <IssueComparisonCard key={issue.id} issue={issue} />
                ))}
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="mt-16 border-t border-slate-800/80 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>정치·시사 커뮤니티 여론 모니터링 · 잇싸 · 보배드림 · 더쿠 · 딴지일보</p>
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
