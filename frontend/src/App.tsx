import React, { useEffect, useState } from 'react';
import { Community, Issue, Post } from './types';
import { getCommunities, getIssues, getCommunityFeed, triggerSync } from './services/api';
import { Header } from './components/Header';
import { IssueComparisonCard } from './components/IssueComparisonCard';
import { CommunityFeedModal } from './components/CommunityFeedModal';
import {
  Users,
  Compass,
  AlertCircle,
  Flame,
  Radio,
  RefreshCw,
  TrendingUp
} from 'lucide-react';

export const App: React.FC = () => {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [feed, setFeed] = useState<Record<string, Post[]>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [feedModalOpen, setFeedModalOpen] = useState<boolean>(false);
  const [syncNotice, setSyncNotice] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [commData, issueData, feedData] = await Promise.all([
        getCommunities(),
        getIssues(),
        getCommunityFeed(30)
      ]);
      setCommunities(commData);
      setIssues(issueData.issues || []);
      setFeed(feedData.feed || {});
    } catch (err) {
      console.error('Failed to load initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleManualSync = async () => {
    try {
      setIsSyncing(true);
      setSyncNotice('지정된 인기 게시판 30개 게시물 수집 및 LLM 여론 분석 작업이 시작되었습니다...');
      await triggerSync();
      setTimeout(async () => {
        await loadData();
        setIsSyncing(false);
        setSyncNotice('6대 인기 게시판 30개 게시물 및 AI 분석 결과가 성공적으로 갱신되었습니다!');
        setTimeout(() => setSyncNotice(null), 4000);
      }, 5000);
    } catch (err) {
      setIsSyncing(false);
      setSyncNotice('수집 요청 중 오류가 발생했습니다.');
      setTimeout(() => setSyncNotice(null), 4000);
    }
  };

  const totalPostsCount = Object.values(feed).reduce((acc, posts) => acc + posts.length, 0);

  return (
    <div className="min-h-screen bg-[#0a0e17] text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Header */}
      <Header
        onRefresh={handleManualSync}
        isSyncing={isSyncing}
        onOpenFeedModal={() => setFeedModalOpen(true)}
      />

      {/* Sync Status Banner */}
      {syncNotice && (
        <div className="bg-indigo-900/80 border-b border-indigo-700/80 px-4 py-2.5 text-center text-xs font-medium text-indigo-200 flex items-center justify-center gap-2 animate-in fade-in">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          <span>{syncNotice}</span>
        </div>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Intro & Spectrum Hero Card */}
        <section className="bg-gradient-to-r from-slate-900 via-slate-800/80 to-slate-900 border border-slate-700/70 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
          
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-3 max-w-3xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold border border-indigo-500/30">
                <Radio className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
                <span>6대 인기 게시판 실시간 관제탑 (커뮤니티별 최근 30선)</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight leading-tight">
                정치 현안별 6대 커뮤니티 인기 게시물(30선) 반응 비교
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed">
                각 커뮤니티의 공식 인기 게시판(<span className="text-purple-400 font-semibold">잇싸 정치HOT</span>,{' '}
                <span className="text-blue-400 font-semibold">펨코 정치인기</span>,{' '}
                <span className="text-emerald-400 font-semibold">보배 정치베스트</span>,{' '}
                <span className="text-pink-400 font-semibold">더쿠 스퀘어HOT</span>,{' '}
                <span className="text-indigo-400 font-semibold">다모앙 공감</span>,{' '}
                <span className="text-amber-400 font-semibold">딴지 HOTBEST</span>)에서
                최근 30개씩 총 180개의 핫게시물을 수집하여, 정치 현안별 스탠스와 감성, 핵심 쟁점을 교차 비교합니다.
              </p>
            </div>

            {/* Stats Pills */}
            <div className="grid grid-cols-3 gap-3 shrink-0">
              <div className="bg-slate-800/90 border border-slate-700 rounded-2xl p-3.5 text-center">
                <Users className="w-4 h-4 text-blue-400 mx-auto mb-1" />
                <div className="text-xl font-extrabold text-white">{communities.length}개소</div>
                <div className="text-[11px] text-slate-400">모니터링 커뮤니티</div>
              </div>
              <div className="bg-slate-800/90 border border-slate-700 rounded-2xl p-3.5 text-center">
                <TrendingUp className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                <div className="text-xl font-extrabold text-white">{totalPostsCount}개</div>
                <div className="text-[11px] text-slate-400">수집된 인기 게시물</div>
              </div>
              <div className="bg-slate-800/90 border border-slate-700 rounded-2xl p-3.5 text-center">
                <Flame className="w-4 h-4 text-amber-400 mx-auto mb-1" />
                <div className="text-xl font-extrabold text-white">{issues.length}대 현안</div>
                <div className="text-[11px] text-slate-400">AI 추출 핵심 이슈</div>
              </div>
            </div>
          </div>

          {/* Spectrum Bar */}
          <div className="mt-6 pt-6 border-t border-slate-700/60">
            <div className="text-xs font-bold text-slate-400 mb-2 flex items-center gap-1.5">
              <Compass className="w-4 h-4 text-indigo-400" />
              <span>모니터링 대상 인기 게시판 및 정치적 스펙트럼</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
              {communities.map((c) => (
                <div
                  key={c.id}
                  className="bg-slate-900/80 border border-slate-800 rounded-xl p-2.5 flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-xs text-white">{c.name}</span>
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: c.color }}></span>
                  </div>
                  <div className="text-[11px] text-indigo-300 font-semibold">{c.section}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5 truncate">{c.demographic}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Issues List Section */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Flame className="w-5 h-5 text-rose-500" />
              <h3 className="text-lg font-extrabold text-white">
                실시간 핫이슈별 커뮤니티(인기글 30선) 반응 비교
              </h3>
            </div>
            <span className="text-xs text-slate-400">
              총 {issues.length}개의 주요 현안 분석 중
            </span>
          </div>

          {loading ? (
            <div className="p-16 text-center bg-slate-900/60 rounded-2xl border border-slate-800">
              <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin mx-auto mb-3" />
              <p className="text-sm text-slate-300 font-medium">
                각 커뮤니티의 30개 인기 게시물을 분석하고 있습니다...
              </p>
            </div>
          ) : issues.length === 0 ? (
            <div className="p-16 text-center bg-slate-900/60 rounded-2xl border border-slate-800 space-y-3">
              <AlertCircle className="w-8 h-8 text-slate-500 mx-auto" />
              <p className="text-slate-400 text-sm">수집된 현안 데이터가 없습니다.</p>
              <button
                onClick={handleManualSync}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition"
              >
                지금 수집 및 AI 분석 시작
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {issues.map((issue) => (
                <IssueComparisonCard key={issue.id} issue={issue} />
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-slate-800/80 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>대한민국 6대 정치·시사 커뮤니티 인기 게시판(30선) 실시간 모니터링 시스템 • Powered by Gemini AI & FastAPI</p>
      </footer>

      {/* Community Feed Modal */}
      <CommunityFeedModal
        isOpen={feedModalOpen}
        onClose={() => setFeedModalOpen(false)}
        communities={communities}
        feed={feed}
      />
    </div>
  );
};
