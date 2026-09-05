import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

if os.environ.get("VERCEL"):
    # 서버리스에서는 /tmp 만 쓸 수 있고 인스턴스마다 별개다.
    # 스키마는 startup 에서 생성하며, 수집 데이터는 인스턴스 수명만큼만 유지된다.
    DATA_DIR = Path("/tmp/data")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "monitor.db"
else:
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "monitor.db"

# 모니터링 대상 커뮤니티 인기 게시판 URL
#
# 아래 세 곳은 수집 대상에서 제외되었습니다. 모두 인프라 레벨에서 자동 수집을
# 거부하므로 우회하지 않습니다.
#   - 에펨코리아: robots.txt가 `User-agent: *` 에 대해 `Disallow: /` 이며
#     허용 경로는 /$, /best, /best2, /humor 뿐입니다. /politics 는 모든 봇에
#     명시적으로 금지되어 있고, 자체 "보안 시스템"이 HTTP 430 으로 차단합니다.
#   - 다모앙: robots.txt 는 허용하지만 Cloudflare Turnstile 챌린지가 걸려 있고,
#     공식 RSS(/rss)에는 공감게시판(/empathy) 글이 포함되지 않습니다.
#   - 잇싸: 데이터센터 IP 를 HTTP 403 으로 차단합니다. 함수 리전을 서울(icn1)로
#     옮겨도 동일해(해외 IP 가 아니라 클라우드 IP 자체를 차단) 배포 환경에서는
#     수집이 불가능했습니다.
COMMUNITIES = {
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

# Claude API 자격 증명은 anthropic SDK 가 환경(ANTHROPIC_API_KEY 등)에서 직접 읽는다.
