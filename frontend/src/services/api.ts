import { Community, Issue, Post, SyncJob } from '../types';

const API_BASE = '/api';

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
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
  return getJson<Community[]>('/communities');
}

/** 지금 이 시각 기준으로 수집을 시작하고 job_id 를 받는다. */
export function startSync(): Promise<{ job_id: string; already_running: boolean }> {
  return getJson('/sync', { method: 'POST' });
}

/** 수집·분석 진행 상황을 조회한다. */
export function getSyncStatus(jobId: string): Promise<SyncJob> {
  return getJson<SyncJob>(`/sync/${jobId}`);
}

/** 해당 실행의 분석 리포트를 가져온다. */
export function getIssues(runId: string): Promise<{ issues: Issue[]; total: number }> {
  return getJson(`/issues?run_id=${encodeURIComponent(runId)}`);
}

/** 해당 실행에서 수집된 원문 게시글 목록을 가져온다. */
export function getCommunityFeed(runId: string): Promise<{ feed: Record<string, Post[]> }> {
  return getJson(`/community-feed?run_id=${encodeURIComponent(runId)}`);
}
