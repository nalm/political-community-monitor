import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import jobs
from .config import COMMUNITIES
from .database import get_issues_by_run, get_posts_by_run, init_db
from .scheduler import run_full_sync

app = FastAPI(
    title="Political Community Monitor API",
    description="시사·정치 커뮤니티(잇싸, 보배드림, 더쿠, 딴지일보) 여론 모니터링",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    # DB 스키마만 준비한다. 수집은 사용자가 '새로고침' 을 눌렀을 때만 시작한다.
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "political-community-monitor"}


@app.get("/api/communities")
def get_communities():
    """모니터링 대상 커뮤니티 목록 및 메타데이터"""
    return list(COMMUNITIES.values())


@app.post("/api/sync")
async def trigger_sync():
    """지금 이 시각 기준으로 수집·분석을 시작하고 job_id 를 돌려준다."""
    running = jobs.latest_job()
    if running and running["phase"] in (jobs.PHASE_COLLECTING, jobs.PHASE_ANALYZING):
        # 이미 돌고 있으면 새로 띄우지 않고 진행 중인 작업에 붙인다.
        return {"job_id": running["job_id"], "already_running": True}

    job = jobs.create_job(list(COMMUNITIES.keys()))
    asyncio.create_task(run_full_sync(job["job_id"]))
    return {"job_id": job["job_id"], "already_running": False}


@app.get("/api/sync/{job_id}")
def get_sync_status(job_id: str):
    """수집·분석 진행 상황. 프론트가 폴링한다."""
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="해당 작업을 찾을 수 없습니다.")

    return {
        "job_id": job["job_id"],
        "run_id": job["run_id"],
        "phase": job["phase"],
        "started_at": job["started_at"],
        "finished_at": job["finished_at"],
        "error": job["error"],
        "issue_count": job["issue_count"],
        "total_posts": job["total_posts"],
        "analysis_method": job.get("analysis_method"),
        "analysis_note": job.get("analysis_note"),
        "communities": [
            {**entry, "name": COMMUNITIES[cid]["name"], "color": COMMUNITIES[cid]["color"]}
            for cid, entry in job["communities"].items()
            if cid in COMMUNITIES
        ],
    }


@app.get("/api/issues")
def get_issues(run_id: Optional[str] = None):
    """현안별 커뮤니티 반응 리포트. run_id 를 주면 그 실행 결과만 반환."""
    issues = get_issues_by_run(run_id)
    return {"issues": issues, "total": len(issues), "run_id": run_id}


@app.get("/api/community-feed")
def get_community_feed(run_id: str):
    """해당 실행에서 수집된 커뮤니티별 게시글 원문 목록"""
    return {"feed": get_posts_by_run(run_id)}


# 프론트엔드 정적 빌드 서빙 (빌드된 경우)
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
