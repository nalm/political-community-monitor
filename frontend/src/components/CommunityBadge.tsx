import React from 'react';

interface Props {
  communityId: string;
  name: string;
  tag?: string;
  className?: string;
}

export const CommunityBadge: React.FC<Props> = ({ communityId, name, tag, className = '' }) => {
  const getBadgeStyle = (id: string) => {
    switch (id) {
      case 'bobaedream':
        return 'bg-emerald-900/60 text-emerald-300 border-emerald-700/80';
      case 'theqoo':
        return 'bg-pink-900/60 text-pink-300 border-pink-700/80';
      case 'ddanzi':
        return 'bg-amber-900/60 text-amber-300 border-amber-700/80';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${getBadgeStyle(communityId)} ${className}`}>
      <span>{name}</span>
      {tag && <span className="opacity-75 font-normal text-[11px]">| {tag}</span>}
    </div>
  );
};
