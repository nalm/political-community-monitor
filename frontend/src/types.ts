export interface Community {
  id: string;
  name: string;
  section: string;
  base_url: string;
  list_url: string;
  bias: string;
  demographic: string;
  color: string;
  tag: string;
}

export interface Post {
  community_id: string;
  original_id: string;
  title: string;
  url: string;
  author: string;
  view_count: number;
  vote_count: number;
  comment_count: number;
}

export interface Stance {
  community_id: string;
  community_name: string;
  bias: string;
  demographic: string;
  color: string;
  tag: string;
  stance_label: string;
  sentiment_score: number; // -1.0 ~ 1.0
  summary_points: string[];
  keywords: string[];
  representative_posts: string[];
  post_count: number;
  total_votes?: number;
}

export interface Issue {
  title: string;
  category: string;
  summary: string;
  key_dispute: string;
  stances: Stance[];
}

/** 화면 단계 */
export type Phase = 'idle' | 'collecting' | 'analyzing' | 'report' | 'error';

/** 커뮤니티 한 곳의 수집 상태. 서버가 아니라 클라이언트가 요청 결과로 직접 채운다. */
export interface CommunityProgress {
  community_id: string;
  name: string;
  color: string;
  status: 'pending' | 'collecting' | 'ok' | 'error';
  count: number;
  error: string | null;
}

export interface AnalyzeResult {
  issues: Issue[];
  /** 'gemini' 또는 'heuristic' */
  analysis_method: string;
  /** 휴리스틱으로 내려간 경우 그 사유 */
  analysis_note: string;
}
