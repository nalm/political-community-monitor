"""수집·분석 API.

서버에 공유 상태를 두지 않는다. 커뮤니티 수집은 요청 하나당 한 곳씩 처리하고,
분석은 클라이언트가 모아 보낸 게시물만 가지고 수행한다.

이렇게 한 이유: Vercel 같은 서버리스에서는 요청마다 다른 인스턴스로 갈 수 있어
프로세스 메모리에 담은 작업 상태나 /tmp 의 SQLite 를 다음 요청에서 다시 읽을 수 없다.
진행 상황 표시도 클라이언트가 4개 요청의 완료 여부로 직접 판단하므로 폴링이 필요 없다.
"""

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .analyzer.llm_client import LLMAnalyzer
from .config import COMMUNITIES
from .scrapers import get_scraper

POSTS_PER_COMMUNITY = 30

app = FastAPI(
    title="Political Community Monitor API",
    description="시사·정치 커뮤니티(잇싸, 보배드림, 더쿠, 딴지일보) 여론 모니터링",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = LLMAnalyzer()


class PostIn(BaseModel):
    """분석 요청으로 되돌아오는 게시물. 과도한 입력을 막기 위해 길이를 제한한다."""
    community_id: str = Field(max_length=32)
    title: str = Field(max_length=300)
    url: str = Field(default="", max_length=500)
    author: str = Field(default="", max_length=100)
    view_count: int = 0
    vote_count: int = 0
    comment_count: int = 0


class AnalyzeRequest(BaseModel):
    posts_by_community: Dict[str, List[PostIn]]


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "political-community-monitor"}


@app.get("/api/communities")
def get_communities():
    """모니터링 대상 커뮤니티 목록 및 메타데이터"""
    return list(COMMUNITIES.values())


@app.get("/api/collect")
async def collect(community: str = Query(..., description="커뮤니티 id")):
    """커뮤니티 한 곳의 인기 게시판에서 공지를 제외한 최신 게시물을 수집한다.

    클라이언트가 커뮤니티마다 따로 호출하므로, 한 곳이 실패해도 나머지는 그대로 진행된다.
    """
    if community not in COMMUNITIES:
        raise HTTPException(status_code=404, detail=f"알 수 없는 커뮤니티: {community}")

    scraper = get_scraper(community)
    try:
        posts = await scraper.fetch_hot_posts(limit=POSTS_PER_COMMUNITY)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"{COMMUNITIES[community]['name']} 수집 실패 - {type(e).__name__}: {e}",
        )

    if not posts:
        raise HTTPException(
            status_code=502,
            detail=f"{COMMUNITIES[community]['name']} 에서 게시물을 찾지 못했습니다.",
        )

    return {"community_id": community, "count": len(posts), "posts": posts}


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    """수집된 게시물에서 현안을 추출하고 커뮤니티별 스탠스를 만든다."""
    posts_by_community: Dict[str, List[Dict[str, Any]]] = {}
    for comm_id, posts in req.posts_by_community.items():
        if comm_id not in COMMUNITIES:
            continue
        posts_by_community[comm_id] = [p.model_dump() for p in posts[:POSTS_PER_COMMUNITY]]

    if not any(posts_by_community.values()):
        raise HTTPException(status_code=400, detail="분석할 게시물이 없습니다.")

    issues, method, note = await analyzer.analyze_issues_and_stances(posts_by_community)
    if not issues:
        raise HTTPException(
            status_code=422, detail="수집된 게시물에서 공통 현안을 추출하지 못했습니다."
        )

    # 커뮤니티 메타데이터(이름·색상·성향)를 스탠스에 붙여 프론트가 바로 쓰게 한다.
    for issue in issues:
        for stance in issue.get("stances", []):
            meta = COMMUNITIES.get(stance.get("community_id"), {})
            stance["community_name"] = meta.get("name", stance.get("community_id"))
            stance["bias"] = meta.get("bias", "")
            stance["demographic"] = meta.get("demographic", "")
            stance["color"] = meta.get("color", "#64748B")
            stance["tag"] = meta.get("tag", "")

    return {"issues": issues, "analysis_method": method, "analysis_note": note}


# 프론트엔드 정적 빌드 서빙 (빌드된 경우)
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
