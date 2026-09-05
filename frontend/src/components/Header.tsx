import React from 'react';
import { RefreshCw, Activity, Landmark } from 'lucide-react';

interface Props {
  onRefresh: () => void;
  isSyncing: boolean;
  lastSyncedAt?: string;
  onOpenFeedModal: () => void;
}

export const Header: React.FC<Props> = ({ onRefresh, isSyncing, lastSyncedAt, onOpenFeedModal }) => {
  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Landmark className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-extrabold text-white tracking-tight">
                정치·시사 여론 레이더 <span className="text-indigo-400">POLI-RADAR</span>
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                인기 게시판 30선 실시간 연동
              </span>
            </div>
            <p className="text-xs text-slate-400">
              잇싸(정치HOT) · 펨코(정치인기) · 보배(정치베스트) · 더쿠(스퀘어HOT) · 다모앙(공감) · 딴지(HOTBEST) 30개 게시물 심층 분석
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenFeedModal}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition shadow-sm"
          >
            <Activity className="w-4 h-4 text-blue-400" />
            수집된 30대 인기글 탐색기
          </button>

          <button
            onClick={onRefresh}
            disabled={isSyncing}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-white shadow-lg transition ${
              isSyncing
                ? 'bg-indigo-600/50 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-500 active:scale-95 shadow-indigo-600/30'
            }`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? '30개 인기글 수집 & AI 분석 중...' : '인기글 실시간 새로고침'}
          </button>
        </div>
      </div>
    </header>
  );
};
