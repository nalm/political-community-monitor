import React, { useState } from 'react';
import { Community, Post } from '../types';
import { CommunityBadge } from './CommunityBadge';
import { X, ExternalLink, ThumbsUp, MessageSquare, Eye, Flame } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  communities: Community[];
  feed: Record<string, Post[]>;
}

export const CommunityFeedModal: React.FC<Props> = ({ isOpen, onClose, communities, feed }) => {
  const [activeCommunityId, setActiveCommunityId] = useState<string>(communities[0]?.id || 'itssa');

  if (!isOpen) return null;

  const currentPosts = feed[activeCommunityId] || [];
  const activeCommunity = communities.find(c => c.id === activeCommunityId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-5xl h-[88vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/80">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Flame className="w-5 h-5 text-rose-500" />
              수집된 원문 게시물
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              이번 새로고침에서 각 커뮤니티 인기 게시판의 공지를 제외하고 수집한 최신 게시물입니다.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Community Tabs */}
        <div className="flex overflow-x-auto px-6 py-3 gap-2 border-b border-slate-800 bg-slate-950/60 shrink-0">
          {communities.map((comm) => (
            <button
              key={comm.id}
              onClick={() => setActiveCommunityId(comm.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition border ${
                activeCommunityId === comm.id
                  ? 'bg-slate-800 text-white border-slate-600 shadow-md'
                  : 'bg-slate-900/40 text-slate-400 border-transparent hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <span>{comm.name}</span>
              <span className="text-[11px] opacity-75 font-normal">({feed[comm.id]?.length || 0}개)</span>
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {activeCommunity && (
            <div className="p-3.5 rounded-xl bg-slate-800/50 border border-slate-700/80 flex items-center justify-between text-xs text-slate-400 mb-4">
              <div className="flex items-center gap-2.5">
                <CommunityBadge communityId={activeCommunity.id} name={activeCommunity.name} tag={activeCommunity.tag} />
                <span>게시판: <strong className="text-slate-200">{activeCommunity.section}</strong></span>
                <span>•</span>
                <span>성향: <strong className="text-slate-200">{activeCommunity.bias}</strong></span>
              </div>
              <a
                href={activeCommunity.list_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-blue-400 hover:underline font-semibold"
              >
                인기 게시판 바로가기 <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          )}

          {currentPosts.length === 0 ? (
            <div className="text-center py-16 text-slate-500 text-sm">
              수집된 인기 게시물이 없습니다. '인기글 실시간 새로고침'을 눌러주세요.
            </div>
          ) : (
            currentPosts.map((post, idx) => (
              <div
                key={post.url || idx}
                className="flex items-center justify-between gap-4 p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/60 hover:border-slate-500 transition hover:bg-slate-800/70"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <span className="shrink-0 w-6 text-center text-xs font-bold text-slate-500 mt-0.5">
                    {idx + 1}
                  </span>
                  <div className="min-w-0">
                    <h4 className="text-sm font-semibold text-slate-100 hover:text-blue-300 transition truncate leading-snug">
                      <a href={post.url} target="_blank" rel="noreferrer">
                        {post.title}
                      </a>
                    </h4>
                    <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-1">
                      <span>작성자: {post.author}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1 text-blue-400 font-semibold">
                        <ThumbsUp className="w-3 h-3" /> {post.vote_count}
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1 text-emerald-400">
                        <MessageSquare className="w-3 h-3" /> {post.comment_count}
                      </span>
                      {post.view_count > 0 && (
                        <>
                          <span>•</span>
                          <span className="flex items-center gap-1 text-slate-400">
                            <Eye className="w-3 h-3" /> {post.view_count.toLocaleString()}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <a
                  href={post.url}
                  target="_blank"
                  rel="noreferrer"
                  className="shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-700/60 hover:bg-slate-700 text-blue-300 text-xs font-medium transition"
                >
                  원문 <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
