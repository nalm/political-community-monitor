import asyncio
from datetime import datetime
from typing import Any, Dict

from . import jobs
from .analyzer.llm_client import LLMAnalyzer
from .database import get_posts_by_run, init_db, save_issue_and_stances, save_posts_batch
from .scrapers import get_all_scrapers

analyzer = LLMAnalyzer()

POSTS_PER_COMMUNITY = 30


async def _collect_one(job_id: str, run_id: str, comm_id: str, scraper) -> int:
    """커뮤니티 하나를 수집한다. 실패해도 예외를 밖으로 던지지 않고 job 에 기록한다."""
    jobs.mark_community(job_id, comm_id, jobs.STATUS_COLLECTING)
    try:
        posts = await scraper.fetch_hot_posts(limit=POSTS_PER_COMMUNITY)
        saved = save_posts_batch(posts, run_id)
        jobs.mark_community(job_id, comm_id, jobs.STATUS_OK, count=saved)
        print(f"[{comm_id}] {saved}개 수집 완료")
        return saved
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        jobs.mark_community(job_id, comm_id, jobs.STATUS_ERROR, error=msg)
        print(f"[{comm_id}] 수집 실패 - {msg}")
        return 0


async def run_full_sync(job_id: str) -> Dict[str, Any]:
    """수집 → 분석 → 저장. 진행 상황은 jobs 모듈에 기록해 프론트가 폴링한다."""
    job = jobs.get_job(job_id)
    if job is None:
        raise ValueError(f"unknown job_id: {job_id}")
    run_id = job["run_id"]

    init_db()
    scrapers = get_all_scrapers()
    print(f"[{datetime.now().isoformat()}] {len(scrapers)}개 커뮤니티 수집 시작 (run={run_id})")

    # 1. 커뮤니티별 수집 (병렬)
    jobs.set_phase(job_id, jobs.PHASE_COLLECTING)
    await asyncio.gather(*(
        _collect_one(job_id, run_id, comm_id, scraper)
        for comm_id, scraper in scrapers.items()
    ))

    collected = get_posts_by_run(run_id)
    if not any(collected.values()):
        jobs.set_phase(job_id, jobs.PHASE_ERROR,
                       error="모든 커뮤니티에서 게시글을 수집하지 못했습니다.")
        return {"status": "error", "run_id": run_id}

    # 2. 현안 분석
    jobs.set_phase(job_id, jobs.PHASE_ANALYZING)
    try:
        analyzed, method, note = await analyzer.analyze_issues_and_stances(collected)
    except Exception as e:
        jobs.set_phase(job_id, jobs.PHASE_ERROR, error=f"분석 실패 - {type(e).__name__}: {e}")
        return {"status": "error", "run_id": run_id}

    if not analyzed:
        jobs.set_phase(job_id, jobs.PHASE_ERROR,
                       error="수집된 게시글에서 공통 현안을 추출하지 못했습니다.")
        return {"status": "error", "run_id": run_id}

    # 3. 저장
    for issue_item in analyzed:
        save_issue_and_stances(issue_item, issue_item.get("stances", []), run_id)

    job["analysis_method"] = method
    job["analysis_note"] = note
    jobs.set_phase(job_id, jobs.PHASE_DONE, issue_count=len(analyzed))
    print(f"동기화 완료: 현안 {len(analyzed)}건 (분석 엔진={method})")

    return {
        "status": "success",
        "run_id": run_id,
        "issue_count": len(analyzed),
        "analysis_method": method,
    }
