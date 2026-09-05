import React from 'react';
import { RefreshCw, Activity, Landmark } from 'lucide-react';

interface Props {
  onRefresh: () => void;
  isSyncing: boolean;
  onOpenFeedModal: () => void;
  /** 수집이 끝나 원문 탐색기를 열 수 있는 상태인지 */
  canOpenFeed: boolean;
}

export const Header: React.FC<Props> = ({ onRefresh, isSyncing, onOpenFeedModal, canOpenFeed }) => {
  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Landmark className="w-4.5 h-4.5 text-white" />
          </div>
          <h1 className="text-base font-extrabold text-white tracking-tight">
            정치·시사 여론 레이더 <span className="text-indigo-400">POLI-RADAR</span>
          </h1>
        </div>

        <div className="flex items-center gap-2.5">
          {canOpenFeed && (
            <button
              onClick={onOpenFeedModal}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
            >
              <Activity className="w-4 h-4 text-blue-400" />
              수집된 원문 보기
            </button>
          )}

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
            {isSyncing ? '수집·분석 중…' : '인기글 실시간 새로고침'}
          </button>
        </div>
      </div>
    </header>
  );
};
