import os
import shutil
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent

if os.environ.get("VERCEL"):
    DATA_DIR = Path("/tmp/data")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "monitor.db"
    bundled_db = BASE_DIR / "data" / "monitor.db"
    if bundled_db.exists() and not DB_PATH.exists():
        shutil.copyfile(bundled_db, DB_PATH)
else:
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "monitor.db"

# 사용자가 지정한 6대 커뮤니티 인기 게시판 URL
COMMUNITIES = {
    "itssa": {
        "id": "itssa",
        "name": "잇싸 (ITSSA)",
        "section": "정치 HOT",
        "base_url": "https://itssa.co.kr",
        "list_url": "https://itssa.co.kr/hot_politics",
        "bias": "친민주·친이재명/이동형",
        "demographic": "3050 고관여 진보",
        "color": "#8B5CF6",
        "tag": "진보 / 잇싸"
    },
    "fmkorea": {
        "id": "fmkorea",
        "name": "에펨코리아",
        "section": "정치/시사 인기글",
        "base_url": "https://www.fmkorea.com",
        "list_url": "https://www.fmkorea.com/index.php?mid=politics&sort_index=pop&order_type=desc",
        "bias": "보수·개혁신당 우호",
        "demographic": "2030 남성",
        "color": "#3B82F6",
        "tag": "2030 남성 / 보수"
    },
    "bobaedream": {
        "id": "bobaedream",
        "name": "보배드림",
        "section": "정치 추천/베스트",
        "base_url": "https://www.bobaedream.co.kr",
        "list_url": "https://www.bobaedream.co.kr/list?code=politic&s_cate=1",
        "bias": "진보·민주당 우호",
        "demographic": "3050 남성",
        "color": "#10B981",
        "tag": "3050 남성 / 진보"
    },
    "theqoo": {
        "id": "theqoo",
        "name": "더쿠",
        "section": "스퀘어 핫이슈",
        "base_url": "https://theqoo.net",
        "list_url": "https://theqoo.net/square/category/3836759081?filter_mode=hot",
        "bias": "중도진보 / 사안별 실용",
        "demographic": "2030 여성",
        "color": "#EC4899",
        "tag": "2030 여성 / 중도진보"
    },
    "damoang": {
        "id": "damoang",
        "name": "다모앙",
        "section": "공감게시판",
        "base_url": "https://damoang.net",
        "list_url": "https://damoang.net/empathy",
        "bias": "진보·민주당 우호",
        "demographic": "4050 IT/직장인",
        "color": "#6366F1",
        "tag": "4050 세대 / 진보"
    },
    "ddanzi": {
        "id": "ddanzi",
        "name": "딴지일보",
        "section": "HOT/HOTBEST 자유게시판",
        "base_url": "https://www.ddanzi.com",
        "list_url": "https://www.ddanzi.com/index.php?mid=free&statusList=HOT%2CHOTBEST%2CHOTAC%2CHOTBESTAC",
        "bias": "친민주·친김어준 진보",
        "demographic": "4050 고관여 진보",
        "color": "#F59E0B",
        "tag": "진보 / 딴지"
    }
}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
