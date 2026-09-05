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
  id: number;
  community_id: string;
  original_id: string;
  title: string;
  content?: string;
  author: string;
  url: string;
  view_count: number;
  vote_count: number;
  comment_count: number;
  collected_at: string;
}

export interface Stance {
  id?: number;
  issue_id: number;
  community_id: string;
  community_name: string;
  bias: string;
  demographic: string;
  color: string;
  tag: string;
  stance_label: string;
  sentiment_score: number; // -1.0 to 1.0
  summary_points: string[];
  keywords: string[];
  representative_posts: string[];
  post_count: number;
  total_votes: number;
  updated_at: string;
}

export interface Issue {
  id: number;
  title: string;
  category: string;
  summary: string;
  key_dispute: string;
  created_at: string;
  updated_at: string;
  stances: Stance[];
}
