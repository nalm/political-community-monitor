"""수집·분석 작업(Job)의 진행 상태를 추적한다.

프론트엔드가 '수집중 → 분석중 → 리포트' 단계를 실제 진행에 맞춰 보여줄 수 있도록
서버가 단계와 커뮤니티별 진행 상황을 노출한다.

저장소는 프로세스 메모리다. `python run.py` 로 띄우는 단일 프로세스 기준이며,
워커를 여러 개 띄우거나 서버리스로 배포하면 폴링이 다른 워커에 붙어 상태를 잃는다.
그 경우 Redis 등 외부 저장소로 교체해야 한다.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# 단계
PHASE_COLLECTING = "collecting"
PHASE_ANALYZING = "analyzing"
PHASE_DONE = "done"
PHASE_ERROR = "error"

# 커뮤니티별 수집 상태
STATUS_PENDING = "pending"
STATUS_COLLECTING = "collecting"
STATUS_OK = "ok"
STATUS_ERROR = "error"

# 최근 작업만 보관 (메모리 누수 방지)
_MAX_JOBS = 20
_JOBS: Dict[str, Dict[str, Any]] = {}


def _now() -> str:
    return datetime.now().isoformat()


def create_job(community_ids: List[str]) -> Dict[str, Any]:
    job_id = uuid.uuid4().hex
    job = {
        "job_id": job_id,
        "run_id": job_id,          # 이 실행으로 수집된 posts/issues 를 묶는 키
        "phase": PHASE_COLLECTING,
        "started_at": _now(),
        "finished_at": None,
        "error": None,
        "issue_count": 0,
        "total_posts": 0,
        "communities": {
            cid: {"community_id": cid, "status": STATUS_PENDING, "count": 0, "error": None}
            for cid in community_ids
        },
    }
    _JOBS[job_id] = job

    if len(_JOBS) > _MAX_JOBS:
        for stale in sorted(_JOBS, key=lambda k: _JOBS[k]["started_at"])[:-_MAX_JOBS]:
            _JOBS.pop(stale, None)

    return job


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    return _JOBS.get(job_id)


def latest_job() -> Optional[Dict[str, Any]]:
    if not _JOBS:
        return None
    return max(_JOBS.values(), key=lambda j: j["started_at"])


def mark_community(job_id: str, community_id: str, status: str,
                   count: int = 0, error: Optional[str] = None) -> None:
    job = _JOBS.get(job_id)
    if not job:
        return
    entry = job["communities"].get(community_id)
    if entry is None:
        return
    entry["status"] = status
    entry["count"] = count
    entry["error"] = error
    job["total_posts"] = sum(c["count"] for c in job["communities"].values())


def set_phase(job_id: str, phase: str, error: Optional[str] = None,
              issue_count: Optional[int] = None) -> None:
    job = _JOBS.get(job_id)
    if not job:
        return
    job["phase"] = phase
    if error is not None:
        job["error"] = error
    if issue_count is not None:
        job["issue_count"] = issue_count
    if phase in (PHASE_DONE, PHASE_ERROR):
        job["finished_at"] = _now()
