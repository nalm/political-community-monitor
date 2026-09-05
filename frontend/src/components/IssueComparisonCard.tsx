import React, { useState } from 'react';
import { Issue, Stance } from '../types';
import { CommunityBadge } from './CommunityBadge';
import { SentimentBar } from './SentimentBar';
import { Scale, FileText, Tag, ChevronDown, ChevronUp, Sparkles, Flame } from 'lucide-react';

interface Props {
  issue: Issue;
}

export const IssueComparisonCard: React.FC<Props> = ({ issue }) => {
  const [expanded, setExpanded] = useState<boolean>(true);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');

  const filteredStances = issue.stances.filter(s => {
    if (selectedFilter === 'all') return true;
    if (selectedFilter === 'progressive') {
      return ['bobaedream', 'ddanzi', 'itssa', 'damoang'].includes(s.community_id);
    }
    if (selectedFilter === 'conservative') {
      return ['fmkorea'].includes(s.community_id);
    }
    if (selectedFilter === 'neutral_female') {
      return ['theqoo'].includes(s.community_id);
    }
    return true;
  });

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-xl backdrop-blur-sm transition-all hover:border-slate-600">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-5">
        <div>
          <div className="flex items-center gap-2.5 mb-2">
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
              {issue.category || '정치/시사'}
            </span>
            <span className="text-xs text-slate-400">
              분석 시점: {new Date(issue.updated_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Scale className="w-6 h-6 text-amber-400 shrink-0" />
            {issue.title}
          </h2>
          <p className="text-slate-300 text-sm mt-2 leading-relaxed max-w-4xl">
            {issue.summary}
          </p>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="self-start md:self-center flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-700/60 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
        >
          {expanded ? (
            <>접기 <ChevronUp className="w-4 h-4" /></>
          ) : (
            <>자세히 보기 <ChevronDown className="w-4 h-4" /></>
          )}
        </button>
      </div>

      {/* Key Dispute Callout */}
      {issue.key_dispute && (
        <div className="mt-4 p-3.5 rounded-xl bg-amber-950/30 border border-amber-800/50 flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-200/90 leading-relaxed">
            <strong className="text-amber-300 font-semibold block mb-0.5">핵심 쟁점 및 진영별 시각차:</strong>
            {issue.key_dispute}
          </div>
        </div>
      )}

      {expanded && (
        <>
          {/* Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 mt-6 mb-4">
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-slate-400 mr-1">성향별 보기:</span>
              <button
                onClick={() => setSelectedFilter('all')}
                className={`px-3 py-1 rounded-full font-medium transition ${
                  selectedFilter === 'all'
                    ? 'bg-slate-200 text-slate-900 font-bold'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                전체 커뮤니티 ({issue.stances.length})
              </button>
              <button
                onClick={() => setSelectedFilter('conservative')}
                className={`px-3 py-1 rounded-full font-medium transition ${
                  selectedFilter === 'conservative'
                    ? 'bg-blue-600 text-white font-bold'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                보수/2030남 (에펨코리아)
              </button>
              <button
                onClick={() => setSelectedFilter('progressive')}
                className={`px-3 py-1 rounded-full font-medium transition ${
                  selectedFilter === 'progressive'
                    ? 'bg-indigo-600 text-white font-bold'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                진보/팬덤 (잇싸·보배·딴지·다모앙)
              </button>
              <button
                onClick={() => setSelectedFilter('neutral_female')}
                className={`px-3 py-1 rounded-full font-medium transition ${
                  selectedFilter === 'neutral_female'
                    ? 'bg-pink-600 text-white font-bold'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                2030여성 (더쿠)
              </button>
            </div>
          </div>

          {/* Stances Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-4">
            {filteredStances.map((stance) => (
              <div
                key={stance.community_id}
                className="flex flex-col justify-between bg-slate-900/90 border border-slate-700/80 rounded-xl p-4 transition-all hover:border-slate-500 hover:shadow-lg"
              >
                <div>
                  {/* Community Header */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <CommunityBadge
                      communityId={stance.community_id}
                      name={stance.community_name}
                      tag={stance.tag}
                    />
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {stance.stance_label}
                    </span>
                  </div>

                  {/* Sentiment Bar */}
                  <div className="mb-4">
                    <SentimentBar score={stance.sentiment_score} />
                  </div>

                  {/* 3-line Bullet Summaries */}
                  <div className="space-y-1.5 mb-4">
                    <div className="text-xs font-semibold text-slate-300 flex items-center gap-1 mb-1">
                      <span>인기글 30선 핵심 기조:</span>
                    </div>
                    {stance.summary_points?.map((point, idx) => (
                      <div key={idx} className="flex items-start gap-1.5 text-xs text-slate-300 leading-relaxed">
                        <span className="text-indigo-400 font-bold shrink-0 mt-0.5">•</span>
                        <span>{point}</span>
                      </div>
                    ))}
                  </div>

                  {/* Representative Hot Posts */}
                  {stance.representative_posts && stance.representative_posts.length > 0 && (
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 mb-3">
                      <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-400 mb-1">
                        <Flame className="w-3.5 h-3.5 text-rose-400" />
                        <span>대표 인기 게시글:</span>
                      </div>
                      {stance.representative_posts.map((postTitle, pIdx) => (
                        <p key={pIdx} className="text-[11px] text-slate-300 pl-2 border-l-2 border-slate-700 my-1 leading-snug">
                          {postTitle}
                        </p>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  {/* Keywords */}
                  {stance.keywords && stance.keywords.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-800">
                      <Tag className="w-3 h-3 text-slate-500" />
                      {stance.keywords.map((kw, kwIdx) => (
                        <span
                          key={kwIdx}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50"
                        >
                          #{kw}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
