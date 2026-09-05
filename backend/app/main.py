import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Dict, Any

from .config import COMMUNITIES
from .database import (
    init_db,
    get_all_issues_with_stances,
    get_recent_posts_by_community
)
from .scheduler import run_full_sync

app = FastAPI(
    title="Political Community Monitor API",
    description="대한민국 주요 시사·정치 커뮤니티(에펨코리아, 보배드림, 더쿠, 다모앙, 딴지일보, 잇싸 등) 반응 모니터링 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 앱 시작 시 DB 초기화 및 초기 데이터 확인
@app.on_event("startup")
async def on_startup():
    init_db()
    # 초기 데이터가 없으면 백그라운드로 1회 동기화
    issues = get_all_issues_with_stances()
    if not issues:
        print("No issues found in DB. Triggering initial sync...")
        asyncio.create_task(run_full_sync())

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "political-community-monitor"}

@app.get("/api/communities")
def get_communities():
    """모니터링 대상 커뮤니티 목록 및 메타데이터 반환"""
    return list(COMMUNITIES.values())

@app.get("/api/issues")
def get_issues():
    """정치 현안별 커뮤니티 반응 및 비교 분석 데이터 반환"""
    issues = get_all_issues_with_stances()
    return {"issues": issues, "total": len(issues)}

@app.get("/api/community-feed")
def get_community_feed(limit: int = 10):
    """각 커뮤니티별 실시간 수집된 인기글과 인기 댓글 5개 반환"""
    data = get_recent_posts_by_community(limit=limit)
    return {"feed": data}

@app.post("/api/sync")
async def trigger_sync(background_tasks: BackgroundTasks):
    """실시간 여론 수집 및 AI 분석 수동 실행 엔드포인트"""
    background_tasks.add_task(run_full_sync)
    return {
        "message": "수집 및 AI 분석 작업이 백그라운드에서 시작되었습니다.",
        "status": "triggered"
    }

# 프론트엔드 정적 빌드 서빙 (빌드된 경우)
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
