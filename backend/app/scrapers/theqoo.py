import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseScraper


class TheqooScraper(BaseScraper):
    def __init__(self):
        super().__init__("theqoo")
        self.base_url = "https://theqoo.net"
        self.list_url = "https://theqoo.net/square/category/3836759081?filter_mode=hot"

    async def fetch_hot_posts(self, limit: int = 30) -> List[Dict[str, Any]]:
        posts: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            page = 1
            while len(posts) < limit and page <= 4:
                url = f"{self.list_url}&page={page}" if page > 1 else self.list_url
                r = await client.get(url, headers=self.get_headers())
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")

                # 공지 행은 class="notice nofn". 페이지당 13개가량이라 실제 글은 20개 안팎이다.
                for tr in soup.select("table tbody tr, .show_normal tbody tr"):
                    if self.is_notice_row(tr):
                        continue

                    a = tr.select_one("td.title a")
                    if not a:
                        continue
                    href = a.get("href", "")
                    if not href or "#" in href:
                        continue

                    cid = href.split("?")[0].split("/")[-1]
                    if not cid.isdigit():
                        continue

                    title = self.clean_text(a.get_text())
                    if len(title) < 2:
                        continue

                    # 목록 컬럼: no / cate / title / time / m_no(조회수)
                    posts.append({
                        "community_id": self.community_id,
                        "original_id": cid,
                        "title": title,
                        "url": href if href.startswith("http") else self.base_url + href,
                        "author": "무명의 더쿠",
                        "view_count": self.first_int(tr.select_one("td.m_no")),
                        "vote_count": self.first_int(tr.select_one("td.voteNum")),
                        "comment_count": self.first_int(tr.select_one("td.title .replyNum, td.title .comment_count")),
                    })
                page += 1

        return self.finalize(posts, limit)
