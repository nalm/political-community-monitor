import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from .config import DB_PATH, COMMUNITIES


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(cursor, table: str, column: str, ddl: str) -> None:
    """이미 만들어진 DB에도 컬럼을 안전하게 추가한다(멱등)."""
    existing = {r["name"] for r in cursor.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


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

    # 2. 수집된 게시글 테이블
    #    post_created_at: 목록에 '3일 전 23:39' 처럼 상대 시각으로만 노출되는 사이트가 있어
    #    신뢰할 수 있는 게시 시각을 얻지 못한다. 채우지 않고 비워 둔다.
    #    최신순 정렬은 게시물 번호(original_id) 기준으로 수집 단계에서 이미 처리한다.
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

    # 3. 정치 현안/이슈 테이블
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

    # 한 번의 '새로고침' 으로 수집/분석된 결과를 묶는 키
    _ensure_column(cursor, "posts", "sync_run_id", "TEXT")
    _ensure_column(cursor, "issues", "sync_run_id", "TEXT")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_run ON posts (sync_run_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_issues_run ON issues (sync_run_id)")

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

    # 수집 대상에서 제외된 커뮤니티(에펨코리아·다모앙)의 잔여 데이터 제거.
    # 해당 데이터는 스크레이핑이 차단됐을 때 코드에 하드코딩돼 있던 가짜 게시글이라
    # 남겨두면 분석 결과를 오염시킨다.
    active = tuple(COMMUNITIES.keys())
    placeholders = ",".join("?" * len(active))
    cursor.execute(f"DELETE FROM posts WHERE community_id NOT IN ({placeholders})", active)
    cursor.execute(f"DELETE FROM issue_community_stances WHERE community_id NOT IN ({placeholders})", active)
    cursor.execute(f"DELETE FROM communities WHERE id NOT IN ({placeholders})", active)
    # 스탠스가 하나도 남지 않은 이슈는 함께 정리
    cursor.execute("""
        DELETE FROM issues
        WHERE id NOT IN (SELECT DISTINCT issue_id FROM issue_community_stances)
    """)

    conn.commit()
    conn.close()


def save_posts_batch(posts_data: List[Dict[str, Any]], run_id: str) -> int:
    """수집된 게시글을 일괄 저장/갱신하고 이번 실행(run_id)에 묶는다."""
    if not posts_data:
        return 0
    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    saved = 0

    for p in posts_data:
        cursor.execute("""
        INSERT INTO posts (community_id, original_id, title, content, author, url,
                           view_count, vote_count, comment_count, collected_at, sync_run_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            title=excluded.title,
            view_count=excluded.view_count,
            vote_count=excluded.vote_count,
            comment_count=excluded.comment_count,
            collected_at=excluded.collected_at,
            sync_run_id=excluded.sync_run_id
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
            run_id,
        ))
        saved += 1

    conn.commit()
    conn.close()
    return saved


def get_posts_by_run(run_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """이번 실행에서 수집된 게시글만 커뮤니티별로 반환 (게시물 번호 내림차순 = 최신순)."""
    conn = get_db()
    cursor = conn.cursor()
    res: Dict[str, List[Dict[str, Any]]] = {}
    for comm_id in COMMUNITIES.keys():
        cursor.execute("""
        SELECT * FROM posts
        WHERE community_id = ? AND sync_run_id = ?
        ORDER BY CAST(original_id AS INTEGER) DESC
        """, (comm_id, run_id))
        res[comm_id] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return res


def save_issue_and_stances(issue_data: Dict[str, Any], stances: List[Dict[str, Any]],
                           run_id: str) -> int:
    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()

    cursor.execute("""
    INSERT INTO issues (title, category, summary, key_dispute, created_at, updated_at, sync_run_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        issue_data["title"],
        issue_data.get("category", "정치/시사"),
        issue_data.get("summary", ""),
        issue_data.get("key_dispute", ""),
        now_str,
        now_str,
        run_id,
    ))
    issue_id = cursor.lastrowid

    for s in stances:
        if s.get("community_id") not in COMMUNITIES:
            continue
        cursor.execute("""
        INSERT INTO issue_community_stances
        (issue_id, community_id, stance_label, sentiment_score, summary_points, keywords,
         representative_posts, post_count, total_votes, updated_at)
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
            now_str,
        ))

    conn.commit()
    conn.close()
    return issue_id


def get_issues_by_run(run_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """run_id 를 주면 해당 실행의 리포트만, 없으면 가장 최근 실행의 리포트를 반환."""
    conn = get_db()
    cursor = conn.cursor()

    if run_id is None:
        row = cursor.execute(
            "SELECT sync_run_id FROM issues WHERE sync_run_id IS NOT NULL ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            conn.close()
            return []
        run_id = row["sync_run_id"]

    issues = [dict(r) for r in cursor.execute(
        "SELECT * FROM issues WHERE sync_run_id = ? ORDER BY id DESC", (run_id,)
    )]

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
