import { AnalyzeResult, Community, Post } from '../types';

const API_BASE = '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    let detail = '';
    try {
      detail = (await res.json())?.detail ?? '';
    } catch {
      /* 본문이 JSON 이 아니면 무시 */
    }
    throw new Error(detail || `요청에 실패했습니다. (HTTP ${res.status})`);
  }
  return res.json();
}

export function getCommunities(): Promise<Community[]> {
  return request<Community[]>('/communities');
}

/** 커뮤니티 한 곳을 수집한다. 커뮤니티마다 따로 호출해 진행 상황을 개별로 표시한다. */
export function collectCommunity(
  communityId: string
): Promise<{ community_id: string; count: number; posts: Post[] }> {
  return request(`/collect?community=${encodeURIComponent(communityId)}`);
}

/** 수집한 게시물을 보내 현안 분석을 받는다. 서버는 상태를 보관하지 않는다. */
export function analyzePosts(
  postsByCommunity: Record<string, Post[]>
): Promise<AnalyzeResult> {
  return request<AnalyzeResult>('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ posts_by_community: postsByCommunity }),
  });
}
