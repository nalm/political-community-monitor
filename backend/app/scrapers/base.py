import abc
import asyncio
import random
import re
from typing import Any, Dict, Iterable, List

import httpx
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
]

# 목록에서 제외해야 하는 행(row)의 CSS class 토큰.
# 실제 각 사이트 HTML을 확인해 수집한 값이다:
#   notice / notice_expand / nofn  → 더쿠·딴지 등 XE 계열 공지 행
#   lnu (lnu--hidden 포함)         → 잇싸(Rhymix) 상단 공지 행
#   best                           → 보배드림 상단 고정 '베스트' 행 (최신글이 아님)
#   bbn                            → 딴지 상단 배너/타이틀 영역
NOTICE_CLASS_TOKENS = frozenset({
    "notice", "notice_expand", "nofn", "nofnhide",
    "lnu",
    "best",
    "bbn",
    "pinned", "sticky",
})


#  일시적인 응답으로 보고 재시도할 상태 코드
_RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


class ScrapeError(Exception):
    """페이지를 끝내 가져오지 못했을 때."""


class BaseScraper(abc.ABC):
    def __init__(self, community_id: str):
        self.community_id = community_id

    async def fetch_soup(self, client: httpx.AsyncClient, url: str,
                         attempts: int = 3) -> BeautifulSoup:
        """목록 페이지를 받아 파싱한다. 일시적 실패는 짧은 백오프로 재시도한다.

        커뮤니티 서버는 연속 요청에 간헐적으로 429/503 을 돌려준다. 한 번의 실패로
        커뮤니티 전체를 버리지 않도록 여기서 흡수한다.
        """
        last_reason = "unknown"
        for i in range(attempts):
            try:
                r = await client.get(url, headers=self.get_headers())
                if r.status_code == 200:
                    return BeautifulSoup(r.text, "html.parser")
                last_reason = f"HTTP {r.status_code}"
                if r.status_code not in _RETRYABLE_STATUS:
                    break  # 404·403 등은 재시도해도 달라지지 않는다
            except (httpx.TimeoutException, httpx.TransportError) as e:
                last_reason = type(e).__name__

            if i < attempts - 1:
                await asyncio.sleep(0.5 * (i + 1))

        raise ScrapeError(f"{url} 요청 실패 ({last_reason})")

    def get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Upgrade-Insecure-Requests": "1"
        }

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

    def is_notice_row(self, tr, extra_tokens: Iterable[str] = ()) -> bool:
        """공지·고정글 행인지 class 토큰으로 판정한다.

        제목 키워드("공지" 등)로 거르면 정상 게시물까지 버려지므로 쓰지 않는다.
        `lnu--hidden` 같은 BEM 변형은 `--` 앞부분으로도 대조한다.
        """
        tokens = set()
        for cls in (tr.get("class") or []):
            tokens.add(cls)
            tokens.add(cls.split("--")[0])
        return bool(tokens & (NOTICE_CLASS_TOKENS | set(extra_tokens)))

    def first_int(self, node, default: int = 0) -> int:
        """노드 텍스트에서 첫 번째 정수를 뽑는다. 없으면 default.

        더쿠 조회수처럼 "30,005" 로 천단위 구분자가 붙는 경우가 있어 콤마를 먼저 제거한다.
        (제거하지 않으면 30 으로 잘못 읽힌다.)
        """
        if node is None:
            return default
        nums = re.findall(r'\d+', node.get_text().replace(",", ""))
        return int(nums[0]) if nums else default

    def finalize(self, posts: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """url 기준 중복 제거 후 게시물 번호 내림차순(=최신순)으로 상위 limit개를 반환."""
        seen = set()
        unique = []
        for p in posts:
            if p["url"] in seen:
                continue
            seen.add(p["url"])
            unique.append(p)

        def sort_key(p: Dict[str, Any]) -> int:
            oid = str(p.get("original_id", ""))
            return int(oid) if oid.isdigit() else -1

        unique.sort(key=sort_key, reverse=True)
        return unique[:limit]

    @abc.abstractmethod
    async def fetch_hot_posts(self, limit: int = 30) -> List[Dict[str, Any]]:
        """지정된 인기 게시판에서 공지를 제외한 최신 게시물을 limit개 수집."""
        pass
