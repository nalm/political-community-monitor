import asyncio
from datetime import datetime
from typing import Dict, Any
from .scrapers import get_all_scrapers
from .database import (
    save_posts_batch,
    get_recent_posts_by_community,
    save_issue_and_stances,
    init_db
)
from .analyzer.llm_client import LLMAnalyzer

analyzer = LLMAnalyzer()

async def run_full_sync() -> Dict[str, Any]:
    """지정된 6대 커뮤니티 인기 게시판에서 최근 30개 게시물을 수집하고 LLM 여론 분석을 실행합니다."""
    init_db()
    scrapers = get_all_scrapers()
    print(f"[{datetime.now().isoformat()}] Starting 30 hot posts sync across {len(scrapers)} sources...")

    posts_collected_stats = {}
    
    # 1. 각 커뮤니티별 인기 게시판 30개 게시물 수집
    for comm_id, scraper in scrapers.items():
        try:
            hot_posts = await scraper.fetch_hot_posts(limit=30)
            saved_count = save_posts_batch(hot_posts)
            posts_collected_stats[comm_id] = saved_count
            print(f"[{comm_id}] Successfully collected & saved {saved_count} hot posts.")
        except Exception as e:
            print(f"Error scraping {comm_id}: {e}")
            posts_collected_stats[comm_id] = 0

    # 2. DB에서 최근 수집된 각 커뮤니티 30개 게시물 조회
    all_recent_posts = get_recent_posts_by_community(limit=30)
    
    # 3. LLM 현안 분석 및 커뮤니티별 스탠스 도출
    print("Running LLM analysis on 30 hot posts per community...")
    analyzed_issues = await analyzer.analyze_issues_and_stances(all_recent_posts)

    # 4. 분석 결과 DB 저장
    saved_issue_ids = []
    for issue_item in analyzed_issues:
        stances = issue_item.get("stances", [])
        issue_id = save_issue_and_stances(issue_item, stances)
        saved_issue_ids.append(issue_id)

    print(f"Sync complete. Created/Updated {len(saved_issue_ids)} issues.")
    return {
        "status": "success",
        "synced_at": datetime.now().isoformat(),
        "stats": posts_collected_stats,
        "issue_count": len(saved_issue_ids)
    }
