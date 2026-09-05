import { Community, Issue, Post } from '../types';

const API_BASE = '/api';

export async function getCommunities(): Promise<Community[]> {
  const res = await fetch(`${API_BASE}/communities`);
  if (!res.ok) throw new Error('커뮤니티 목록을 불러오지 못했습니다.');
  return res.json();
}

export async function getIssues(): Promise<{ issues: Issue[]; total: number }> {
  const res = await fetch(`${API_BASE}/issues`);
  if (!res.ok) throw new Error('이슈 분석 데이터를 불러오지 못했습니다.');
  return res.json();
}

export async function getCommunityFeed(limit: number = 10): Promise<{ feed: Record<string, Post[]> }> {
  const res = await fetch(`${API_BASE}/community-feed?limit=${limit}`);
  if (!res.ok) throw new Error('커뮤니티 피드를 불러오지 못했습니다.');
  return res.json();
}

export async function triggerSync(): Promise<{ message: string; status: string }> {
  const res = await fetch(`${API_BASE}/sync`, { method: 'POST' });
  if (!res.ok) throw new Error('수집 요청에 실패했습니다.');
  return res.json();
}
