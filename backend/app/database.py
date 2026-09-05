import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from .config import DB_PATH, COMMUNITIES

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. 커뮤니티 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS communities (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        section TEXT NOT NULL,
        base_url TEXT NOT NULL,
        list_url TEXT NOT NULL,
        bias TEXT,
        demographic TEXT,
        color TEXT,
        tag TEXT
    )
    """)

    # 2. 인기 게시글 테이블 (최근 30개 수집)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        community_id TEXT NOT NULL,
        original_id TEXT,
        title TEXT NOT NULL,
        content TEXT,
        author TEXT,
        url TEXT UNIQUE NOT NULL,
        view_count INTEGER DEFAULT 0,
        vote_count INTEGER DEFAULT 0,
        comment_count INTEGER DEFAULT 0,
        post_created_at TEXT,
        collected_at TEXT NOT NULL,
        FOREIGN KEY (community_id) REFERENCES communities (id)
    )
    """)

    # 3. 종합 정치 현안/이슈 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT DEFAULT '정치/사회',
        summary TEXT,
        key_dispute TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # 4. 이슈별 커뮤니티 반응/스탠스 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS issue_community_stances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER NOT NULL,
        community_id TEXT NOT NULL,
        stance_label TEXT,
        sentiment_score REAL,
        summary_points TEXT,
        keywords TEXT,
        representative_posts TEXT,
        post_count INTEGER DEFAULT 0,
        total_votes INTEGER DEFAULT 0,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (issue_id) REFERENCES issues (id) ON DELETE CASCADE,
        FOREIGN KEY (community_id) REFERENCES communities (id)
    )
    """)

    # 기본 커뮤니티 데이터 시드
    for comm_id, comm in COMMUNITIES.items():
        cursor.execute("""
        INSERT OR REPLACE INTO communities 
        (id, name, section, base_url, list_url, bias, demographic, color, tag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comm["id"], comm["name"], comm["section"], comm["base_url"],
            comm["list_url"], comm["bias"], comm["demographic"], comm["color"], comm["tag"]
        ))

    conn.commit()
    conn.close()

def save_posts_batch(posts_data: List[Dict[str, Any]]) -> int:
    """수집된 30개 게시글 일괄 저장 및 갱신"""
    if not posts_data:
        return 0
    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    saved = 0

    for p in posts_data:
        cursor.execute("""
        INSERT INTO posts (community_id, original_id, title, content, author, url, 
                           view_count, vote_count, comment_count, post_created_at, collected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            title=excluded.title,
            view_count=excluded.view_count,
            vote_count=excluded.vote_count,
            comment_count=excluded.comment_count,
            collected_at=excluded.collected_at
        """, (
            p.get("community_id"),
            p.get("original_id"),
            p.get("title"),
            p.get("content", ""),
            p.get("author", "익명"),
            p.get("url"),
            p.get("view_count", 0),
            p.get("vote_count", 0),
            p.get("comment_count", 0),
            now_str,
            now_str
        ))
        saved += 1

    conn.commit()
    conn.close()
    return saved

def get_recent_posts_by_community(limit: int = 30) -> Dict[str, List[Dict[str, Any]]]:
    conn = get_db()
    cursor = conn.cursor()
    res = {}
    for comm_id in COMMUNITIES.keys():
        cursor.execute("""
        SELECT * FROM posts WHERE community_id = ? ORDER BY id DESC LIMIT ?
        """, (comm_id, limit))
        res[comm_id] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return res

def save_issue_and_stances(issue_data: Dict[str, Any], stances: List[Dict[str, Any]]) -> int:
    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()

    cursor.execute("""
    INSERT INTO issues (title, category, summary, key_dispute, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        issue_data["title"],
        issue_data.get("category", "정치/시사"),
        issue_data.get("summary", ""),
        issue_data.get("key_dispute", ""),
        now_str,
        now_str
    ))
    issue_id = cursor.lastrowid

    for s in stances:
        cursor.execute("""
        INSERT INTO issue_community_stances 
        (issue_id, community_id, stance_label, sentiment_score, summary_points, keywords, representative_posts, post_count, total_votes, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            issue_id,
            s["community_id"],
            s.get("stance_label", "중립"),
            s.get("sentiment_score", 0.0),
            json.dumps(s.get("summary_points", []), ensure_ascii=False),
            json.dumps(s.get("keywords", []), ensure_ascii=False),
            json.dumps(s.get("representative_posts", s.get("representative_quotes", [])), ensure_ascii=False),
            s.get("post_count", 0),
            s.get("total_votes", 0),
            now_str
        ))

    conn.commit()
    conn.close()
    return issue_id

def get_all_issues_with_stances():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM issues ORDER BY id DESC")
    issues = [dict(r) for r in cursor.fetchall()]

    for issue in issues:
        cursor.execute("""
        SELECT s.*, c.name as community_name, c.bias, c.demographic, c.color, c.tag
        FROM issue_community_stances s
        JOIN communities c ON s.community_id = c.id
        WHERE s.issue_id = ?
        """, (issue["id"],))
        stances = []
        for sr in cursor.fetchall():
            s_dict = dict(sr)
            s_dict["summary_points"] = json.loads(s_dict["summary_points"] or "[]")
            s_dict["keywords"] = json.loads(s_dict["keywords"] or "[]")
            s_dict["representative_posts"] = json.loads(s_dict["representative_posts"] or "[]")
            stances.append(s_dict)
        issue["stances"] = stances

    conn.close()
    return issues
